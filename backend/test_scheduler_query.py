#!/usr/bin/env python3
"""
测试调度器查询逻辑
"""
import sys
sys.path.insert(0, '/app/backend')

from datetime import datetime, timedelta
from models.database import get_db, ScheduledTask

def test_scheduler_query():
    """测试调度器查询"""
    db = next(get_db())

    try:
        now = datetime.utcnow()
        tolerance_seconds = 30

        print(f"当前UTC时间: {now}")
        print(f"容忍度: {tolerance_seconds}秒")
        print(f"查询条件: next_run_time <= {now + timedelta(seconds=tolerance_seconds)}")
        print()

        # 查询所有任务
        all_tasks = db.query(ScheduledTask).all()
        print(f"数据库中共有 {len(all_tasks)} 个任务:")
        for task in all_tasks:
            print(f"\n任务 ID={task.id}:")
            print(f"  名称: {task.name}")
            print(f"  is_active: {task.is_active}")
            print(f"  next_run_time: {task.next_run_time}")
            print(f"  next_run_time类型: {type(task.next_run_time)}")

            if task.next_run_time:
                # 判断是否在查询范围内
                if isinstance(task.next_run_time, str):
                    next_run_dt = datetime.fromisoformat(task.next_run_time.replace('Z', ''))
                else:
                    next_run_dt = task.next_run_time

                time_diff = (next_run_dt - now).total_seconds()
                print(f"  时间差: {time_diff:.1f}秒")
                print(f"  是否 <= now+tolerance: {next_run_dt <= now + timedelta(seconds=tolerance_seconds)}")

        print("\n" + "="*80)

        # 执行实际查询
        pending_tasks = db.query(ScheduledTask).filter(
            ScheduledTask.is_active == True,
            ScheduledTask.next_run_time <= now + timedelta(seconds=tolerance_seconds)
        ).all()

        print(f"查询到 {len(pending_tasks)} 个待执行任务")

    finally:
        db.close()

if __name__ == '__main__':
    test_scheduler_query()
