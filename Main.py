import discord
from discord.ext import commands
import json
from datetime import datetime
import os  # Đã có, dùng để đọc env var

# Đọc BOT_TOKEN từ environment variable (an toàn hơn hardcode)
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    print("❌ Lỗi: Không tìm thấy BOT_TOKEN trong environment variables!")
    print("Hướng dẫn set: export BOT_TOKEN='your_token_here' (Linux/Mac) hoặc set BOT_TOKEN=your_token_here (Windows)")
    exit(1)  # Exit nếu thiếu token

# ID kênh nhận webhook (có thể cũng làm env var nếu muốn, ví dụ: WEBHOOK_CHANNEL_ID = int(os.getenv('WEBHOOK_CHANNEL_ID', '0')))
WEBHOOK_CHANNEL_ID = 1405080664390500402  # Thay bằng ID kênh log của bạn

# Setup bot (giữ nguyên)
intents = discord.Intents.default()
intents.message_content = True
intents.components = True  # Để handle button
bot = commands.Bot(command_prefix='!', intents=intents)

# ... (Phần còn lại của code giữ nguyên: on_ready, on_message, on_interaction, track command, bot.run(BOT_TOKEN))

# Global dict lưu data real-time (key: username Roblox)
user_data = {}

@bot.event
async def on_ready():
    print(f'{bot.user} (AppleHubTracker) đã online! Sẵn sàng track logs từ Roblox.')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} slash commands.')
    except Exception as e:
        print(f'Lỗi sync commands: {e}')

@bot.event
async def on_message(message):
    # Parse embed từ webhook Apple Hub (chỉ trong kênh cụ thể)
    if message.channel.id == WEBHOOK_CHANNEL_ID and message.embeds:
        embed = message.embeds[0]
        if "Apple Hub" in embed.title:  # Xác nhận từ script Roblox
            # Extract username từ description
            desc = embed.description
            username = "Unknown"
            if "username" in desc:
                start_idx = desc.find("**username**: `") + len("**username**: `")
                end_idx = desc.find("`", start_idx)
                if start_idx > 0 and end_idx > start_idx:
                    username = desc[start_idx:end_idx]
            
            # Parse fields real-time
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
                # Tùy chọn: Gửi confirm message vào kênh (hoặc không, để im lặng)
                # await message.channel.send(f"✅ Updated data for {username}")
    
    await bot.process_commands(message)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get('custom_id', '')
        if custom_id.startswith('view_script_details_'):
            if not user_data:
                await interaction.response.send_message("❌ Chưa có data real-time từ Apple Hub!", ephemeral=True)
                return
            
            # Nếu multi-user, list options; nếu single, lấy đầu tiên
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
    
    # Xử lý slash commands (nếu có)
    if interaction.type == discord.InteractionType.application_command:
        # Bot sẽ tự handle qua tree
        pass

# Slash command để xem track thủ công
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

# Chạy bot
if __name__ == "__main__":
    bot.run(BOT_TOKEN)
