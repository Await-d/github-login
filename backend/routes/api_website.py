"""
API网站管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import json

from models.database import get_db, User, ApiWebsite
from models.schemas import (
    ApiWebsiteCreate, ApiWebsiteUpdate, ApiWebsiteResponse, ApiWebsiteSafe, ApiWebsite as ApiWebsiteSchema,
    LoginSimulationRequest, LoginSimulationResponse, AccountInfoResponse
)
from utils.encryption import encrypt_data, decrypt_data
from utils.auth import get_current_user
from utils.website_simulator import website_simulator

router = APIRouter()


@router.get("/websites", response_model=ApiWebsiteResponse)
async def get_api_websites(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取当前用户的所有API网站账号列表"""
    try:
        websites = db.query(ApiWebsite).filter(ApiWebsite.user_id == current_user.id).all()
        
        # 转换为安全格式（不包含密码等敏感信息）
        safe_websites = []
        for website in websites:
            safe_website = ApiWebsiteSafe(
                id=website.id,
                user_id=website.user_id,
                name=website.name,
                type=website.type,
                login_url=website.login_url,
                username=website.username,
                is_logged_in=website.is_logged_in,
                last_login_time=website.last_login_time,
                balance=website.balance,
                created_at=website.created_at,
                updated_at=website.updated_at
            )
            safe_websites.append(safe_website)
        
        return ApiWebsiteResponse(
            success=True,
            message="获取API网站列表成功",
            websites=safe_websites
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取API网站列表失败: {str(e)}"
        )


@router.get("/websites/{website_id}", response_model=ApiWebsiteResponse)
async def get_api_website(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定API网站的详细信息（包含密码）"""
    website = db.query(ApiWebsite).filter(
        ApiWebsite.id == website_id,
        ApiWebsite.user_id == current_user.id
    ).first()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API网站未找到"
        )
    
    try:
        # 解密敏感信息
        decrypted_password = decrypt_data(website.encrypted_password)
        decrypted_api_keys = None
        
        if website.api_keys:
            try:
                decrypted_api_keys = decrypt_data(website.api_keys)
            except:
                decrypted_api_keys = website.api_keys  # 如果解密失败，返回原始数据
        
        website_detail = ApiWebsiteSchema(
            id=website.id,
            user_id=website.user_id,
            name=website.name,
            type=website.type,
            login_url=website.login_url,
            username=website.username,
            password=decrypted_password,
            is_logged_in=website.is_logged_in,
            last_login_time=website.last_login_time,
            balance=website.balance,
            api_keys=decrypted_api_keys,
            created_at=website.created_at,
            updated_at=website.updated_at
        )
        
        return ApiWebsiteResponse(
            success=True,
            message="获取API网站详情成功",
            website=website_detail
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取API网站详情失败: {str(e)}"
        )


@router.post("/websites", response_model=ApiWebsiteResponse)
async def create_api_website(
    website_data: ApiWebsiteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建新的API网站账号"""
    try:
        # 检查是否已存在相同的网站账号
        existing_website = db.query(ApiWebsite).filter(
            ApiWebsite.user_id == current_user.id,
            ApiWebsite.name == website_data.name,
            ApiWebsite.username == website_data.username
        ).first()
        
        if existing_website:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="该网站账号已存在"
            )
        
        # 加密敏感信息
        encrypted_password = encrypt_data(website_data.password)
        
        # 创建新的API网站记录
        new_website = ApiWebsite(
            user_id=current_user.id,
            name=website_data.name,
            type=website_data.type,
            login_url=website_data.login_url,
            username=website_data.username,
            encrypted_password=encrypted_password,
            is_logged_in="false",
            balance=0.0
        )
        
        db.add(new_website)
        db.commit()
        db.refresh(new_website)
        
        # 返回安全格式的信息
        safe_website = ApiWebsiteSafe(
            id=new_website.id,
            user_id=new_website.user_id,
            name=new_website.name,
            type=new_website.type,
            login_url=new_website.login_url,
            username=new_website.username,
            is_logged_in=new_website.is_logged_in,
            last_login_time=new_website.last_login_time,
            balance=new_website.balance,
            created_at=new_website.created_at,
            updated_at=new_website.updated_at
        )
        
        return ApiWebsiteResponse(
            success=True,
            message="API网站账号创建成功",
            websites=[safe_website]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建API网站账号失败: {str(e)}"
        )


@router.put("/websites/{website_id}", response_model=ApiWebsiteResponse)
async def update_api_website(
    website_id: int,
    website_data: ApiWebsiteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新API网站账号信息"""
    website = db.query(ApiWebsite).filter(
        ApiWebsite.id == website_id,
        ApiWebsite.user_id == current_user.id
    ).first()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API网站未找到"
        )
    
    try:
        # 更新字段
        if website_data.name is not None:
            website.name = website_data.name
        if website_data.type is not None:
            website.type = website_data.type
        if website_data.login_url is not None:
            website.login_url = website_data.login_url
        if website_data.username is not None:
            website.username = website_data.username
        if website_data.password is not None:
            website.encrypted_password = encrypt_data(website_data.password)
            # 密码更新后，重置登录状态
            website.is_logged_in = "false"
            website.session_data = None
        
        db.commit()
        db.refresh(website)
        
        # 返回安全格式的信息
        safe_website = ApiWebsiteSafe(
            id=website.id,
            user_id=website.user_id,
            name=website.name,
            type=website.type,
            login_url=website.login_url,
            username=website.username,
            is_logged_in=website.is_logged_in,
            last_login_time=website.last_login_time,
            balance=website.balance,
            created_at=website.created_at,
            updated_at=website.updated_at
        )
        
        return ApiWebsiteResponse(
            success=True,
            message="API网站账号更新成功",
            websites=[safe_website]
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新API网站账号失败: {str(e)}"
        )


@router.delete("/websites/{website_id}")
async def delete_api_website(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除API网站账号"""
    website = db.query(ApiWebsite).filter(
        ApiWebsite.id == website_id,
        ApiWebsite.user_id == current_user.id
    ).first()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API网站未找到"
        )
    
    try:
        db.delete(website)
        db.commit()
        
        return {
            "success": True,
            "message": "API网站账号删除成功"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除API网站账号失败: {str(e)}"
        )


@router.post("/websites/{website_id}/login", response_model=LoginSimulationResponse)
async def simulate_login(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """模拟登录API网站"""
    website = db.query(ApiWebsite).filter(
        ApiWebsite.id == website_id,
        ApiWebsite.user_id == current_user.id
    ).first()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API网站未找到"
        )
    
    try:
        # 解密密码
        decrypted_password = decrypt_data(website.encrypted_password)
        
        # 执行登录模拟
        success, message, session_data = website_simulator.simulate_login(
            website.login_url,
            website.username,
            decrypted_password
        )
        
        if success:
            # 保存会话数据
            encrypted_session_data = encrypt_data(json.dumps(session_data))
            website.session_data = encrypted_session_data
            website.is_logged_in = "true"
            website.last_login_time = datetime.now()
            
            # 获取账户信息
            account_success, account_info = website_simulator.get_account_info(
                session_data, website.login_url
            )
            
            if account_success and 'balance' in account_info:
                website.balance = account_info['balance']
                
                # 保存API密钥信息
                if 'api_keys' in account_info:
                    encrypted_api_keys = encrypt_data(json.dumps(account_info['api_keys']))
                    website.api_keys = encrypted_api_keys
            
            db.commit()
            
            return LoginSimulationResponse(
                success=True,
                message=message,
                is_logged_in=True,
                balance=website.balance,
                session_info="会话已保存"
            )
        else:
            website.is_logged_in = "false"
            db.commit()
            
            return LoginSimulationResponse(
                success=False,
                message=message,
                is_logged_in=False,
                balance=None,
                session_info=None
            )
            
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录模拟失败: {str(e)}"
        )


@router.get("/websites/{website_id}/account-info", response_model=AccountInfoResponse)
async def get_account_info(
    website_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取API网站的账户信息（余额、API密钥等）"""
    website = db.query(ApiWebsite).filter(
        ApiWebsite.id == website_id,
        ApiWebsite.user_id == current_user.id
    ).first()
    
    if not website:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API网站未找到"
        )
    
    try:
        api_keys = []
        
        # 解密API密钥信息
        if website.api_keys:
            try:
                decrypted_api_keys = decrypt_data(website.api_keys)
                api_keys = json.loads(decrypted_api_keys)
            except:
                api_keys = []
        
        # 如果有会话数据，尝试获取最新信息
        if website.session_data and website.is_logged_in == "true":
            try:
                decrypted_session = decrypt_data(website.session_data)
                session_data = json.loads(decrypted_session)
                
                # 获取最新账户信息
                success, account_info = website_simulator.get_account_info(
                    session_data, website.login_url
                )
                
                if success and 'balance' in account_info:
                    # 更新余额
                    website.balance = account_info['balance']
                    
                    # 更新API密钥
                    if 'api_keys' in account_info:
                        api_keys = account_info['api_keys']
                        encrypted_api_keys = encrypt_data(json.dumps(api_keys))
                        website.api_keys = encrypted_api_keys
                    
                    db.commit()
                    
            except Exception as e:
                print(f"获取最新账户信息失败: {e}")
        
        return AccountInfoResponse(
            success=True,
            message="获取账户信息成功",
            balance=website.balance,
            api_keys=api_keys,
            last_updated=website.updated_at
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取账户信息失败: {str(e)}"
        )