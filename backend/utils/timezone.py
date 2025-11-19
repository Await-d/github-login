"""
时区处理工具函数
"""

from datetime import datetime, timezone
from typing import Optional


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    确保datetime对象带有UTC时区信息

    Args:
        dt: datetime对象或ISO格式字符串

    Returns:
        带有UTC时区信息的datetime对象,或None
    """
    if dt is None:
        return None
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)
