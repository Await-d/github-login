"""
仓库收藏相关数据模型
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class RepositoryStarTask(Base):
    """GitHub仓库收藏任务模型"""
    __tablename__ = "repository_star_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # 仓库信息
    repository_url = Column(String, nullable=False)  # 完整URL
    owner = Column(String, nullable=False)  # 仓库所有者
    repo_name = Column(String, nullable=False)  # 仓库名称
    description = Column(Text)  # 描述/备注
    
    # 时间字段
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # 关联
    owner_user = relationship("User", back_populates="repository_star_tasks")
    star_records = relationship("RepositoryStarRecord", back_populates="task", cascade="all, delete-orphan")


class RepositoryStarRecord(Base):
    """仓库收藏执行记录模型"""
    __tablename__ = "repository_star_records"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("repository_star_tasks.id"), nullable=False)
    github_account_id = Column(Integer, ForeignKey("github_accounts.id"), nullable=False)
    
    # 执行状态
    status = Column(String, nullable=False)  # success, failed, already_starred, skipped
    error_message = Column(Text)  # 错误信息
    
    # 执行时间
    executed_at = Column(DateTime, default=func.now())
    
    # 关联
    task = relationship("RepositoryStarTask", back_populates="star_records")
    github_account = relationship("GitHubAccount")
    
    # 唯一约束：同一个任务的同一个账号只能有一条记录（避免重复star）
    __table_args__ = (
        UniqueConstraint('task_id', 'github_account_id', name='uq_task_account'),
    )
