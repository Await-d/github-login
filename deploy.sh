#!/bin/bash
# GitHub账号管理系统 - 快速部署脚本

set -e  # 遇到错误时退出

echo "🚀 开始部署GitHub账号管理系统..."

# 检查Python版本
echo "📋 检查Python环境..."
python3 --version || {
    echo "❌ Python3未安装，请先安装Python3"
    exit 1
}

# 进入backend目录
cd backend

# 创建虚拟环境
echo "🔧 创建Python虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ 虚拟环境创建成功"
else
    echo "⚠️  虚拟环境已存在，跳过创建"
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "⬆️  升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📦 安装Python依赖包..."
pip install -r requirements.txt

# 检查依赖
echo "🔍 检查依赖安装情况..."
python check_dependencies.py || {
    echo "❌ 依赖检查失败，请检查上述错误信息"
    exit 1
}

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p data

# 检查前端构建文件
echo "🌐 检查前端构建文件..."
if [ -d "../frontend/build" ]; then
    echo "✅ 前端构建文件存在"
else
    echo "⚠️  前端构建文件不存在，如需完整功能请先构建前端"
fi

echo ""
echo "🎉 部署完成！"
echo ""
echo "📋 启动命令："
echo "   source backend/venv/bin/activate"
echo "   python backend/app/main.py"
echo ""
echo "📱 访问地址："
echo "   前端应用: http://localhost:8000/"
echo "   API文档: http://localhost:8000/docs"
echo "   健康检查: http://localhost:8000/api/health"
echo ""
echo "🔐 首次使用："
echo "   1. 访问系统注册新账号"
echo "   2. 或使用默认账号（如已配置）"
echo ""

# 询问是否立即启动
read -p "是否立即启动服务？(y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 正在启动服务..."
    python app/main.py
fi