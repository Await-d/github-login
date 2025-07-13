#!/bin/sh

# Docker容器启动脚本

echo "🚀 启动GitHub账号管理系统..."

# 检查并创建数据目录
DATA_DIR="${DATABASE_DIR:-/app/data}"
echo "📁 数据目录: $DATA_DIR"

if [ ! -d "$DATA_DIR" ]; then
    echo "创建数据目录: $DATA_DIR"
    mkdir -p "$DATA_DIR"
fi

# 检查权限
if [ ! -w "$DATA_DIR" ]; then
    echo "⚠️  数据目录权限不足，尝试修复..."
    chmod 755 "$DATA_DIR" 2>/dev/null || echo "无法修改权限，继续尝试..."
fi

# 显示环境信息
echo "📋 环境信息:"
echo "- NODE_ENV: $NODE_ENV"
echo "- PORT: $PORT"
echo "- DATABASE_DIR: $DATABASE_DIR"
echo "- 当前用户: $(id)"
echo "- 工作目录: $(pwd)"
echo "- 数据目录权限: $(ls -ld $DATA_DIR)"

# 启动应用
echo "🌟 启动Node.js应用..."
exec "$@"