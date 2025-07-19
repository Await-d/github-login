"""
TOTP工具模块
"""

import pyotp
import time
from typing import Dict


def generate_totp_token(secret: str) -> Dict[str, str]:
    """
    生成TOTP令牌
    
    Args:
        secret: TOTP密钥
        
    Returns:
        包含令牌信息的字典
    """
    try:
        # 创建TOTP对象
        totp = pyotp.TOTP(secret)
        
        # 生成当前令牌
        token = totp.now()
        
        # 计算剩余时间
        current_time = int(time.time())
        time_remaining = 30 - (current_time % 30)
        
        # 格式化令牌（添加空格）
        formatted_token = f"{token[:3]} {token[3:]}"
        
        return {
            "token": token,
            "time_remaining": time_remaining,
            "formatted_token": formatted_token
        }
    except Exception as e:
        raise ValueError(f"生成TOTP令牌失败: {str(e)}")


def verify_totp_token(secret: str, token: str) -> bool:
    """
    验证TOTP令牌
    
    Args:
        secret: TOTP密钥
        token: 要验证的令牌
        
    Returns:
        验证结果
    """
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(token, valid_window=1)  # 允许前后30秒的窗口
    except Exception:
        return False


def validate_totp_secret(secret: str) -> bool:
    """
    验证TOTP密钥格式是否正确
    
    Args:
        secret: TOTP密钥
        
    Returns:
        验证结果
    """
    try:
        # 尝试创建TOTP对象来验证密钥格式
        pyotp.TOTP(secret)
        return True
    except Exception:
        return False