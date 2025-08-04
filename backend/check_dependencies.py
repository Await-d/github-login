#!/usr/bin/env python3
"""
依赖检查脚本 - 检查所有必要的Python包是否正确安装
"""

import sys
import importlib

# 必要的依赖包列表
REQUIRED_PACKAGES = [
    ('fastapi', 'FastAPI web框架'),
    ('uvicorn', 'ASGI服务器'),
    ('sqlalchemy', '数据库ORM'),
    ('pydantic', '数据验证'),
    ('jose', 'JWT处理'),
    ('passlib', '密码哈希'),
    ('cryptography', '加密'),
    ('pyotp', 'TOTP验证码'),
    ('multipart', '文件上传处理'),
    ('dotenv', '环境变量'),
]

# 可选的依赖包（用于网站模拟功能）
OPTIONAL_PACKAGES = [
    ('requests', 'HTTP请求库'),
    ('bs4', 'HTML解析库'),
]

def check_package(package_name, description):
    """检查单个包是否可用"""
    try:
        importlib.import_module(package_name)
        return True, f"✅ {description} ({package_name})"
    except ImportError as e:
        return False, f"❌ {description} ({package_name}) - {str(e)}"

def main():
    """主检查函数"""
    print("🔍 检查Python依赖包...")
    print("=" * 50)
    
    all_good = True
    
    # 检查必要依赖
    print("\n📦 必要依赖包:")
    for package, desc in REQUIRED_PACKAGES:
        success, message = check_package(package, desc)
        print(f"   {message}")
        if not success:
            all_good = False
    
    # 检查可选依赖
    print("\n🔧 可选依赖包 (用于网站模拟功能):")
    optional_missing = 0
    for package, desc in OPTIONAL_PACKAGES:
        success, message = check_package(package, desc)
        print(f"   {message}")
        if not success:
            optional_missing += 1
    
    # 检查Python版本
    print(f"\n🐍 Python版本: {sys.version}")
    
    # 总结
    print("\n" + "=" * 50)
    if all_good:
        print("🎉 所有必要依赖包都已正确安装！")
        if optional_missing > 0:
            print(f"⚠️  有 {optional_missing} 个可选依赖包缺失，网站模拟功能可能不可用")
        else:
            print("✨ 包括可选依赖在内，所有包都已安装！")
        
        # 尝试导入主要模块
        print("\n🧪 测试主要模块导入...")
        try:
            from app.main import app
            print("✅ 主应用模块导入成功")
        except Exception as e:
            print(f"❌ 主应用模块导入失败: {e}")
            all_good = False
        
        try:
            from utils.website_simulator import website_simulator
            print("✅ 网站模拟器模块导入成功")
        except Exception as e:
            print(f"⚠️  网站模拟器模块导入失败: {e} (功能将降级)")
        
    else:
        print("❌ 有必要的依赖包缺失，请安装后再运行系统")
        print("\n📋 安装命令:")
        print("   pip install -r requirements.txt")
    
    return 0 if all_good else 1

if __name__ == "__main__":
    exit(main())