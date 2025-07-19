"""
数据库模型和配置
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from datetime import datetime
import os

# 数据库配置
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./github_manager.db")

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