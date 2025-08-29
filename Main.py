import discord
from discord.ext import commands
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from datetime import datetime
import time
import random
import os

# Cấu hình bot Discord
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# Lấy biến môi trường
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
DISCORD_CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID'))

# Cấu hình Chrome với stealth
def setup_driver():
    for attempt in range(3):  # Thử 3 lần
        try:
            options = Options()  # Tạo mới options mỗi lần thử
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument(f"--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(120, 130)}.0.0.0 Safari/537.36")
            options.binary_location = "/usr/bin/google-chrome"
            driver = uc.Chrome(
                options=options,
                browser_executable_path="/usr/bin/google-chrome",
                version_main=random.randint(120, 130)
            )
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            print(f"Driver khởi tạo thành công (thử {attempt + 1})")
            return driver
        except Exception as e:
            print(f"Lỗi khởi tạo driver (thử {attempt + 1}/3): {str(e)}")
            time.sleep(2)
    return None

driver = setup_driver()
if not driver:
    print("Không thể khởi tạo Chrome driver sau 3 lần thử")
    raise Exception("Không thể khởi tạo Chrome driver sau 3 lần thử")

# Hàm tạo progress bar
def create_progress_bar(percentage):
    filled = int(percentage / 10)
    return f"[{'█' * filled}{' ' * (10 - filled)} {percentage}%]"

# Hàm kiểm tra link Krnl
def is_krnl_link(url):
    return "krnl" in url.lower()

# Hàm xử lý Cloudflare
def handle_cloudflare():
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'cf-browser-verification') or contains(text(), 'Checking your browser')]"))
        )
        step_time = datetime.now()
        WebDriverWait(driver, 30).until(
            lambda d: "success" in d.page_source.lower() or 
                      d.execute_script("return document.readyState") == "complete" and 
                      "cf_clearance" in [cookie['name'] for cookie in d.get_cookies()]
        )
        time.sleep(5)
        return True, (datetime.now() - step_time).total_seconds()
    except:
        return False, 0

# Hàm xử lý một Linkvertise
def handle_single_linkvertise(linkvertise_count):
    try:
        # Bước 1: Bấm "Agree" nếu có
        try:
            agree_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Agree') or contains(text(), 'Accept')]"))
            )
            agree_button.click()
            time.sleep(2)
        except:
            pass

        # Bước 2: Bấm "Get Link"
        get_link_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Get Link')]"))
        )
        get_link_button.click()
        time.sleep(2)

        # Bước 3: Bấm "I'm Interested"
        interested_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Interested')]"))
        )
        interested_button.click()
        time.sleep(2)

        # Bước 4: Bấm "Click Here" hoặc "Search Now"
        click_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Click Here') or contains(text(), 'Search Now')]"))
        )
        click_button.click()
        time.sleep(2)

        # Bước 5: Đợi 10 giây
        time.sleep(10)

        # Bước 6: Back về Linkvertise
        driver.back()
        time.sleep(2)

        # Bước 7: Bấm "I Have Already Completed This Step"
        completed_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'I Have Already Completed This Step')]"))
        )
        completed_button.click()
        time.sleep(2)

        # Bước 8: Đợi 11 giây
        time.sleep(11)

        # Bước 9: Bấm "Get Link" lần nữa
        get_link_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Get Link')]"))
        )
        get_link_button.click()
        time.sleep(2)

        # Bước 10: Bấm "Open"
        open_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Open')]"))
        )
        open_button.click()
        time.sleep(2)

        return True, None
    except Exception as e:
        return False, f"Lỗi Linkvertise {linkvertise_count}: {str(e)}"

# Hàm xử lý link và lấy key
async def process_link(url, channel):
    if not is_krnl_link(url):
        await channel.send("🚫 Link không phải Krnl, bỏ qua!")
        return

    start_time = datetime.now()
    await channel.send(f"⏳ Bắt đầu xử lý link: {url}\n{create_progress_bar(10)}")

    driver.get(url)
    await channel.send(f"🌐 Đã truy cập link ({(datetime.now() - start_time).total_seconds():.2f}s)\n{create_progress_bar(20)}")

    linkvertise_count = 0
    max_linkvertise = 4
    max_cloudflare_retries = 3

    while linkvertise_count < max_linkvertise:
        try:
            # Xử lý Cloudflare
            step_time = datetime.now()
            cf_retries = 0
            while cf_retries < max_cloudflare_retries:
                cf_success, cf_time = handle_cloudflare()
                if cf_success:
                    await channel.send(f"✅ Cloudflare success ({cf_time:.2f}s)\n{create_progress_bar(30)}")
                    break
                else:
                    cf_retries += 1
                    await channel.send(f"❌ Cloudflare thất bại, retry {cf_retries}/{max_cloudflare_retries}... ({cf_time:.2f}s)\n{create_progress_bar(20)}")
                    driver.refresh()
                    time.sleep(5)
            if cf_retries >= max_cloudflare_retries:
                await channel.send("❌ Cloudflare thất bại sau 3 lần thử. Cần can thiệp thủ công!")
                return

            # Bấm "Next Checkpoint" sau Cloudflare success
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Next Checkpoint')]"))
            )
            next_button.click()
            await channel.send(f"✅ Đã bấm 'Next Checkpoint' ({(datetime.now() - step_time).total_seconds():.2f}s)\n{create_progress_bar(40)}")

            # Kiểm tra lỗi captcha fail
            if "captcha fail" in driver.page_source.lower():
                await channel.send(f"❌ Lỗi: Captcha fail, quay lại... ({(datetime.now() - step_time).total_seconds():.2f}s)\n{create_progress_bar(30)}")
                driver.back()
                time.sleep(2)
                continue

            # Xử lý Linkvertise
            if "linkvertise" in driver.current_url:
                linkvertise_count += 1
                step_time = datetime.now()
                success, error_msg = handle_single_linkvertise(linkvertise_count)
                if success:
                    await channel.send(f"🔗 Hoàn thành Linkvertise {linkvertise_count}/{max_linkvertise} ({(datetime.now() - step_time).total_seconds():.2f}s)\n{create_progress_bar(50 + (linkvertise_count * 10))}")
                else:
                    await channel.send(f"❌ {error_msg}. Thử lại... ({(datetime.now() - step_time).total_seconds():.2f}s)\n{create_progress_bar(40)}")
                    driver.back()
                    time.sleep(2)
                    continue

            # Kiểm tra lỗi "Linkvertise not done"
            if "linkvertise not done" in driver.page_source.lower():
                await channel.send(f"❌ Lỗi: Linkvertise chưa hoàn thành, thử lại... ({(datetime.now() - step_time).total_seconds():.2f}s)\n{create_progress_bar(40)}")
                driver.back()
                time.sleep(2)
                continue

            # Tìm key nếu không còn "Next Checkpoint"
            if not driver.find_elements(By.XPATH, "//button[contains(text(), 'Next Checkpoint')]"):
                step_time = datetime.now()
                try:
                    key_element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Your key is')]"))
                    )
                    key = key_element.text
                    await channel.send(f"🎉 Lấy được key: **{key}** ({(datetime.now() - step_time).total_seconds():.2f}s)\n{create_progress_bar(100)}\nTổng thời gian: {(datetime.now() - start_time).total_seconds():.2f}s (Hoàn thành {linkvertise_count} Linkvertise)")
                    break
                except:
                    await channel.send(f"❌ Không tìm thấy key, thử lại toàn bộ... ({(datetime.now() - step_time).total_seconds():.2f}s)\n{create_progress_bar(50)}")
                    break

        except Exception as e:
            await channel.send(f"❌ Lỗi hệ thống: {str(e)} ({(datetime.now() - step_time).total_seconds():.2f}s)\n{create_progress_bar(30)}")
            driver.back()
            time.sleep(2)

    else:
        await channel.send("❌ Đã thử tối đa 4 Linkvertise nhưng không lấy được key. Cần can thiệp thủ công!")

# Sự kiện Discord: Chờ người dùng gửi link
@bot.event
async def on_message(message):
    if message.channel.id == DISCORD_CHANNEL_ID and message.author != bot.user:
        url = message.content.strip()
        if url.startswith("http"):
            await process_link(url, message.channel)
    await bot.process_commands(message)

# Khởi động bot
bot.run(DISCORD_BOT_TOKEN)
