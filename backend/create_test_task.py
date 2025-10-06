#!/usr/bin/env python3
"""
创建一个1分钟后执行的测试任务
"""
import sys
sys.path.insert(0, '/app/backend')

from datetime import datetime, timezone, timedelta
from models.database import get_db, ScheduledTask
import json

def create_test_task():
    """创建测试任务"""
    db = next(get_db())

    try:
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        next_run = now_utc + timedelta(minutes=1)

        print(f"当前UTC时间: {now_utc}")
        print(f"计划执行时间: {next_run}")

        # 创建测试任务
        task = ScheduledTask(
            user_id=1,
            name="自动测试任务",
            description="用于测试调度器自动执行功能",
            task_type="github_oauth_login",
            cron_expression="* * * * *",  # 每分钟(虽然我们直接设置next_run_time)
            timezone="Asia/Shanghai",
            task_params=json.dumps({
                "github_account_ids": [7, 8],
                "target_website": "https://anyrouter.top",
                "retry_count": 1
            }),
            is_active=True,
            next_run_time=next_run
        )

        db.add(task)
        db.commit()
        db.refresh(task)

        print(f"\n✅ 测试任务创建成功!")
        print(f"   ID: {task.id}")
        print(f"   名称: {task.name}")
        print(f"   下次执行时间: {task.next_run_time}")
        print(f"\n⏰ 请等待约1分钟,任务应该会自动执行...")

    except Exception as e:
        print(f"❌ 创建任务失败: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == '__main__':
    create_test_task()
