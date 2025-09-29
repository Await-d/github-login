"""
数据库模型和配置
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text, Float, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import os

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/github_manager.db")
#判断DATABASE_URL是否以sqlite://开头，如果不是，则代表是文件路径，需要拼接data目录
if not DATABASE_URL.startswith("sqlite://"):
    DATABASE_URL = "sqlite:///" + DATABASE_URL + "/github_manager.db"

# 创建数据库引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# 创建会话
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基础模型类
Base = declarative_base()


class User(Base):
    """用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now())
    
    # 关联的GitHub账号
    github_accounts = relationship("GitHubAccount", back_populates="owner", cascade="all, delete-orphan")
    # 关联的API网站账号
    api_websites = relationship("ApiWebsite", back_populates="owner", cascade="all, delete-orphan")


class GitHubAccount(Base):
    """GitHub账号模型"""
    __tablename__ = "github_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    username = Column(String, nullable=False)
    encrypted_password = Column(Text, nullable=False)  # 加密存储
    encrypted_totp_secret = Column(Text, nullable=False)  # 加密存储
    created_at = Column(String, nullable=False)  # 日期字符串格式 YYYY-MM-DD
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联用户
    owner = relationship("User", back_populates="github_accounts")


class ApiWebsite(Base):
    """API网站账号模型"""
    __tablename__ = "api_websites"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)  # 网站名称，如"anyrouter.top"
    type = Column(String, nullable=False, default="api网站1")  # 网站类型
    login_url = Column(String, nullable=False)  # 登录URL
    username = Column(String, nullable=False)  # 登录用户名
    encrypted_password = Column(Text, nullable=False)  # 加密的登录密码
    
    # 登录状态和会话信息
    is_logged_in = Column(String, default="false")  # 登录状态: "true"/"false"
    session_data = Column(Text)  # 加密的会话数据（cookies等）
    last_login_time = Column(DateTime)  # 最后登录时间
    
    # 账户信息
    balance = Column(Float, default=0.0)  # 余额
    api_keys = Column(Text)  # 加密的API密钥列表（JSON格式）
    
    # 时间字段
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联用户
    owner = relationship("User", back_populates="api_websites")


class ScheduledTask(Base):
    """定时任务模型"""
    __tablename__ = "scheduled_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 任务基本信息
    name = Column(String, nullable=False)  # 任务名称
    description = Column(Text)  # 任务描述
    task_type = Column(String, nullable=False)  # 任务类型: github_oauth_login
    
    # 定时配置
    cron_expression = Column(String, nullable=False)  # cron表达式
    timezone = Column(String, default="Asia/Shanghai")  # 时区
    
    # 任务参数
    task_params = Column(Text)  # JSON格式的任务参数
    
    # 状态信息
    is_active = Column(Boolean, default=True)  # 是否启用
    last_run_time = Column(DateTime)  # 最后执行时间
    next_run_time = Column(DateTime)  # 下次执行时间
    last_result = Column(Text)  # 最后执行结果
    run_count = Column(Integer, default=0)  # 执行次数
    success_count = Column(Integer, default=0)  # 成功次数
    error_count = Column(Integer, default=0)  # 失败次数
    
    # 时间字段
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联用户
    owner = relationship("User", back_populates="scheduled_tasks")


class TaskExecutionLog(Base):
    """任务执行日志模型"""
    __tablename__ = "task_execution_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("scheduled_tasks.id"), nullable=False)
    
    # 执行信息
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime)
    duration = Column(Float)  # 执行时长(秒)
    status = Column(String, nullable=False)  # success, failed, running
    
    # 结果信息
    result_message = Column(Text)  # 执行结果消息
    error_details = Column(Text)  # 错误详情
    execution_data = Column(Text)  # JSON格式的执行数据
    
    # 关联任务
    task = relationship("ScheduledTask", back_populates="execution_logs")


# 更新User模型关联
User.scheduled_tasks = relationship("ScheduledTask", back_populates="owner", cascade="all, delete-orphan")

# 更新ScheduledTask模型关联  
ScheduledTask.execution_logs = relationship("TaskExecutionLog", back_populates="task", cascade="all, delete-orphan")


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_default_admin():
    """创建默认管理员账号"""
    # 检查是否应该创建默认账号
    create_default = os.getenv("CREATE_DEFAULT_ADMIN", "true").lower() == "true"
    if not create_default:
        return
    
    db = SessionLocal()
    try:
        # 检查是否已有用户
        existing_users = db.query(User).count()
        if existing_users > 0:
            return
        
        # 导入加密工具
        from utils.encryption import hash_password
        
        # 创建默认管理员账号
        default_username = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
        default_password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")
        
        hashed_password = hash_password(default_password)
        admin_user = User(
            username=default_username,
            hashed_password=hashed_password
        )
        
        db.add(admin_user)
        db.commit()
        
        print(f"✅ 创建默认管理员账号: {default_username}")
        print(f"   密码: {default_password}")
        print("   ⚠️  首次登录后请及时修改密码!")
        
    except Exception as e:
        print(f"❌ 创建默认管理员账号失败: {e}")
        db.rollback()
    finally:
        db.close()


def init_db():
    """初始化数据库"""
    global DATABASE_URL, engine, SessionLocal
    
    try:
        # 创建所有表
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建成功")
        
        # 创建默认管理员账号
        create_default_admin()
        
    except Exception as e:
        print(f"❌ 数据库初始化失败: {e}")
        # 创建fallback数据库目录
        os.makedirs("./data", exist_ok=True)
        # 尝试使用data目录下的数据库
        DATABASE_URL = "sqlite:///./data/github_manager.db"
        engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        print("✅ 使用fallback数据库路径创建成功")
        
        # 在fallback情况下也创建默认管理员账号
        create_default_admin()