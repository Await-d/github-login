#!/bin/bash

# Docker构建测试脚本

echo "🐳 GitHub账号管理系统 - Docker构建测试"
echo "=========================================="

# 检查Docker是否可用
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装或不可用"
    exit 1
fi

echo "📋 Docker版本："
docker --version
echo ""

# 测试所有Dockerfile版本
DOCKERFILES=(
    "Dockerfile.simple:简化版"
    "Dockerfile:标准版" 
    "Dockerfile.optimized:优化版"
)

SUCCESS_COUNT=0
TOTAL_COUNT=${#DOCKERFILES[@]}

for dockerfile_info in "${DOCKERFILES[@]}"; do
    IFS=':' read -r dockerfile description <<< "$dockerfile_info"
    
    echo "🔨 测试 $description ($dockerfile)..."
    
    if docker build -f "$dockerfile" -t "github-manager:test-$dockerfile" . --no-cache; then
        echo "✅ $description 构建成功"
        
        # 获取镜像大小
        size=$(docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" | grep "github-manager:test-$dockerfile" | awk '{print $2}')
        echo "📊 镜像大小: $size"
        
        # 清理测试镜像
        docker rmi "github-manager:test-$dockerfile" >/dev/null 2>&1
        
        ((SUCCESS_COUNT++))
    else
        echo "❌ $description 构建失败"
    fi
    echo ""
done

echo "📊 构建测试结果："
echo "   成功: $SUCCESS_COUNT/$TOTAL_COUNT"

if [ $SUCCESS_COUNT -eq $TOTAL_COUNT ]; then
    echo "✅ 所有Docker配置构建成功！"
    echo ""
    echo "🚀 推荐使用方式："
    echo "   开发测试: docker build -f Dockerfile.simple -t github-manager ."
    echo "   生产环境: docker build -f Dockerfile.optimized -t github-manager ."
    echo "   快速部署: docker-compose -f docker-compose.simple.yml up -d"
else
    echo "⚠️  部分Docker配置构建失败，请检查错误信息"
fi

echo ""
echo "🧹 清理完成"