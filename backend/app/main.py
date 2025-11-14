"""
GitHub账号管理系统 - FastAPI后端
Version: 1.0.6
支持定时任务和浏览器自动化
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn
import os

import sys
import os

# 将backend目录添加到Python路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from routes import auth, github, api_website, scheduled_tasks, repository_star, github_groups
from models.database import init_db, get_db
from utils.task_scheduler import task_scheduler
from utils.task_executor import execute_task
from utils.db_migration import check_and_migrate_database
from utils.repository_star_queue import repository_star_queue
import asyncio
from datetime import datetime


# 全局变量用于控制后台任务
background_scheduler_task = None
scheduler_running = False


async def task_scheduler_loop():
    """后台任务调度器循环"""
    global scheduler_running
    scheduler_running = True

    print("⏰ 定时任务调度器已启动")

    while scheduler_running:
        try:
            print(f"🔍 [{datetime.now()}] 开始检查待执行任务...")

            # 获取数据库会话
            db = next(get_db())

            try:
                # 获取待执行的任务
                print(f"🔍 正在查询待执行任务...")
                pending_tasks = task_scheduler.get_pending_tasks(db, tolerance_seconds=10)

                print(f"🔍 查询完成,找到 {len(pending_tasks)} 个待执行任务")

                if pending_tasks:
                    print(f"📋 发现 {len(pending_tasks)} 个待执行任务")

                    # 执行每个待执行的任务
                    for task in pending_tasks:
                        try:
                            print(f"🚀 执行任务: {task.name} (ID: {task.id})")
                            success, result = await execute_task(task, db)

                            if success:
                                print(f"✅ 任务 {task.name} 执行成功: {result}")
                            else:
                                print(f"❌ 任务 {task.name} 执行失败: {result}")
                        except Exception as e:
                            print(f"❌ 执行任务 {task.name} 时发生异常: {e}")
                            import traceback
                            traceback.print_exc()
                else:
                    print(f"💤 当前没有待执行任务")

            finally:
                db.close()

            # 每30秒检查一次
            print(f"⏰ 等待10秒后进行下次检查...")
            await asyncio.sleep(10)

        except Exception as e:
            print(f"⚠️ 任务调度器循环异常: {e}")
            import traceback
            traceback.print_exc()
            # 发生异常后等待一段时间再继续
            await asyncio.sleep(60)

    print("⏰ 定时任务调度器已停止")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的生命周期管理"""
    global background_scheduler_task, scheduler_running

    # 打印配置信息和安全警告
    from utils.config import config
    config.print_config()
    
    # 启动时初始化数据库
    print("🚀 初始化数据库...")
    init_db()
    print("✅ 数据库表创建成功")

    # 检查并迁移数据库（自动修复缺失字段）
    print("🔧 检查数据库结构...")
    success, migrations = check_and_migrate_database()
    if success and migrations:
        print(f"✅ 数据库迁移完成，应用了 {len(migrations)} 个更新")
    elif success:
        print("✅ 数据库结构完整")
    else:
        print("⚠️  数据库迁移出现警告，但系统将继续运行")

    print("✅ 数据库初始化完成")

    # 启动后台任务调度器
    print("🚀 启动后台任务调度器...")
    background_scheduler_task = asyncio.create_task(task_scheduler_loop())
    print("✅ 后台任务调度器已启动")

    # 启动仓库收藏任务队列
    print("🚀 启动仓库收藏任务队列...")
    # 从repository_star路由导入执行器函数
    from routes.repository_star import _queue_executor
    repository_star_queue.set_executor(_queue_executor)
    await repository_star_queue.start()
    print("✅ 仓库收藏任务队列已启动")

    yield

    # 关闭时的清理工作
    print("🛑 正在关闭应用...")

    # 停止仓库收藏任务队列
    print("🛑 停止仓库收藏任务队列...")
    await repository_star_queue.stop()
    print("✅ 仓库收藏任务队列已停止")

    # 停止后台任务调度器
    print("🛑 停止后台任务调度器...")
    scheduler_running = False

    if background_scheduler_task:
        background_scheduler_task.cancel()
        try:
            await background_scheduler_task
        except asyncio.CancelledError:
            pass

    print("✅ 后台任务调度器已停止")
    print("🛑 应用已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="GitHub账号管理系统",
    description="安全的GitHub账号管理和TOTP验证码生成系统",
    version="2.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # React开发服务器
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(github.router, prefix="/api/github", tags=["GitHub管理"])
app.include_router(github_groups.router, prefix="/api/github", tags=["GitHub分组管理"])
app.include_router(api_website.router, prefix="/api/api-website", tags=["API网站管理"])
app.include_router(scheduled_tasks.router, prefix="/api/scheduled-tasks", tags=["定时任务管理"])
app.include_router(repository_star.router, prefix="/api/repository-star", tags=["仓库收藏管理"])

# 健康检查
@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    return {
        "success": True,
        "message": "GitHub Manager API is running",
        "version": "2.0.0",
        "tech_stack": "Python + FastAPI + React + Ant Design"
    }

# 挂载静态文件 (React构建产物)
# 在Docker容器中，前端构建文件位于 /app/frontend/build
frontend_paths = [
    "/app/frontend/build",  # Docker容器路径
    os.path.join(os.path.dirname(backend_dir), "frontend", "build"),  # 本地开发路径
]

frontend_dir = None
for frontend_build in frontend_paths:
    if os.path.exists(frontend_build):
        print(f"✅ 找到前端构建文件: {frontend_build}")
        frontend_dir = frontend_build
        break
else:
    print("⚠️  未找到前端构建文件，将只提供API服务")

# 如果找到前端文件，添加静态文件服务
if frontend_dir:
    # 提供静态资源
    app.mount("/static", StaticFiles(directory=os.path.join(frontend_dir, "static")), name="static")
    
    # 提供前端主页
    @app.get("/")
    async def serve_frontend():
        """提供前端主页"""
        return FileResponse(os.path.join(frontend_dir, "index.html"))
    
    # 捕获所有前端路由，返回index.html（支持React Router）
    @app.get("/{path:path}")
    async def serve_frontend_routes(path: str):
        """处理前端路由，返回index.html"""
        # 如果请求的是API路径，不处理
        if path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        
        # 检查是否存在对应的静态文件
        file_path = os.path.join(frontend_dir, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            # 根据文件类型设置正确的Content-Type
            if path.endswith('.js'):
                return FileResponse(file_path, media_type='application/javascript')
            elif path.endswith('.css'):
                return FileResponse(file_path, media_type='text/css')
            elif path.endswith('.html'):
                return FileResponse(file_path, media_type='text/html')
            return FileResponse(file_path)
        
        # 否则返回index.html，让React Router处理
        return FileResponse(os.path.join(frontend_dir, "index.html"))

if __name__ == "__main__":
    port = int(os.getenv("PORT", 3000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # 生产环境禁用reload,避免后台任务被取消
        log_level="info"
    )
