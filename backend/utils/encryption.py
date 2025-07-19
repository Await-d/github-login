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
    # 开发环境生成一个固定的密钥
    ENCRYPTION_KEY = Fernet.generate_key().decode()

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