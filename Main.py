import os
import discord
from discord.ext import commands, tasks
import asyncio
from datetime import datetime, timedelta, timezone
from keep_alive import keep_alive
import random
import json
import re

# -------------------------
# Cấu hình bot
# -------------------------
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
FILE_PATH = "data.json"

# Mute & Filter Config
SPAM_LIMIT = 10
TIME_WINDOW = 30  # giây
MUTE_TIME = 900  # 15 phút
MUTE_ROLE_ID = 1409154399259066388
LOG_CHANNEL_ID = 1409154239791370240

# Từ cấm
BAD_WORDS = ["Parky", "namki", "namky", "backy", "backi", "trungkiki"]

# Khởi tạo dữ liệu từ file cục bộ
data = {}
try:
    with open(FILE_PATH, 'r') as f:
        loaded = json.load(f)
        data = {
            k: {
                'last_daily': datetime.fromisoformat(v['last_daily']) if v['last_daily'] else None,
            } for k, v in loaded.items()
        }
except FileNotFoundError:
    print(f"❌ Không tìm thấy {FILE_PATH}, tạo file mới")
    with open(FILE_PATH, 'w') as f:
        json.dump(data, f, indent=2)
except Exception as e:
    print(f"❌ Lỗi khi đọc {FILE_PATH}: {e}")

def save_data():
    try:
        with open(FILE_PATH, 'w') as f:
            content = {
                k: {
                    'last_daily': v['last_daily'].isoformat() if v['last_daily'] else None,
                } for k, v in data.items()
            }
        json.dump(content, f, indent=2)
        print(f"✅ Đã lưu dữ liệu vào {FILE_PATH}")
    except Exception as e:
        print(f"❌ Lỗi khi lưu {FILE_PATH}: {e}")

# Intents
intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True

bot = commands.Bot(command_prefix="/", intents=intents)

# -------------------------
# Mute + Xóa tin nhắn + Log
# -------------------------
async def mute_and_log(message, reason="vi phạm", mute_time=900):
    try:
        mute_role = message.guild.get_role(MUTE_ROLE_ID)
        if not mute_role:
            print("❌ Không tìm thấy role mute!")
            return

        # Xóa tin nhắn vi phạm
        async for msg in message.channel.history(limit=50):
            if msg.author == message.author and (datetime.now(timezone.utc) - msg.created_at).seconds <= TIME_WINDOW:
                try:
                    await msg.delete()
                    print(f"✅ Đã xóa tin nhắn của {message.author.name}")
                except Exception as e:
                    print(f"❌ Lỗi khi xóa tin nhắn: {e}")

        # Mute thành viên
        await message.author.add_roles(mute_role)
        print(f"✅ Đã mute {message.author.name} trong {mute_time // 60} phút")

        # Gửi log
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                title="🚨 Phát hiện vi phạm",
                description=f"**Người vi phạm:** {message.author.mention}\n**Lý do:** {reason}\n**Thời gian mute:** {mute_time // 60} phút",
                color=discord.Color.red()
            )
            embed.add_field(name="Nội dung", value=f"||{message.content or '*Không có nội dung*'}||", inline=False)
            embed.add_field(name="Kênh", value=message.channel.mention, inline=True)
            embed.add_field(name="Lưu ý", value="Cân nhắc khi xem", inline=False)
            embed.timestamp = datetime.now(timezone.utc)
            await log_channel.send(embed=embed)
            print(f"✅ Đã gửi log vi phạm cho {message.author.name}")

        # Bỏ mute sau thời gian quy định
        await asyncio.sleep(mute_time)
        await message.author.remove_roles(mute_role)
        print(f"✅ Đã bỏ mute {message.author.name}")

    except Exception as e:
        print(f"❌ Lỗi mute_and_log: {e}")

# -------------------------
# On Message (Filter + Anti-Spam)
# -------------------------
user_messages = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    content_lower = message.content.lower()

    # Kiểm tra từ cấm
    has_bad_word = any(word.lower() in content_lower for word in BAD_WORDS)
    if has_bad_word:
        await mute_and_log(message, "sử dụng từ ngữ cấm", MUTE_TIME)
        return

    # Kiểm tra spam
    now = datetime.now(timezone.utc)
    uid = message.author.id
    if uid not in user_messages:
        user_messages[uid] = []
    user_messages[uid].append(now)
    user_messages[uid] = [t for t in user_messages[uid] if now - t < timedelta(seconds=TIME_WINDOW)]

    if len(user_messages[uid]) > SPAM_LIMIT:
        await mute_and_log(message, "spam tin nhắn", MUTE_TIME)
        user_messages[uid] = []
        return

    await bot.process_commands(message)

# -------------------------
# On Ready
# -------------------------
@bot.event
async def on_ready():
    print(f"✅ Bot đã đăng nhập: {bot.user}")

# -------------------------
# Run Bot
# -------------------------
keep_alive()

if not DISCORD_TOKEN:
    print("❌ Chưa đặt DISCORD_TOKEN")
else:
    bot.run(DISCORD_TOKEN)