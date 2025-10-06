#!/usr/bin/env python3
"""
调试脚本 - 检查定时任务数据库状态和时区处理
"""
import sqlite3
from datetime import datetime, timezone
import sys
import pytz

def debug_scheduled_tasks(db_path='/app/data/github_manager.db'):
    """检查定时任务表的数据"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("=" * 80)
        print("📊 定时任务数据库调试信息")
        print("=" * 80)

        # 获取当前时间
        now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
        now_shanghai = datetime.now(pytz.timezone('Asia/Shanghai'))

        print(f"\n🕐 当前UTC时间: {now_utc}")
        print(f"🕐 当前上海时间: {now_shanghai.strftime('%Y-%m-%d %H:%M:%S')}")

        # 查询所有定时任务
        cursor.execute("""
            SELECT
                id,
                name,
                cron_expression,
                is_active,
                next_run_time,
                timezone,
                last_run_time,
                created_at,
                updated_at
            FROM scheduled_tasks
            ORDER BY id
        """)

        tasks = cursor.fetchall()

        if not tasks:
            print("\n⚠️  数据库中没有任何定时任务")
            return

        print(f"\n📋 共找到 {len(tasks)} 个定时任务:\n")

        for task in tasks:
            task_id, name, cron_expr, is_active, next_run_time, tz, last_run_time, created_at, updated_at = task

            print("-" * 80)
            print(f"ID: {task_id}")
            print(f"名称: {name}")
            print(f"Cron表达式: {cron_expr}")
            print(f"是否激活: {'✅ 是' if is_active else '❌ 否'}")
            print(f"时区: {tz}")
            print(f"下次执行时间(数据库存储): {next_run_time}")
            print(f"上次执行时间: {last_run_time or '未执行'}")
            print(f"创建时间: {created_at}")
            print(f"更新时间: {updated_at}")

            # 解析 next_run_time
            if next_run_time:
                try:
                    # 数据库存储的应该是UTC时间(无时区信息)
                    next_run_dt = datetime.fromisoformat(next_run_time.replace('Z', ''))

                    # 与当前UTC时间比较
                    time_diff = (next_run_dt - now_utc).total_seconds()

                    print(f"\n⏱️  时间分析:")
                    print(f"   数据库时间视为UTC: {next_run_dt}")
                    print(f"   当前UTC时间: {now_utc}")
                    print(f"   时间差: {time_diff:.1f} 秒 ({time_diff/60:.1f} 分钟)")

                    if time_diff < -60:
                        print(f"   ⚠️  任务已过期 {abs(time_diff):.1f} 秒 ({abs(time_diff)/60:.1f} 分钟)")
                    elif -30 <= time_diff <= 60:
                        print(f"   ✅ 任务在执行窗口内 (容忍度±30秒)")
                    else:
                        print(f"   ⏳ 任务将在 {time_diff:.1f} 秒后执行 ({time_diff/60:.1f} 分钟)")

                    # 转换为上海时间显示
                    next_run_dt_utc = next_run_dt.replace(tzinfo=timezone.utc)
                    next_run_shanghai = next_run_dt_utc.astimezone(pytz.timezone('Asia/Shanghai'))
                    print(f"   上海时间表示: {next_run_shanghai.strftime('%Y-%m-%d %H:%M:%S')}")

                    # 使用croniter计算正确的下次执行时间
                    try:
                        import croniter
                        tz_obj = pytz.timezone(tz) if tz else pytz.timezone('Asia/Shanghai')
                        now_tz = datetime.now(tz_obj)
                        cron = croniter.croniter(cron_expr, now_tz)
                        correct_next_run = cron.get_next(datetime)
                        correct_next_run_utc = correct_next_run.astimezone(timezone.utc).replace(tzinfo=None)

                        print(f"\n🔍 Croniter计算结果:")
                        print(f"   当前时区时间: {now_tz.strftime('%Y-%m-%d %H:%M:%S')} ({tz})")
                        print(f"   正确的下次执行(时区): {correct_next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"   正确的下次执行(UTC): {correct_next_run_utc}")
                        print(f"   数据库中的值: {next_run_dt}")

                        if correct_next_run_utc != next_run_dt:
                            print(f"   ⚠️  数据库值不正确!差异: {(correct_next_run_utc - next_run_dt).total_seconds():.1f} 秒")
                        else:
                            print(f"   ✅ 数据库值正确")
                    except Exception as e:
                        print(f"   ❌ Croniter计算失败: {e}")

                except Exception as e:
                    print(f"❌ 解析时间失败: {e}")
                    import traceback
                    traceback.print_exc()
            else:
                print("⚠️  next_run_time 为空")

        print("\n" + "=" * 80)
        print("✅ 调试信息收集完成")
        print("=" * 80)

    except Exception as e:
        print(f"\n❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else '/app/data/github_manager.db'
    debug_scheduled_tasks(db_path)
