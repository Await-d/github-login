#!/usr/bin/env python3
"""
检查任务执行记录
"""
import sqlite3
import sys

def check_execution_records(db_path='/app/data/github_manager.db'):
    """检查任务执行记录"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print("=" * 80)
        print("📊 任务执行记录检查")
        print("=" * 80)

        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%execution%' OR name LIKE '%log%'")
        tables = cursor.fetchall()
        print(f"\n📋 执行记录相关表: {[t[0] for t in tables]}")

        if not tables:
            print("\n⚠️  未找到执行记录表")
            return

        # 检查每个表的结构
        for table_name in [t[0] for t in tables]:
            print(f"\n{'='*80}")
            print(f"表: {table_name}")
            print(f"{'='*80}")

            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            print("\n列结构:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")

            # 查询记录
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 10")
            records = cursor.fetchall()

            if records:
                print(f"\n最近10条记录:")
                col_names = [c[1] for c in columns]
                for record in records:
                    print(f"\n  记录 ID={record[0]}:")
                    for i, col_name in enumerate(col_names):
                        print(f"    {col_name}: {record[i]}")
            else:
                print("\n⚠️  表中没有记录")

    except Exception as e:
        print(f"\n❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == '__main__':
    db_path = sys.argv[1] if len(sys.argv) > 1 else '/app/data/github_manager.db'
    check_execution_records(db_path)
