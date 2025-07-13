#!/bin/bash

# Docker测试脚本

echo "🐳 GitHub账号管理系统 Docker 测试"
echo "=================================="

# 检查Docker是否可用
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装或不可用"
    exit 1
fi

echo "📋 Docker版本："
docker --version

echo ""
echo "🔨 构建Docker镜像..."
if docker build -t github-manager:test .; then
    echo "✅ Docker镜像构建成功"
else
    echo "❌ Docker镜像构建失败"
    exit 1
fi

echo ""
echo "📊 镜像信息："
docker images | grep github-manager

echo ""
echo "🚀 启动测试容器..."
docker run -d --name github-manager-test -p 3001:3000 github-manager:test

echo "⏳ 等待容器启动..."
sleep 10

echo ""
echo "🔍 检查容器状态："
docker ps | grep github-manager-test

echo ""
echo "🏥 健康检查："
if docker exec github-manager-test curl -f http://localhost:3000/api/health 2>/dev/null; then
    echo "✅ 应用健康检查通过"
else
    echo "⚠️ 健康检查失败，查看容器日志："
    docker logs github-manager-test
fi

echo ""
echo "🧹 清理测试容器..."
docker stop github-manager-test
docker rm github-manager-test

echo ""
echo "✅ Docker测试完成"
echo "📝 如需手动测试，使用："
echo "   docker run -d --name github-manager -p 3000:3000 github-manager:test"
echo "   访问: http://localhost:3000"