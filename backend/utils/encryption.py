"""
加密工具模块
"""

from cryptography.fernet import Fernet
from passlib.context import CryptContext
import os
import base64

# 密码哈希工具
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 加密密钥 (生产环境应该从环境变量读取)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
if not ENCRYPTION_KEY:
    # 开发环境使用一个固定的密钥 (必须是32字节)
    # 注意：生产环境必须设置 ENCRYPTION_KEY 环境变量
    secret_bytes = b"github_manager_secret_key_32byte"  # 正好32字节
    ENCRYPTION_KEY = base64.urlsafe_b64encode(secret_bytes).decode()

# 确保密钥格式正确
try:
    fernet = Fernet(ENCRYPTION_KEY.encode())
except ValueError:
    # 如果密钥格式不正确，生成一个新的
    secret_bytes = b"github_manager_secret_key_32byte"  # 正好32字节
    ENCRYPTION_KEY = base64.urlsafe_b64encode(secret_bytes).decode()
    fernet = Fernet(ENCRYPTION_KEY.encode())


def hash_password(password: str) -> str:
    """哈希密码"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return pwd_context.verify(plain_password, hashed_password)


def encrypt_data(data: str) -> str:
    """加密数据"""
    return fernet.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    """解密数据"""
    return fernet.decrypt(encrypted_data.encode()).decode()