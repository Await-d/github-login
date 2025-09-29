# 使用官方Python基础镜像
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
    && rm -rf /var/lib/apt/lists/*

# 复制requirements.txt
COPY backend/requirements.txt /app/backend/requirements.txt

# 安装Python依赖
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /app/backend/requirements.txt

# 复制项目文件
COPY backend/ /app/backend/
COPY frontend/build/ /app/frontend/build/

# 设置环境变量
ENV PYTHONPATH=/app/backend
ENV PORT=8000

# 暴露端口
EXPOSE 8000

# 运行依赖检查
RUN cd /app/backend && python check_dependencies.py

# 启动命令
CMD ["python", "/app/backend/app/main.py"]