"""
仓库收藏任务队列管理器
使用异步队列实现任务串行执行，避免并发问题
"""

import asyncio
from typing import Dict, Optional, Callable, Any
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"      # 等待中
    RUNNING = "running"      # 执行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"        # 失败
    CANCELLED = "cancelled"  # 已取消


@dataclass
class QueueTask:
    """队列任务数据类"""
    task_id: int
    user_id: int
    repository_url: str
    account_ids: list[int]
    force_execute: bool
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now(timezone.utc)


class RepositoryStarQueue:
    """仓库收藏任务队列管理器（单例模式）"""

    _instance = None
    _lock = asyncio.Lock()

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._queue: asyncio.Queue = asyncio.Queue()
        self._tasks: Dict[int, QueueTask] = {}  # task_id -> QueueTask
        self._running_task: Optional[QueueTask] = None
        self._worker_task: Optional[asyncio.Task] = None
        self._is_running = False
        self._executor: Optional[Callable] = None

        print("✅ 仓库收藏任务队列管理器初始化完成")

    def set_executor(self, executor: Callable):
        """设置任务执行器函数"""
        self._executor = executor
        print(f"✅ 任务执行器已设置: {executor.__name__}")

    async def start(self):
        """启动队列worker"""
        async with self._lock:
            if self._is_running:
                print("⚠️ 队列worker已经在运行")
                return

            self._is_running = True
            self._worker_task = asyncio.create_task(self._worker())
            print("✅ 队列worker已启动")

    async def stop(self):
        """停止队列worker"""
        async with self._lock:
            if not self._is_running:
                return

            self._is_running = False
            if self._worker_task:
                self._worker_task.cancel()
                try:
                    await self._worker_task
                except asyncio.CancelledError:
                    pass
            print("✅ 队列worker已停止")

    async def add_task(
        self,
        task_id: int,
        user_id: int,
        repository_url: str,
        account_ids: list[int],
        force_execute: bool = False
    ) -> QueueTask:
        """添加任务到队列"""

        # 检查任务是否已存在
        if task_id in self._tasks:
            existing_task = self._tasks[task_id]
            if existing_task.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                print(f"⚠️ 任务 {task_id} 已在队列中，状态: {existing_task.status}")
                return existing_task

        # 创建新任务
        queue_task = QueueTask(
            task_id=task_id,
            user_id=user_id,
            repository_url=repository_url,
            account_ids=account_ids,
            force_execute=force_execute
        )

        self._tasks[task_id] = queue_task
        await self._queue.put(queue_task)

        queue_size = self._queue.qsize()
        print(f"✅ 任务 {task_id} 已加入队列 (队列大小: {queue_size})")

        return queue_task

    async def _worker(self):
        """队列worker，串行执行任务"""
        print("🚀 队列worker开始运行")

        while self._is_running:
            try:
                # 从队列获取任务（超时避免无限等待）
                try:
                    queue_task = await asyncio.wait_for(
                        self._queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # 检查任务是否已被取消
                if queue_task.status == TaskStatus.CANCELLED:
                    print(f"⏭️ 任务 {queue_task.task_id} 已被取消，跳过")
                    self._queue.task_done()
                    continue

                # 执行任务
                self._running_task = queue_task
                await self._execute_task(queue_task)
                self._running_task = None

                self._queue.task_done()

                # 任务间隔延迟，避免频繁请求
                await asyncio.sleep(2)

            except asyncio.CancelledError:
                print("⚠️ Worker被取消")
                break
            except Exception as e:
                print(f"❌ Worker处理任务时出错: {e}")
                import traceback
                traceback.print_exc()

    async def _execute_task(self, queue_task: QueueTask):
        """执行单个任务"""
        task_id = queue_task.task_id

        try:
            print(f"▶️ 开始执行任务 {task_id}: {queue_task.repository_url}")

            # 更新任务状态
            queue_task.status = TaskStatus.RUNNING
            queue_task.started_at = datetime.now(timezone.utc)

            # 检查执行器是否已设置
            if not self._executor:
                raise Exception("任务执行器未设置")

            # 执行任务（调用实际的star操作）
            result = await self._executor(
                task_id=task_id,
                user_id=queue_task.user_id,
                repository_url=queue_task.repository_url,
                account_ids=queue_task.account_ids,
                force_execute=queue_task.force_execute
            )

            # 任务完成
            queue_task.status = TaskStatus.COMPLETED
            queue_task.completed_at = datetime.now(timezone.utc)
            queue_task.result = result

            duration = (queue_task.completed_at - queue_task.started_at).total_seconds()
            print(f"✅ 任务 {task_id} 执行完成 (耗时: {duration:.1f}秒)")

        except Exception as e:
            # 任务失败
            queue_task.status = TaskStatus.FAILED
            queue_task.completed_at = datetime.now(timezone.utc)
            queue_task.error = str(e)

            print(f"❌ 任务 {task_id} 执行失败: {e}")
            import traceback
            traceback.print_exc()

    def get_task_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取任务状态"""
        if task_id not in self._tasks:
            return None

        queue_task = self._tasks[task_id]

        return {
            "task_id": queue_task.task_id,
            "status": queue_task.status.value,
            "created_at": queue_task.created_at.isoformat() if queue_task.created_at else None,
            "started_at": queue_task.started_at.isoformat() if queue_task.started_at else None,
            "completed_at": queue_task.completed_at.isoformat() if queue_task.completed_at else None,
            "result": queue_task.result,
            "error": queue_task.error,
            "queue_position": self._get_queue_position(task_id)
        }

    def _get_queue_position(self, task_id: int) -> Optional[int]:
        """获取任务在队列中的位置（0表示正在执行，None表示不在队列中）"""
        if self._running_task and self._running_task.task_id == task_id:
            return 0

        # 获取队列中等待的任务
        queue_items = list(self._queue._queue)
        for i, queue_task in enumerate(queue_items):
            if queue_task.task_id == task_id:
                return i + 1  # +1 因为位置0是正在执行的任务

        return None

    def get_queue_info(self) -> Dict[str, Any]:
        """获取队列信息"""
        return {
            "is_running": self._is_running,
            "queue_size": self._queue.qsize(),
            "total_tasks": len(self._tasks),
            "running_task": {
                "task_id": self._running_task.task_id,
                "repository_url": self._running_task.repository_url,
                "account_count": len(self._running_task.account_ids)
            } if self._running_task else None,
            "pending_tasks": [
                {
                    "task_id": task.task_id,
                    "repository_url": task.repository_url,
                    "account_count": len(task.account_ids)
                }
                for task in self._tasks.values()
                if task.status == TaskStatus.PENDING
            ]
        }

    async def cancel_task(self, task_id: int) -> bool:
        """取消任务"""
        if task_id not in self._tasks:
            return False

        queue_task = self._tasks[task_id]

        # 只能取消等待中的任务
        if queue_task.status == TaskStatus.PENDING:
            queue_task.status = TaskStatus.CANCELLED
            queue_task.completed_at = datetime.now(timezone.utc)
            print(f"✅ 任务 {task_id} 已取消")
            return True

        print(f"⚠️ 任务 {task_id} 无法取消，当前状态: {queue_task.status}")
        return False

    def clear_completed_tasks(self, max_keep: int = 100):
        """清理已完成的任务记录"""
        completed_tasks = [
            task_id for task_id, task in self._tasks.items()
            if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]

        if len(completed_tasks) <= max_keep:
            return

        # 按完成时间排序，保留最新的max_keep个
        completed_tasks.sort(
            key=lambda tid: self._tasks[tid].completed_at or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True
        )

        # 删除旧的任务
        for task_id in completed_tasks[max_keep:]:
            del self._tasks[task_id]

        print(f"🧹 已清理 {len(completed_tasks) - max_keep} 个旧任务记录")


# 全局队列实例
repository_star_queue = RepositoryStarQueue()
