"""
应用配置管理
使用环境变量管理敏感配置
"""
import os
from typing import Optional


class Config:
    """应用配置类"""
    
    # JWT配置
    JWT_SECRET_KEY: str = os.environ.get(
        'JWT_SECRET_KEY',
        'github_manager_jwt_secret_key_change_in_production'  # 默认值仅用于开发
    )
    JWT_ALGORITHM: str = os.environ.get('JWT_ALGORITHM', 'HS256')
    JWT_EXPIRE_MINUTES: int = int(os.environ.get('JWT_EXPIRE_MINUTES', '43200'))  # 30天
    
    # 数据库加密密钥
    ENCRYPTION_KEY: Optional[str] = os.environ.get('ENCRYPTION_KEY')
    
    # 速率限制配置
    RATE_LIMIT_ENABLED: bool = os.environ.get('RATE_LIMIT_ENABLED', 'true').lower() == 'true'
    
    # 批量操作限制
    MAX_BATCH_IMPORT_SIZE: int = int(os.environ.get('MAX_BATCH_IMPORT_SIZE', '100'))
    
    # 队列配置
    ACCOUNT_DELAY_MIN: int = int(os.environ.get('ACCOUNT_DELAY_MIN', '3'))
    ACCOUNT_DELAY_MAX: int = int(os.environ.get('ACCOUNT_DELAY_MAX', '8'))
    MAX_RETRY: int = int(os.environ.get('MAX_RETRY', '2'))
    RETRY_DELAY: int = int(os.environ.get('RETRY_DELAY', '10'))
    
    @classmethod
    def validate(cls):
        """验证关键配置是否正确设置"""
        warnings = []
        
        # 检查JWT密钥
        if cls.JWT_SECRET_KEY == 'github_manager_jwt_secret_key_change_in_production':
            warnings.append(
                "⚠️  WARNING: 使用默认JWT密钥!生产环境请设置JWT_SECRET_KEY环境变量!"
            )
        
        # 检查加密密钥
        if not cls.ENCRYPTION_KEY:
            warnings.append(
                "⚠️  WARNING: 未设置ENCRYPTION_KEY环境变量,将使用默认加密方式"
            )
        
        return warnings
    
    @classmethod
    def print_config(cls):
        """打印配置信息(隐藏敏感值)"""
        print("=" * 50)
        print("应用配置:")
        print(f"  JWT_ALGORITHM: {cls.JWT_ALGORITHM}")
        print(f"  JWT_EXPIRE_MINUTES: {cls.JWT_EXPIRE_MINUTES}")
        print(f"  JWT_SECRET_KEY: {'*' * 20} (已设置)")
        print(f"  ENCRYPTION_KEY: {'*' * 20 if cls.ENCRYPTION_KEY else '未设置'}")
        print(f"  RATE_LIMIT_ENABLED: {cls.RATE_LIMIT_ENABLED}")
        print(f"  MAX_BATCH_IMPORT_SIZE: {cls.MAX_BATCH_IMPORT_SIZE}")
        print(f"  ACCOUNT_DELAY: {cls.ACCOUNT_DELAY_MIN}-{cls.ACCOUNT_DELAY_MAX}秒")
        print(f"  MAX_RETRY: {cls.MAX_RETRY}")
        print(f"  RETRY_DELAY: {cls.RETRY_DELAY}秒")
        print("=" * 50)
        
        # 打印警告
        warnings = cls.validate()
        if warnings:
            print("\n配置警告:")
            for warning in warnings:
                print(warning)
            print()


# 创建配置实例
config = Config()
