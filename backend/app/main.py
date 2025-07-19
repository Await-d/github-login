"""
GitHub账号管理系统 - FastAPI后端
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import os

import sys
import os

# 将backend目录添加到Python路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)

from routes import auth, github
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
frontend_build = os.path.join(os.path.dirname(backend_dir), "frontend", "build")
if os.path.exists(frontend_build):
    app.mount("/", StaticFiles(directory=frontend_build, html=True), name="frontend")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )