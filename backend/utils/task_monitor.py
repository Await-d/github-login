"""
定时任务监控和日志记录模块
提供详细的执行状态反馈和性能监控
"""

import json
import time
import psutil
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from contextlib import contextmanager

@dataclass
class TaskExecutionMetrics:
    """任务执行指标"""
    task_id: int
    task_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    memory_usage_mb: float = 0.0
    cpu_percent: float = 0.0
    status: str = "running"
    processed_accounts: int = 0
    successful_accounts: int = 0
    failed_accounts: int = 0
    error_details: List[str] = None
    browser_sessions: int = 0
    network_requests: int = 0
    
    def __post_init__(self):
        if self.error_details is None:
            self.error_details = []

@dataclass
class AccountExecutionResult:
    """单个账户执行结果"""
    account_id: int
    username: str
    status: str  # success, failed, skipped
    start_time: datetime
    end_time: Optional[datetime] = None
    duration: Optional[float] = None
    message: str = ""
    error_type: Optional[str] = None
    retry_count: int = 0
    browser_events: List[str] = None
    final_url: Optional[str] = None
    cookies_count: int = 0
    
    def __post_init__(self):
        if self.browser_events is None:
            self.browser_events = []

class TaskMonitor:
    """任务监控器"""
    
    def __init__(self):
        self.active_tasks: Dict[int, TaskExecutionMetrics] = {}
        self.process = psutil.Process()
        
    @contextmanager
    def monitor_task_execution(self, task_id: int, task_name: str):
        """
        监控任务执行的上下文管理器
        
        Usage:
            with task_monitor.monitor_task_execution(task_id, task_name) as metrics:
                # 执行任务
                pass
        """
        metrics = TaskExecutionMetrics(
            task_id=task_id,
            task_name=task_name,
            start_time=datetime.utcnow(),
            memory_usage_mb=self._get_memory_usage(),
            cpu_percent=self._get_cpu_percent()
        )
        
        self.active_tasks[task_id] = metrics
        
        try:
            yield metrics
            
            # 任务成功完成
            metrics.status = "completed"
            metrics.end_time = datetime.utcnow()
            metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
            
        except Exception as e:
            # 任务执行异常
            metrics.status = "failed"
            metrics.end_time = datetime.utcnow()
            metrics.duration = (metrics.end_time - metrics.start_time).total_seconds()
            metrics.error_details.append(f"Task execution failed: {str(e)}")
            
            raise
            
        finally:
            # 记录最终系统资源使用情况
            metrics.memory_usage_mb = self._get_memory_usage()
            metrics.cpu_percent = self._get_cpu_percent()
            
            # 从活跃任务中移除
            self.active_tasks.pop(task_id, None)
            
            # 输出监控总结
            self._log_task_summary(metrics)
    
    def update_account_metrics(self, task_id: int, account_result: AccountExecutionResult):
        """更新账户处理指标"""
        if task_id in self.active_tasks:
            metrics = self.active_tasks[task_id]
            metrics.processed_accounts += 1
            
            if account_result.status == "success":
                metrics.successful_accounts += 1
            elif account_result.status == "failed":
                metrics.failed_accounts += 1
                if account_result.error_type:
                    metrics.error_details.append(
                        f"Account {account_result.username}: {account_result.error_type}"
                    )
    
    def increment_browser_session(self, task_id: int):
        """增加浏览器会话计数"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].browser_sessions += 1
    
    def increment_network_request(self, task_id: int):
        """增加网络请求计数"""
        if task_id in self.active_tasks:
            self.active_tasks[task_id].network_requests += 1
    
    def get_task_metrics(self, task_id: int) -> Optional[TaskExecutionMetrics]:
        """获取任务指标"""
        return self.active_tasks.get(task_id)
    
    def get_all_active_tasks(self) -> Dict[int, TaskExecutionMetrics]:
        """获取所有活跃任务"""
        return self.active_tasks.copy()
    
    def _get_memory_usage(self) -> float:
        """获取内存使用量（MB）"""
        try:
            return self.process.memory_info().rss / 1024 / 1024
        except:
            return 0.0
    
    def _get_cpu_percent(self) -> float:
        """获取CPU使用百分比"""
        try:
            return self.process.cpu_percent()
        except:
            return 0.0
    
    def _log_task_summary(self, metrics: TaskExecutionMetrics):
        """输出任务执行总结"""
        print(f"\n📊 任务执行总结 - {metrics.task_name} (ID: {metrics.task_id})")
        print(f"   状态: {'✅ 成功' if metrics.status == 'completed' else '❌ 失败' if metrics.status == 'failed' else '⏳ 运行中'}")
        print(f"   执行时间: {metrics.duration:.2f}秒" if metrics.duration else "   执行中...")
        print(f"   处理账户: {metrics.processed_accounts} 个")
        print(f"   成功/失败: {metrics.successful_accounts}/{metrics.failed_accounts}")
        print(f"   内存使用: {metrics.memory_usage_mb:.1f} MB")
        print(f"   CPU使用: {metrics.cpu_percent:.1f}%")
        print(f"   浏览器会话: {metrics.browser_sessions} 个")
        print(f"   网络请求: {metrics.network_requests} 次")
        
        if metrics.error_details:
            print(f"   错误详情:")
            for error in metrics.error_details[-3:]:  # 显示最近3个错误
                print(f"     - {error}")

class EnhancedTaskLogger:
    """增强的任务日志记录器"""
    
    def __init__(self):
        self.log_entries: List[Dict] = []
        
    def log_task_start(self, task_id: int, task_name: str, account_count: int):
        """记录任务开始"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "task_start",
            "task_id": task_id,
            "task_name": task_name,
            "account_count": account_count,
            "message": f"开始执行任务 '{task_name}' - {account_count} 个账户"
        }
        self.log_entries.append(entry)
        print(f"🚀 {entry['message']}")
    
    def log_account_start(self, task_id: int, account_id: int, username: str):
        """记录账户处理开始"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "account_start",
            "task_id": task_id,
            "account_id": account_id,
            "username": username,
            "message": f"开始处理账户: {username}"
        }
        self.log_entries.append(entry)
        print(f"🔄 {entry['message']}")
    
    def log_account_result(self, task_id: int, result: AccountExecutionResult):
        """记录账户处理结果"""
        status_icon = "✅" if result.status == "success" else "❌" if result.status == "failed" else "⏭️"
        
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "account_result",
            "task_id": task_id,
            "account_id": result.account_id,
            "username": result.username,
            "status": result.status,
            "duration": result.duration,
            "message": result.message,
            "error_type": result.error_type,
            "retry_count": result.retry_count,
            "final_url": result.final_url,
            "cookies_count": result.cookies_count
        }
        self.log_entries.append(entry)
        
        duration_str = f" ({result.duration:.2f}s)" if result.duration else ""
        retry_str = f" (重试{result.retry_count}次)" if result.retry_count > 0 else ""
        
        print(f"{status_icon} 账户 {result.username}: {result.message}{duration_str}{retry_str}")
        
        if result.error_type and result.status == "failed":
            print(f"   错误类型: {result.error_type}")
        
        if result.final_url:
            print(f"   最终URL: {result.final_url}")
    
    def log_browser_event(self, task_id: int, account_id: int, event: str):
        """记录浏览器事件"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "browser_event",
            "task_id": task_id,
            "account_id": account_id,
            "browser_event": event
        }
        self.log_entries.append(entry)
        print(f"   🌐 {event}")
    
    def log_retry_attempt(self, task_id: int, account_id: int, username: str, attempt: int, max_attempts: int, error: str):
        """记录重试尝试"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "retry_attempt",
            "task_id": task_id,
            "account_id": account_id,
            "username": username,
            "attempt": attempt,
            "max_attempts": max_attempts,
            "error": error
        }
        self.log_entries.append(entry)
        print(f"🔄 账户 {username} 重试 {attempt}/{max_attempts}: {error}")
    
    def log_task_complete(self, task_id: int, success_count: int, total_count: int, duration: float):
        """记录任务完成"""
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event": "task_complete",
            "task_id": task_id,
            "success_count": success_count,
            "total_count": total_count,
            "success_rate": success_count / total_count if total_count > 0 else 0,
            "duration": duration
        }
        self.log_entries.append(entry)
        
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        print(f"🏁 任务完成: {success_count}/{total_count} 成功 ({success_rate:.1f}%) - 耗时 {duration:.2f}秒")
    
    def get_task_logs(self, task_id: int) -> List[Dict]:
        """获取特定任务的日志"""
        return [entry for entry in self.log_entries if entry.get("task_id") == task_id]
    
    def get_recent_logs(self, limit: int = 100) -> List[Dict]:
        """获取最近的日志记录"""
        return self.log_entries[-limit:]
    
    def clear_old_logs(self, keep_hours: int = 24):
        """清理旧日志记录"""
        cutoff_time = datetime.utcnow().timestamp() - (keep_hours * 3600)
        
        self.log_entries = [
            entry for entry in self.log_entries
            if datetime.fromisoformat(entry["timestamp"]).timestamp() > cutoff_time
        ]
    
    def export_logs_json(self, task_id: Optional[int] = None) -> str:
        """导出日志为JSON格式"""
        if task_id:
            logs = self.get_task_logs(task_id)
        else:
            logs = self.log_entries
        
        return json.dumps(logs, indent=2, ensure_ascii=False)

# 全局实例
task_monitor = TaskMonitor()
task_logger = EnhancedTaskLogger()

def get_task_execution_summary(task_id: int) -> Optional[Dict]:
    """获取任务执行摘要"""
    logs = task_logger.get_task_logs(task_id)
    metrics = task_monitor.get_task_metrics(task_id)
    
    if not logs and not metrics:
        return None
    
    # 计算统计信息
    account_events = [log for log in logs if log["event"] == "account_result"]
    success_count = len([log for log in account_events if log["status"] == "success"])
    failed_count = len([log for log in account_events if log["status"] == "failed"])
    
    retry_events = [log for log in logs if log["event"] == "retry_attempt"]
    total_retries = len(retry_events)
    
    summary = {
        "task_id": task_id,
        "total_accounts": len(account_events),
        "success_count": success_count,
        "failed_count": failed_count,
        "success_rate": success_count / len(account_events) if account_events else 0,
        "total_retries": total_retries,
        "logs_count": len(logs),
        "last_update": datetime.utcnow().isoformat()
    }
    
    if metrics:
        summary.update({
            "status": metrics.status,
            "duration": metrics.duration,
            "memory_usage_mb": metrics.memory_usage_mb,
            "cpu_percent": metrics.cpu_percent,
            "browser_sessions": metrics.browser_sessions,
            "network_requests": metrics.network_requests
        })
    
    return summary