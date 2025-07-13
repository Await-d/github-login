#!/bin/bash

# 本地Docker测试脚本

echo "🧪 本地Docker权限测试"
echo "====================="

# 构建并测试权限
echo "🔨 重新构建镜像..."
npm run build

echo ""
echo "📁 创建本地测试数据目录..."
mkdir -p ./test-data
chmod 755 ./test-data

echo ""
echo "🐳 测试Docker容器启动..."
echo "容器名: github-manager-test"
echo "端口: 3001:3000"
echo "数据卷: ./test-data:/app/data"

# 停止并清理旧容器
docker stop github-manager-test 2>/dev/null || true
docker rm github-manager-test 2>/dev/null || true

# 启动测试容器
docker run -d \
  --name github-manager-test \
  -p 3001:3000 \
  -e NODE_ENV=development \
  -e DATABASE_DIR=/app/data \
  -v "$(pwd)/test-data:/app/data" \
  github-manager:latest

echo ""
echo "⏳ 等待容器启动..."
sleep 5

echo ""
echo "📋 容器状态:"
docker ps | grep github-manager-test

echo ""
echo "📋 容器日志:"
docker logs github-manager-test

echo ""
echo "🏥 健康检查:"
for i in {1..5}; do
    echo "尝试 $i/5..."
    if curl -s http://localhost:3001/api/health >/dev/null; then
        echo "✅ 健康检查通过"
        break
    else
        echo "⏳ 等待应用启动..."
        sleep 2
    fi
done

echo ""
echo "📊 数据目录状态:"
ls -la ./test-data

echo ""
echo "🧹 清理测试环境..."
read -p "是否清理测试容器和数据? (y/N): " cleanup
if [[ $cleanup =~ ^[Yy]$ ]]; then
    docker stop github-manager-test
    docker rm github-manager-test
    rm -rf ./test-data
    echo "✅ 清理完成"
else
    echo "💡 测试容器继续运行在端口3001"
    echo "   访问: http://localhost:3001"
    echo "   清理: docker stop github-manager-test && docker rm github-manager-test"
fi