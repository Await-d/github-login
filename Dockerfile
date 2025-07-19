# 多阶段构建：先构建前端，再构建后端
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Python后端镜像
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制后端代码
COPY backend/ ./backend/

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/build ./frontend/build

# 创建数据目录
RUN mkdir -p /app/data && chmod 755 /app/data

# 设置环境变量
ENV PYTHONPATH=/app/backend
ENV PORT=8000

# 暴露端口
EXPOSE 8000

# 切换到后端目录并启动应用
WORKDIR /app/backend
CMD ["python", "app/main.py"]