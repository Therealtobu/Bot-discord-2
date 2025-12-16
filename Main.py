import discord
from discord.ext import commands
import json
from datetime import datetime
import os
import threading
from flask import Flask
import time
import requests  # Để post Pastebin

# Đọc BOT_TOKEN từ env
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ Lỗi: Không tìm thấy BOT_TOKEN!")
    exit(1)

# ID kênh webhook
WEBHOOK_CHANNEL_ID = 1405080664390500402  # Thay ID kênh log

# Setup bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Dict lưu data user
user_data = {}

# Keep-alive Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "AppleHubTracker Bot is Alive! 🚀"

@app.route('/ping')
def ping():
    return {"status": "alive", "timestamp": time.time()}, 200

def run_flask():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)

flask_thread = threading.Thread(target=run_flask, daemon=True)
flask_thread.start()

@bot.event
async def on_ready():
    print(f'{bot.user} (AppleHubTracker) đã online!')
    print(f'Keep-Alive server running on port {os.environ.get("PORT", 8080)}')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash commands.')
    except Exception as e:
        print(f'Lỗi sync commands: {e}')

@bot.event
async def on_message(message):
    if message.channel.id == WEBHOOK_CHANNEL_ID and message.embeds:
        embed = message.embeds[0]
        if "Apple Hub" in embed.title:
            desc = embed.description
            username = "Unknown"
            if "username" in desc:
                start_idx = desc.find("**username**: `") + len("**username**: `")
                end_idx = desc.find("`", start_idx)
                if start_idx > 0 and end_idx > start_idx:
                    username = desc[start_idx:end_idx]
            
            total_time = "00:00:00"
            wins = 0
            hops = 0
            fps = 0
            for field in embed.fields:
                if "Thời gian chạy tổng" in field.name:
                    total_time = field.value.strip("**")
                elif "Tổng wins" in field.name:
                    wins = int(field.value) if field.value.isdigit() else 0
                elif "Số server đã hop" in field.name:
                    hops = int(field.value) if field.value.isdigit() else 0
                elif "FPS hiện tại" in field.name:
                    fps = int(field.value) if field.value.isdigit() else 0
            
            if username != "Unknown":
                user_data[username] = {
                    'time': total_time,
                    'wins': wins,
                    'hops': hops,
                    'fps': fps,
                    'last_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                print(f"[TRACK] Updated {username}: Time={total_time}, Wins={wins}, Hops={hops}, FPS={fps}")
    
    await bot.process_commands(message)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get('custom_id', '')
        if custom_id.startswith('view_script_details_'):
            if not user_data:
                await interaction.response.send_message("❌ Chưa có data real-time từ Apple Hub!", ephemeral=True)
                return
            
            if len(user_data) == 1:
                username = list(user_data.keys())[0]
            else:
                usernames_list = "\n".join([f"• `{u}`" for u in user_data.keys()])
                await interaction.response.send_message(f"📋 Users đang track:\n{usernames_list}\n\nDùng `/track <username>` để xem chi tiết!", ephemeral=True)
                return
            
            data = user_data.get(username)
            if data:
                embed = discord.Embed(
                    title="📈 Chi Tiết Real-time Apple Hub",
                    description=f"**Username Roblox:** `{username}`\n**⏱️ Thời gian chạy:** {data['time']}\n**🎮 Tổng wins:** {data['wins']}\n**🌐 Số server hop:** {data['hops']}\n**🎯 FPS hiện tại:** {data['fps']}\n**🕒 Cập nhật lúc:** {data['last_update']}",
                    color=0x00ff00
                )
                embed.add_field(name="Ghi chú", value="Data sync tự động mỗi phút từ script Roblox!", inline=False)
                await interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                await interaction.response.send_message("❌ Không tìm thấy data!", ephemeral=True)
            return

@bot.tree.command(name="track", description="Xem chi tiết real-time của user Apple Hub")
async def track(interaction: discord.Interaction, username: str = None):
    if not user_data:
        await interaction.response.send_message("❌ Chưa có data real-time từ Apple Hub!", ephemeral=True)
        return
    
    if username is None:
        usernames_list = "\n".join([f"• `{u}`" for u in user_data.keys()])
        await interaction.response.send_message(f"📋 Users đang track:\n{usernames_list}\n\nDùng `/track <username>` để xem cụ thể!", ephemeral=True)
        return
    
    data = user_data.get(username)
    if data:
        embed = discord.Embed(
            title="📈 Chi Tiết Real-time Apple Hub",
            description=f"**Username Roblox:** `{username}`\n**⏱️ Thời gian chạy:** {data['time']}\n**🎮 Tổng wins:** {data['wins']}\n**🌐 Số server hop:** {data['hops']}\n**🎯 FPS hiện tại:** {data['fps']}\n**🕒 Cập nhật lúc:** {data['last_update']}",
            color=0x00ff00
        )
        embed.add_field(name="Ghi chú", value="Data sync tự động từ webhook Roblox!", inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True)
    else:
        await interaction.response.send_message(f"❌ Không tìm thấy data cho `{username}`!", ephemeral=True)

# NEW: Command broadcast thông báo đến all hoặc specific user (post lên Pastebin)
PASTEBIN_API_KEY = 'eh9H6JqSr16XPV101t2PV4otRasHLLO3'  # Thay API key Pastebin (đăng ký tại pastebin.com/api)

@bot.tree.command(name="broadcast", description="Gửi thông báo cho user script trên Discord")
async def broadcast(interaction: discord.Interaction, message: str, username: str = "all"):
    await interaction.response.defer(ephemeral=True)
    
    paste_title = f"AppleHub_Notification_{username}"
    paste_content = f'{{ "message": "{message}", "target": "{username}" }}'
    
    response = requests.post("https://pastebin.com/api/api_post.php", data={
        'api_dev_key': PASTEBIN_API_KEY,
        'api_option': 'paste',
        'api_paste_code': paste_content,
        'api_paste_name': paste_title,
        'api_paste_expire_date': '1D'  # Expire 1 ngày
    })
    
    if "pastebin.com" in response.text:
        paste_url = response.text
        await interaction.followup.send(f"✅ Thông báo gửi thành công đến {username}! Paste URL: {paste_url}", ephemeral=True)
    else:
        await interaction.followup.send("❌ Lỗi gửi thông báo! (Check API key)", ephemeral=True)

if __name__ == "__main__":
    bot.run(BOT_TOKEN)
