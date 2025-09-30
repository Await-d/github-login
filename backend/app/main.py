"""
GitHub账号管理系统 - FastAPI后端
Version: 1.0.5
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

from routes import auth, github, api_website, scheduled_tasks
from models.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动和关闭时的生命周期管理"""
    # 启动时初始化数据库
    print("🚀 初始化数据库...")
    init_db()
    print("✅ 数据库初始化完成")
    
    yield
    
    # 关闭时的清理工作
    print("🛑 应用关闭")


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
app.include_router(api_website.router, prefix="/api/api-website", tags=["API网站管理"])
app.include_router(scheduled_tasks.router, prefix="/api/scheduled-tasks", tags=["定时任务管理"])

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
        reload=True,
        log_level="info"
    )