#!/bin/sh

# Docker容器启动脚本 - 处理权限问题

echo "🚀 GitHub Manager 容器启动..."

# 显示环境信息
echo "📋 环境信息:"
echo "- NODE_ENV: $NODE_ENV"
echo "- DATABASE_DIR: $DATABASE_DIR"
echo "- 当前用户: $(id)"
echo "- 工作目录: $(pwd)"

# 检查数据目录
DATA_DIR="${DATABASE_DIR:-/app/data}"
echo "📁 检查数据目录: $DATA_DIR"

# 如果数据目录不存在，创建它
if [ ! -d "$DATA_DIR" ]; then
    echo "创建数据目录..."
    mkdir -p "$DATA_DIR" || echo "⚠️  无法创建数据目录，将使用临时目录"
fi

# 检查权限并尝试修复
if [ -d "$DATA_DIR" ]; then
    echo "检查数据目录权限..."
    if [ ! -w "$DATA_DIR" ]; then
        echo "⚠️  数据目录权限不足，尝试修复..."
        chmod 777 "$DATA_DIR" 2>/dev/null || echo "无法修改权限，应用将尝试使用临时目录"
    fi
    
    # 测试写权限
    TEST_FILE="$DATA_DIR/.write-test"
    if echo "test" > "$TEST_FILE" 2>/dev/null; then
        rm -f "$TEST_FILE"
        echo "✅ 数据目录权限正常"
    else
        echo "⚠️  数据目录仍无写权限，应用将使用临时目录"
    fi
    
    echo "📊 数据目录状态: $(ls -ld $DATA_DIR)"
fi

# 检查是否以root用户运行
if [ "$(id -u)" = "0" ]; then
    echo "🔒 以root用户运行，无权限问题"
else
    echo "👤 以非root用户运行 ($(id -u):$(id -g))"
fi

echo "🌟 启动应用..."
exec "$@"