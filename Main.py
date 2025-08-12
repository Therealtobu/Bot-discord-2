# bot.py
import discord
from discord.ext import commands
from discord.ui import View, Button
import asyncio
import json
import os
import random
from pathlib import Path
from io import BytesIO
from datetime import datetime

# -------------------------
# Cấu hình
# -------------------------
# token: thay trực tiếp hoặc set env DISCORD_TOKEN
TOKEN = os.getenv("DISCORD_TOKEN") or "YOUR_TOKEN_HERE"

# Role ID: role nào có quyền set/add coin cho toàn bộ thành viên role
ROLE_COIN_ID = 1404851048052559872

# Tên đồng tiền
COIN_NAME = "Loli Coin"
COIN_ICON_URL = "https://discord.com/channels/919822394359701514/1397982660218847382/1404848078707753074"  # thay bằng URL icon của bạn nếu muốn

# File lưu dữ liệu
DATA_FILE = Path("data.json")

# Lần đầu tặng
DEFAULT_START = 10000

# range reward khi spin
SPIN_MIN = 10
SPIN_MAX = 200

# Spin animation settings (simple: edit message N lần)
SPIN_ITER = 10
SPIN_SLEEP = 0.12

# -------------------------
# Helpers: load/save data
# -------------------------
def ensure_datafile():
    if not DATA_FILE.exists():
        DATA_FILE.write_text(json.dumps({"users": {}}, ensure_ascii=False, indent=2), encoding="utf-8")

def load_data():
    ensure_datafile()
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_balance_dict():
    data = load_data()
    return data.setdefault("users", {})

def ensure_user_record(user_id: int):
    users = get_balance_dict()
    uid = str(user_id)
    if uid not in users:
        users[uid] = {"balance": DEFAULT_START, "first_claimed": True}
        save_data({"users": users})
        return users[uid], True
    return users[uid], False

# -------------------------
# Bot setup
# -------------------------
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -------------------------
# Spin View (button)
# -------------------------
class SpinView(View):
    def __init__(self, author_id: int, bet: int):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.bet = bet

    @discord.ui.button(label="🎰 Kéo cần", style=discord.ButtonStyle.green, custom_id="spin_button")
    async def spin_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # only allow the user who requested to press
        if interaction.user.id != self.author_id:
            return await interaction.response.send_message("❌ Không phải lượt của bạn.", ephemeral=True)

        # disable to avoid double click
        for child in self.children:
            child.disabled = True
        try:
            await interaction.message.edit(view=self)
        except:
            pass

        # ensure user record
        user_obj, is_new = ensure_user_record(interaction.user.id)
        # if new user: initial balance already given in ensure_user_record

        # check balance unless user is in role with unlimited? (we're not giving unlimited here)
        uid = str(interaction.user.id)
        users = get_balance_dict()
        bal = users.get(uid, {}).get("balance", 0)

        if bal < self.bet:
            return await interaction.response.send_message(f"❌ Bạn không đủ {COIN_NAME}. Số dư: `{bal}`", ephemeral=True)

        # deduct bet
        users[uid]["balance"] = bal - self.bet
        save_data({"users": users})

        # animation by editing message (simple emoji "wheel")
        wheel_emojis = ["🍒","🍋","🍇","🍌","💎","⭐"]
        msg = interaction.message
        await interaction.response.defer()  # defer so we can followup edits

        final_reward = 0
        final_symbols = None

        for i in range(SPIN_ITER):
            # temporary symbols
            temp = [random.choice(wheel_emojis) for _ in range(3)]
            try:
                await msg.edit(content=f"🎰 Đang quay... {' | '.join(temp)}\n(Bet `{self.bet}` {COIN_NAME})", view=self)
            except:
                pass
            await asyncio.sleep(SPIN_SLEEP)

        # determine final symbols and reward based on matches
        final_symbols = tuple(random.choice(wheel_emojis) for _ in range(3))
        # simple paytable: triple -> x10, pair -> x2, else -> 0
        if final_symbols[0] == final_symbols[1] == final_symbols[2]:
            multiplier = 10
            final_reward = self.bet * multiplier
            note = f"Triple {final_symbols[0]} ×{multiplier}"
        elif final_symbols[0] == final_symbols[1] or final_symbols[0] == final_symbols[2] or final_symbols[1] == final_symbols[2]:
            # find which symbol forms the pair
            pair_sym = None
            for s in set(final_symbols):
                if final_symbols.count(s) == 2:
                    pair_sym = s
                    break
            multiplier = 2
            final_reward = self.bet * multiplier
            note = f"Pair {pair_sym} ×{multiplier}"
        else:
            final_reward = 0
            note = "No match"

        # add reward
        users = get_balance_dict()
        users[uid]["balance"] = users.get(uid, {}).get("balance", 0) + final_reward
        save_data({"users": users})

        # send final result (edit)
        result_text = (
            f"**{interaction.user.display_name}** kết quả: `{final_symbols[0]}` | `{final_symbols[1]}` | `{final_symbols[2]}`\n"
            f"{'🎉 Bạn thắng' if final_reward>0 else '😢 Bạn thua'} **{final_reward} {COIN_NAME}**. ({note})\n"
            f"Số dư hiện tại: `{users[uid]['balance']}` {COIN_NAME}"
        )
        try:
            await msg.edit(content=result_text, view=self)
        except:
            await interaction.followup.send(result_text)

        self.stop()

# -------------------------
# Commands
# -------------------------
@bot.event
async def on_ready():
    print(f"Bot ready: {bot.user} — {datetime.utcnow().isoformat()}")

@bot.command(name="spin")
async def cmd_spin(ctx, bet: int = 100):
    # Ensure user record (gives default START if first time)
    user, was_new = ensure_user_record(ctx.author.id)
    if was_new:
        await ctx.reply(f"🎁 Lần đầu chơi — bạn được tặng `{DEFAULT_START}` {COIN_NAME}!")

    # Build initial message with button
    msg = await ctx.send(
        f"**{ctx.author.display_name}** chuẩn bị quay (bet `{bet}` {COIN_NAME})\n🔲 • • • • • • • •",
        view=SpinView(ctx.author.id, bet)
    )

@bot.command(name="mycoin")
async def cmd_mycoin(ctx):
    users = get_balance_dict()
    uid = str(ctx.author.id)
    bal = users.get(uid, {}).get("balance", 0)
    embed = discord.Embed(title=f"💎 {ctx.author.display_name} - {COIN_NAME}", description=f"Số dư: **{bal}** {COIN_NAME}", color=discord.Color.blue())
    embed.set_thumbnail(url=COIN_ICON_URL)
    await ctx.send(embed=embed)

@bot.command(name="setcoin")
async def cmd_setcoin(ctx, amount: int):
    # check author has role ROLE_COIN_ID
    role = discord.utils.get(ctx.guild.roles, id=ROLE_COIN_ID)
    if role is None:
        return await ctx.send("❌ Role cấu hình không tồn tại trong server này.")
    if role not in ctx.author.roles:
        return await ctx.send("⛔ Bạn không có quyền dùng lệnh này (cần role).")

    users = get_balance_dict()
    # set amount for all members in role
    for member in role.members:
        users[str(member.id)] = users.get(str(member.id), {"balance": DEFAULT_START})
        users[str(member.id)]["balance"] = amount
    save_data({"users": users})
    await ctx.send(f"✅ Đã đặt **{amount} {COIN_NAME}** cho tất cả thành viên role **{role.name}**.")

@bot.command(name="addcoin")
async def cmd_addcoin(ctx, amount: int):
    role = discord.utils.get(ctx.guild.roles, id=ROLE_COIN_ID)
    if role is None:
        return await ctx.send("❌ Role cấu hình không tồn tại trong server này.")
    if role not in ctx.author.roles:
        return await ctx.send("⛔ Bạn không có quyền dùng lệnh này (cần role).")

    users = get_balance_dict()
    for member in role.members:
        uid = str(member.id)
        users[uid] = users.get(uid, {"balance": DEFAULT_START})
        users[uid]["balance"] = users[uid].get("balance", 0) + amount
    save_data({"users": users})
    await ctx.send(f"✅ Đã cộng **{amount} {COIN_NAME}** cho tất cả thành viên role **{role.name}**.")

@bot.command(name="leaderboard")
async def cmd_leaderboard(ctx):
    users = get_balance_dict()
    # convert to list and sort desc by balance
    items = [(uid, info.get("balance", 0)) for uid, info in users.items()]
    items.sort(key=lambda x: x[1], reverse=True)
    top = items[:10]
    if not top:
        return await ctx.send("Chưa có dữ liệu Loli Coin.")
    lines = []
    for uid, bal in top:
        try:
            member = await bot.fetch_user(int(uid))
            name = member.name
        except:
            name = f"<@{uid}>"
        lines.append(f"**{name}** — `{bal}` {COIN_NAME}")
    embed = discord.Embed(title="🏆 Top Loli Coin", description="\n".join(lines), color=discord.Color.gold())
    await ctx.send(embed=embed)

# -------------------------
# Ensure data file exists at start
# -------------------------
ensure_datafile()

# -------------------------
# Run bot
# -------------------------
if __name__ == "__main__":
    if not TOKEN or TOKEN == "YOUR_TOKEN_HERE":
        print("❌ Chưa cấu hình token. Đặt biến môi trường DISCORD_TOKEN hoặc chỉnh trực tiếp biến TOKEN trong file.")
    else:
        bot.run(TOKEN)
