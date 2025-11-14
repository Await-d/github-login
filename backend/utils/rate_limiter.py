"""
简单的速率限制实现
使用内存缓存跟踪API调用频率
"""
from datetime import datetime, timedelta
from typing import Dict, Tuple
from fastapi import HTTPException, status
import threading


class RateLimiter:
    """内存速率限制器"""
    
    def __init__(self):
        self._requests: Dict[str, list] = {}
        self._lock = threading.Lock()
    
    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> Tuple[bool, int]:
        """
        检查是否超过速率限制
        
        Args:
            key: 限流键(如用户ID)
            max_requests: 时间窗口内最大请求数
            window_seconds: 时间窗口(秒)
            
        Returns:
            (是否允许, 剩余请求数)
        """
        with self._lock:
            now = datetime.now()
            cutoff_time = now - timedelta(seconds=window_seconds)
            
            # 获取该键的请求历史
            if key not in self._requests:
                self._requests[key] = []
            
            # 清理过期的请求记录
            self._requests[key] = [
                req_time for req_time in self._requests[key]
                if req_time > cutoff_time
            ]
            
            # 检查是否超限
            current_count = len(self._requests[key])
            
            if current_count >= max_requests:
                return False, 0
            
            # 记录本次请求
            self._requests[key].append(now)
            
            remaining = max_requests - current_count - 1
            return True, remaining
    
    def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """清理旧的限流记录,释放内存"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(seconds=max_age_seconds)
            keys_to_remove = []
            
            for key, requests in self._requests.items():
                # 清理该键的过期请求
                self._requests[key] = [
                    req_time for req_time in requests
                    if req_time > cutoff_time
                ]
                
                # 如果该键没有任何请求记录,标记删除
                if not self._requests[key]:
                    keys_to_remove.append(key)
            
            # 删除空键
            for key in keys_to_remove:
                del self._requests[key]


# 全局限流器实例
rate_limiter = RateLimiter()


def check_batch_execute_rate_limit(user_id: int):
    """
    检查批量执行的速率限制
    5分钟内最多5次批量执行
    """
    key = f"batch_execute_{user_id}"
    allowed, remaining = rate_limiter.check_rate_limit(
        key=key,
        max_requests=5,
        window_seconds=300  # 5分钟
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="批量执行操作过于频繁,请5分钟后再试"
        )
    
    return remaining


def check_task_execute_rate_limit(user_id: int):
    """
    检查单个任务执行的速率限制
    1分钟内最多10次
    """
    key = f"task_execute_{user_id}"
    allowed, remaining = rate_limiter.check_rate_limit(
        key=key,
        max_requests=10,
        window_seconds=60
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="执行操作过于频繁,请1分钟后再试"
        )
    
    return remaining


def check_batch_import_rate_limit(user_id: int):
    """
    检查批量导入的速率限制
    5分钟内最多3次
    """
    key = f"batch_import_{user_id}"
    allowed, remaining = rate_limiter.check_rate_limit(
        key=key,
        max_requests=3,
        window_seconds=300
    )
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="批量导入操作过于频繁,请5分钟后再试"
        )
    
    return remaining
