# Sử dụng base image Python 3.11 slim
FROM python:3.11-slim

# Cài đặt các phụ thuộc cần thiết cho Chrome
RUN apt-get update && apt-get install -y \
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
RUN which google-chrome || { echo "Chrome binary not found"; exit 1; }

# Cài đặt Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy mã nguồn
COPY . .

# Chạy bot
CMD ["python", "Main.py"]
