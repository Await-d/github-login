"""
任务调度器 - 处理cron表达式和时间计算
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
import croniter
import pytz


def calculate_next_run_time(cron_expression: str, tz: str = "Asia/Shanghai", from_time: Optional[datetime] = None) -> datetime:
    """
    计算下次执行时间
    
    Args:
        cron_expression: cron表达式
        tz: 时区
        from_time: 基准时间，默认为当前时间
    
    Returns:
        下次执行的时间
    """
    # 设置时区
    timezone_obj = pytz.timezone(tz)
    
    if from_time is None:
        # 直接获取指定时区的当前时间，避免时区转换错误
        from_time = datetime.now(timezone_obj)
    elif from_time.tzinfo is None:
        # 如果传入的时间没有时区信息，将其本地化到指定时区
        from_time = timezone_obj.localize(from_time)
    else:
        # 如果已有时区信息，转换到指定时区
        from_time = from_time.astimezone(timezone_obj)
    
    # 使用croniter计算下次执行时间
    try:
        cron = croniter.croniter(cron_expression, from_time)
        next_time = cron.get_next(datetime)
        
        # 转换为UTC时间存储
        return next_time.astimezone(timezone.utc).replace(tzinfo=None)
    
    except Exception as e:
        raise ValueError(f"无效的cron表达式: {cron_expression}, 错误: {str(e)}")


def is_time_to_run(task_next_run_time: datetime, tolerance_seconds: int = 30) -> bool:
    """
    检查是否到了执行时间
    
    Args:
        task_next_run_time: 任务的下次执行时间(UTC)
        tolerance_seconds: 容忍的时间误差(秒)
    
    Returns:
        是否应该执行
    """
    now = datetime.utcnow()
    time_diff = (now - task_next_run_time).total_seconds()
    
    # 在容忍范围内或已过执行时间
    return -tolerance_seconds <= time_diff <= tolerance_seconds * 2


def validate_cron_expression(cron_expression: str) -> bool:
    """
    验证cron表达式是否有效
    
    Args:
        cron_expression: cron表达式
    
    Returns:
        是否有效
    """
    try:
        cron = croniter.croniter(cron_expression)
        # 尝试获取下一个执行时间
        cron.get_next()
        return True
    except:
        return False


def get_cron_description(cron_expression: str, tz: str = "Asia/Shanghai") -> str:
    """
    获取cron表达式的中文描述
    
    Args:
        cron_expression: cron表达式
        tz: 时区
    
    Returns:
        描述文本
    """
    try:
        # 简单的cron描述映射
        common_patterns = {
            "0 9 * * *": "每天上午9点",
            "0 */6 * * *": "每6小时执行一次",
            "0 9 * * 1-5": "工作日上午9点",
            "0 0 * * 0": "每周日零点",
            "0 0 1 * *": "每月1号零点",
            "*/30 * * * *": "每30分钟",
            "0 */2 * * *": "每2小时",
            "0 8,12,18 * * *": "每天8点、12点、18点"
        }
        
        if cron_expression in common_patterns:
            return common_patterns[cron_expression]
        
        # 计算接下来的几次执行时间作为描述
        timezone_obj = pytz.timezone(tz)
        now = datetime.now(timezone_obj)
        cron = croniter.croniter(cron_expression, now)
        
        next_times = []
        for _ in range(3):
            next_time = cron.get_next(datetime)
            next_times.append(next_time.strftime("%Y-%m-%d %H:%M"))
        
        return f"接下来执行: {', '.join(next_times)}"
    
    except:
        return "无效的cron表达式"


def get_next_n_run_times(cron_expression: str, n: int = 5, tz: str = "Asia/Shanghai") -> list:
    """
    获取接下来n次的执行时间
    
    Args:
        cron_expression: cron表达式
        n: 获取次数
        tz: 时区
    
    Returns:
        时间列表
    """
    try:
        timezone_obj = pytz.timezone(tz)
        now = datetime.now(timezone_obj)
        cron = croniter.croniter(cron_expression, now)
        
        times = []
        for _ in range(n):
            next_time = cron.get_next(datetime)
            times.append(next_time)
        
        return times
    
    except:
        return []


class TaskScheduler:
    """任务调度器类"""
    
    def __init__(self):
        self.running_tasks = set()  # 正在运行的任务ID
    
    def is_task_running(self, task_id: int) -> bool:
        """检查任务是否正在运行"""
        return task_id in self.running_tasks
    
    def mark_task_running(self, task_id: int):
        """标记任务为运行中"""
        self.running_tasks.add(task_id)
    
    def mark_task_completed(self, task_id: int):
        """标记任务完成"""
        self.running_tasks.discard(task_id)
    
    def get_pending_tasks(self, db_session, tolerance_seconds: int = 30):
        """
        获取待执行的任务
        
        Args:
            db_session: 数据库会话
            tolerance_seconds: 时间容忍度
        
        Returns:
            待执行的任务列表
        """
        from models.database import ScheduledTask
        
        now = datetime.utcnow()
        
        # 查询应该执行的任务
        tasks = db_session.query(ScheduledTask).filter(
            ScheduledTask.is_active == True,
            ScheduledTask.next_run_time <= now + timedelta(seconds=tolerance_seconds)
        ).all()
        
        # 过滤掉正在运行的任务
        pending_tasks = [
            task for task in tasks 
            if not self.is_task_running(task.id) and is_time_to_run(task.next_run_time, tolerance_seconds)
        ]
        
        return pending_tasks
    
    def update_task_next_run_time(self, task, db_session):
        """更新任务的下次执行时间"""
        try:
            next_run = calculate_next_run_time(task.cron_expression, task.timezone)
            task.next_run_time = next_run
            db_session.commit()
        except Exception as e:
            print(f"更新任务 {task.id} 的下次执行时间失败: {e}")


# 全局调度器实例
task_scheduler = TaskScheduler()