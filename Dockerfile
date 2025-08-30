# Sử dụng base image Python 3.13 slim
FROM python:3.13-slim

# Kiểm tra phiên bản Python
RUN python --version > /app/python_version.txt
RUN echo "Python version: $(python --version)"

# Cài đặt phụ thuộc cho Chrome và biên dịch aiohttp
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    libffi-dev \
    libc-dev \
    wget \
    unzip \
    curl \
    libglib2.0-0 \
    libnss3 \
    libgconf-2-4 \
    libfontconfig1 \
    libx11-6 \
    libx11-xcb1 \
    libxi6 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    libxtst6 \
    libxss1 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libgbm1 \
    libu2f-udev \
    && rm -rf /var/lib/apt/lists/*

# Cài đặt Google Chrome
RUN wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN dpkg -i google-chrome-stable_current_amd64.deb || apt-get -f install -y
RUN rm google-chrome-stable_current_amd64.deb

# Kiểm tra Chrome binary
RUN google-chrome --version || { echo "Chrome installation failed"; exit 1; }
RUN which google-chrome || { echo "Chrome binary not found at /usr/bin/google-chrome"; exit 1; }
RUN echo "Chrome binary found at: $(which google-chrome)"
RUN google-chrome --version > /app/chrome_version.txt

# Cài đặt Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy mã nguồn
COPY . .

# Chạy bot
CMD ["python", "Main.py"]
