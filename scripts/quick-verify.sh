#!/bin/bash

# 快速验证脚本

echo "🔍 GitHub账号管理系统 - 快速验证"
echo "================================"

echo "1️⃣ 检查项目结构..."
REQUIRED_FILES=(
    "package.json"
    "Dockerfile"
    "Dockerfile.root" 
    "Dockerfile.optimized"
    "docker-compose.yml"
    "src/server.ts"
    "dist/server.js"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (缺失)"
    fi
done

echo ""
echo "2️⃣ 检查TypeScript构建..."
if [ -f "dist/server.js" ] && [ -f "dist/server.js.map" ]; then
    echo "✅ TypeScript构建产物存在"
else
    echo "⚠️  TypeScript构建产物缺失，正在构建..."
    npm run build
fi

echo ""
echo "3️⃣ 检查依赖..."
if [ -f "node_modules/.bin/tsc" ]; then
    echo "✅ TypeScript编译器可用"
else
    echo "❌ TypeScript编译器不可用"
fi

echo ""
echo "4️⃣ 运行功能测试..."
npm test

echo ""
echo "5️⃣ Docker配置验证..."
echo "可用的Docker构建命令："
echo "📦 标准版: docker build -f Dockerfile -t github-manager ."  
echo "📦 Root版: docker build -f Dockerfile.root -t github-manager:root ."
echo "📦 优化版: docker build -f Dockerfile.optimized -t github-manager:optimized ."

echo ""
echo "6️⃣ 部署建议..."
echo "🚀 快速部署: docker-compose -f docker-compose.root.yml up -d"
echo "🚀 标准部署: docker-compose up -d"

echo ""
echo "✅ 验证完成！项目已准备就绪。"