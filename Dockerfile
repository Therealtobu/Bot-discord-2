# Base image: Python 3.12 slim (ổn định, còn audioop)
FROM python:3.12-slim

# Cài dependency cho Chrome
RUN apt-get update && apt-get install -y \
    wget unzip curl gnupg \
    libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1 \
    libx11-6 libx11-xcb1 libxi6 libxcomposite1 libxdamage1 \
    libxrandr2 libxtst6 libxss1 libatk1.0-0 libatk-bridge2.0-0 \
    libpango-1.0-0 libcairo2 libasound2 libgbm1 libu2f-udev \
    fonts-liberation xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt Google Chrome
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get install -y ./google-chrome-stable_current_amd64.deb \
    && rm google-chrome-stable_current_amd64.deb

# Thư mục làm việc
WORKDIR /app

# Cài dependencies Python (bỏ voice)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && pip uninstall -y discord.py[voice] || true \
    && pip install --no-cache-dir "discord.py==2.3.2"

# Copy code vào container
COPY . .

# Chạy bot
CMD ["python", "Main.py"]
