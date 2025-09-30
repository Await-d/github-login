# 多阶段构建：第一阶段 - 构建前端
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend

# 复制前端依赖文件
COPY frontend/package*.json ./

# 安装前端依赖
RUN npm install

# 复制前端源代码
COPY frontend/ ./

# 构建前端
RUN npm run build

# 第二阶段 - 构建后端
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libwayland-client0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# 安装 Google Chrome（使用新的 GPG 密钥方法）
RUN wget -q -O /tmp/google-chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
    && apt-get update \
    && apt-get install -y /tmp/google-chrome.deb \
    && rm /tmp/google-chrome.deb \
    && rm -rf /var/lib/apt/lists/*

# 设置 Chrome 环境变量
ENV CHROME_BIN=/usr/bin/google-chrome
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 复制requirements.txt
COPY backend/requirements.txt /app/backend/requirements.txt

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# 复制后端项目文件
COPY backend/ /app/backend/

# 从前端构建阶段复制构建好的文件
COPY --from=frontend-builder /app/frontend/build /app/frontend/build

# 设置环境变量
ENV PYTHONPATH=/app/backend
ENV PORT=8000

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "/app/backend/app/main.py"]