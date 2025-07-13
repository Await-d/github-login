#!/bin/bash

# Docker权限问题诊断和修复脚本

echo "🔧 Docker数据库权限问题修复工具"
echo "=================================="

echo "📋 当前可用的解决方案:"
echo ""
echo "1. 🚀 快速解决方案 - 使用Root用户版本"
echo "   docker-compose -f docker-compose.root.yml up -d"
echo ""
echo "2. 📦 标准解决方案 - 修复数据目录权限"
echo "   mkdir -p ./data && chmod 777 ./data"
echo "   docker-compose up -d"
echo ""
echo "3. 🔒 安全解决方案 - 设置正确的用户权限"
echo "   sudo chown -R 1001:1001 ./data"
echo "   docker-compose up -d"

echo ""
read -p "选择解决方案 (1-3, 或按回车查看详细信息): " choice

case $choice in
    1)
        echo ""
        echo "🚀 使用Root用户版本..."
        echo "这是最简单的解决方案，适合快速部署和测试"
        
        # 停止现有容器
        docker-compose down 2>/dev/null || true
        docker-compose -f docker-compose.root.yml down 2>/dev/null || true
        
        # 启动root版本
        echo "构建并启动root版本容器..."
        docker-compose -f docker-compose.root.yml up -d
        
        echo "✅ Root版本启动完成"
        echo "访问: http://localhost:3000"
        ;;
        
    2)
        echo ""
        echo "📦 修复数据目录权限..."
        
        # 创建并修复数据目录权限
        mkdir -p ./data
        chmod 777 ./data
        echo "✅ 数据目录权限已修复"
        
        # 停止现有容器
        docker-compose down 2>/dev/null || true
        
        # 启动标准版本
        echo "启动标准版本容器..."
        docker-compose up -d
        
        echo "✅ 标准版本启动完成"
        echo "访问: http://localhost:3000"
        ;;
        
    3)
        echo ""
        echo "🔒 设置安全权限..."
        
        # 创建数据目录
        mkdir -p ./data
        
        # 设置正确的用户权限
        if command -v sudo >/dev/null 2>&1; then
            sudo chown -R 1001:1001 ./data
            echo "✅ 已设置用户权限 (1001:1001)"
        else
            echo "⚠️  需要sudo权限，手动设置权限:"
            echo "   chown -R 1001:1001 ./data"
        fi
        
        # 停止现有容器
        docker-compose down 2>/dev/null || true
        
        # 启动标准版本
        echo "启动标准版本容器..."
        docker-compose up -d
        
        echo "✅ 安全版本启动完成"
        echo "访问: http://localhost:3000"
        ;;
        
    *)
        echo ""
        echo "📚 详细信息:"
        echo ""
        echo "🔍 权限问题原因:"
        echo "- Docker容器中的nodejs用户(UID:1001)无法写入数据目录"
        echo "- SQLite需要在数据目录创建和修改数据库文件"
        echo "- 宿主机和容器之间的权限映射问题"
        echo ""
        echo "💡 解决方案对比:"
        echo ""
        echo "方案1 (Root版本):"
        echo "  ✅ 最简单，立即生效"
        echo "  ✅ 无需权限配置"
        echo "  ⚠️  安全性较低(容器以root运行)"
        echo ""
        echo "方案2 (777权限):"
        echo "  ✅ 简单有效"
        echo "  ✅ 兼容性好"
        echo "  ⚠️  权限过于宽松"
        echo ""
        echo "方案3 (正确权限):"
        echo "  ✅ 最安全"
        echo "  ✅ 符合最佳实践"
        echo "  ⚠️  需要管理员权限"
        echo ""
        echo "🎯 推荐:"
        echo "- 开发测试: 使用方案1 (Root版本)"
        echo "- 生产环境: 使用方案3 (正确权限)"
        echo ""
        echo "重新运行脚本选择具体方案"
        ;;
esac

echo ""
echo "📊 容器状态检查:"
docker ps | grep github || echo "没有运行中的GitHub管理容器"

echo ""
echo "🔗 有用的命令:"
echo "- 查看日志: docker-compose logs -f"
echo "- 停止服务: docker-compose down"
echo "- 重启服务: docker-compose restart"