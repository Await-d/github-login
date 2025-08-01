"""
数据模型和Pydantic schemas
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# 用户相关模型
class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=20, description="用户名")


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, description="密码")


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=20, description="新用户名")


class PasswordChange(BaseModel):
    current_password: str = Field(..., description="当前密码")
    new_password: str = Field(..., min_length=6, description="新密码")


class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    success: bool
    message: str
    user: Optional[User] = None


# GitHub账号相关模型
class GitHubAccountBase(BaseModel):
    username: str = Field(..., description="GitHub用户名")
    password: str = Field(..., description="GitHub密码")
    totp_secret: str = Field(..., description="TOTP密钥")
    created_at: str = Field(..., description="创建日期 (YYYY-MM-DD)")


class GitHubAccountCreate(GitHubAccountBase):
    pass


class GitHubAccountUpdate(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
    totp_secret: Optional[str] = None
    created_at: Optional[str] = None


class GitHubAccount(GitHubAccountBase):
    id: int
    user_id: int
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GitHubAccountSafe(BaseModel):
    """安全的GitHub账号信息（隐藏敏感字段）"""
    id: int
    user_id: int
    username: str
    password: Optional[str] = None  # 可选，用于查看详情时
    totp_secret: Optional[str] = None  # 可选，用于查看详情时
    created_at: str
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GitHubAccountResponse(BaseModel):
    success: bool
    message: str
    account: Optional[GitHubAccountSafe] = None
    accounts: Optional[List[GitHubAccountSafe]] = None


# TOTP相关模型
class TOTPToken(BaseModel):
    token: str
    time_remaining: int
    formatted_token: str


class TOTPResponse(BaseModel):
    success: bool
    token: Optional[TOTPToken] = None
    message: Optional[str] = None


class TOTPBatchItem(BaseModel):
    id: int
    username: str
    token: str
    time_remaining: int


class TOTPBatchResponse(BaseModel):
    success: bool
    accounts: List[TOTPBatchItem]


# 通用响应模型
class BaseResponse(BaseModel):
    success: bool
    message: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    user: Optional[User] = None
    access_token: Optional[str] = None
    token_type: str = "bearer"


# 批量导入相关模型
class BatchImportItem(BaseModel):
    username: str = Field(..., description="GitHub用户名")
    password: str = Field(..., description="GitHub密码")
    totp_secret: str = Field(..., description="TOTP密钥")
    created_at: str = Field(..., description="创建日期 (YYYY-MM-DD)")


class BatchImportRequest(BaseModel):
    accounts: List[BatchImportItem] = Field(..., description="待导入的账号列表")


class BatchImportResult(BaseModel):
    success_count: int = Field(..., description="成功导入的账号数量")
    error_count: int = Field(..., description="导入失败的账号数量")
    errors: List[str] = Field(default=[], description="错误信息列表")


class BatchImportResponse(BaseModel):
    success: bool
    message: str
    result: Optional[BatchImportResult] = None