#!/bin/bash

# GitHub账号管理系统构建脚本

echo "🚀 开始构建GitHub账号管理系统..."

# 检查Node.js版本
echo "📋 检查Node.js版本..."
node --version
npm --version

# 安装依赖
echo "📦 安装依赖..."
npm install

# 构建项目
echo "🔨 构建TypeScript项目..."
npm run build

# 运行测试
echo "🧪 运行功能测试..."
node test-system.js

# 检查构建结果
if [ -d "dist" ] && [ -f "dist/server.js" ]; then
    echo "✅ 构建成功！"
    echo "📁 构建文件位于 dist/ 目录"
    echo ""
    echo "🐳 Docker 相关文件已创建："
    echo "   - Dockerfile"
    echo "   - .dockerignore"  
    echo "   - docker-compose.yml"
    echo "   - .drone.yml"
    echo ""
    echo "📝 使用方法："
    echo "   开发模式: npm run dev"
    echo "   生产模式: npm start"
    echo "   Docker构建: docker build -t github-manager ."
    echo "   Docker运行: docker-compose up -d"
    echo ""
    echo "🌐 访问地址: http://localhost:3000"
else
    echo "❌ 构建失败！"
    exit 1
fi