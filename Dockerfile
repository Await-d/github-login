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
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# 设置 Chrome 环境变量
ENV CHROME_BIN=/usr/bin/chromium
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