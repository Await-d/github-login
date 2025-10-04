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

# 安装系统依赖和 Chromium（支持多架构）
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    wget \
    chromium \
    chromium-driver \
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

# 创建 google-chrome 符号链接，让 Selenium 可以找到浏览器
RUN ln -s /usr/bin/chromium /usr/bin/google-chrome

# 设置 Chrome 环境变量
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# 复制requirements.txt
COPY backend/requirements.txt /app/backend/requirements.txt

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# 安装Playwright浏览器（跳过系统依赖安装，因为已经手动安装）
RUN playwright install chromium

# 复制后端项目文件
COPY backend/ /app/backend/

# 从前端构建阶段复制构建好的文件
COPY --from=frontend-builder /app/frontend/build /app/frontend/build

# 设置环境变量
ENV PYTHONPATH=/app/backend
ENV PORT=3000
ENV TZ=Asia/Shanghai

# 暴露端口
EXPOSE 3000

# 启动命令
CMD ["python", "/app/backend/app/main.py"]