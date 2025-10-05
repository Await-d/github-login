"""
数据库迁移工具 - 自动检测和修复缺失的字段
"""
import sqlite3
from typing import List, Tuple


def check_and_migrate_database(db_path: str = '/app/data/github_manager.db'):
    """
    检查并迁移数据库，确保所有必要的字段都存在

    Args:
        db_path: 数据库文件路径
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    migrations_applied = []

    try:
        # ===== 检查 github_accounts 表 =====
        print("🔍 检查 github_accounts 表...")
        cursor.execute("PRAGMA table_info(github_accounts)")
        columns = [column[1] for column in cursor.fetchall()]

        # 检查 group_id 字段
        if 'group_id' not in columns:
            print("  ⚠️  缺少 group_id 字段，正在添加...")
            cursor.execute("ALTER TABLE github_accounts ADD COLUMN group_id INTEGER")
            conn.commit()
            migrations_applied.append("添加 github_accounts.group_id 字段")
            print("  ✅ 成功添加 group_id 字段")
        else:
            print("  ✅ group_id 字段已存在")

        # ===== 检查 github_account_groups 表 =====
        print("🔍 检查 github_account_groups 表...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='github_account_groups'")

        if not cursor.fetchone():
            print("  ⚠️  缺少 github_account_groups 表，正在创建...")
            cursor.execute("""
                CREATE TABLE github_account_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name VARCHAR NOT NULL,
                    description TEXT,
                    color VARCHAR,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            """)
            conn.commit()
            migrations_applied.append("创建 github_account_groups 表")
            print("  ✅ 成功创建 github_account_groups 表")
        else:
            print("  ✅ github_account_groups 表已存在")

        # ===== 检查 repository_star_tasks 表 =====
        print("🔍 检查 repository_star_tasks 表...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='repository_star_tasks'")

        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(repository_star_tasks)")
            repo_columns = [column[1] for column in cursor.fetchall()]

            # 检查必要字段
            required_fields = ['owner', 'repo_name']
            for field in required_fields:
                if field not in repo_columns:
                    print(f"  ⚠️  缺少 {field} 字段，正在添加...")
                    cursor.execute(f"ALTER TABLE repository_star_tasks ADD COLUMN {field} VARCHAR")
                    conn.commit()
                    migrations_applied.append(f"添加 repository_star_tasks.{field} 字段")
                    print(f"  ✅ 成功添加 {field} 字段")
                else:
                    print(f"  ✅ {field} 字段已存在")
        else:
            print("  ℹ️  repository_star_tasks 表不存在（可能是新安装）")

        # ===== 检查 repository_star_records 表 =====
        print("🔍 检查 repository_star_records 表...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='repository_star_records'")

        if cursor.fetchone():
            print("  ✅ repository_star_records 表已存在")
        else:
            print("  ℹ️  repository_star_records 表不存在（可能是新安装）")

        # 打印迁移摘要
        if migrations_applied:
            print("\n" + "="*60)
            print("📊 数据库迁移摘要:")
            for i, migration in enumerate(migrations_applied, 1):
                print(f"  {i}. {migration}")
            print("="*60 + "\n")
            print(f"✅ 成功应用 {len(migrations_applied)} 个数据库迁移")
        else:
            print("\n✅ 数据库结构完整，无需迁移")

        return True, migrations_applied

    except Exception as e:
        print(f"\n❌ 数据库迁移失败: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
        return False, []

    finally:
        conn.close()


def get_database_info(db_path: str = '/app/data/github_manager.db') -> dict:
    """
    获取数据库信息

    Returns:
        包含所有表和字段信息的字典
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 获取所有表
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]

        db_info = {}
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            db_info[table] = [
                {
                    'name': col[1],
                    'type': col[2],
                    'notnull': bool(col[3]),
                    'default': col[4],
                    'pk': bool(col[5])
                }
                for col in columns
            ]

        return db_info

    finally:
        conn.close()


if __name__ == '__main__':
    # 测试迁移功能
    success, migrations = check_and_migrate_database()
    if success:
        print("\n✅ 数据库迁移测试成功")

        # 显示数据库信息
        print("\n📋 数据库结构信息:")
        db_info = get_database_info()
        for table, columns in db_info.items():
            print(f"\n  表: {table}")
            for col in columns:
                print(f"    - {col['name']} ({col['type']})")
    else:
        print("\n❌ 数据库迁移测试失败")
