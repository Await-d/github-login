"""
GitHub账号管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from models.database import get_db, User, GitHubAccount
from models.schemas import (
    GitHubAccountCreate, 
    GitHubAccountUpdate, 
    GitHubAccountResponse,
    GitHubAccountSafe,
    TOTPResponse,
    TOTPToken,
    TOTPBatchResponse,
    TOTPBatchItem,
    BatchImportRequest,
    BatchImportResponse,
    BatchImportResult,
    GitHubOAuthLoginResponse
)
from utils.auth import get_current_user
from utils.encryption import encrypt_data, decrypt_data
from utils.totp import generate_totp_token, validate_totp_secret

router = APIRouter()


@router.post("/accounts", response_model=GitHubAccountResponse)
async def create_github_account(
    account_data: GitHubAccountCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建GitHub账号"""
    
    # 验证TOTP密钥格式
    if not validate_totp_secret(account_data.totp_secret):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="TOTP密钥格式不正确"
        )
    
    # 检查是否已存在相同用户名的账号
    existing_account = db.query(GitHubAccount).filter(
        GitHubAccount.user_id == current_user.id,
        GitHubAccount.username == account_data.username
    ).first()
    
    if existing_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="该GitHub用户名已存在"
        )
    
    # 加密敏感数据
    encrypted_password = encrypt_data(account_data.password)
    encrypted_totp_secret = encrypt_data(account_data.totp_secret)
    
    # 创建新账号
    new_account = GitHubAccount(
        user_id=current_user.id,
        username=account_data.username,
        encrypted_password=encrypted_password,
        encrypted_totp_secret=encrypted_totp_secret,
        created_at=account_data.created_at
    )
    
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    
    # 返回安全的账号信息
    safe_account = GitHubAccountSafe(
        id=new_account.id,
        user_id=new_account.user_id,
        username=new_account.username,
        created_at=new_account.created_at,
        updated_at=new_account.updated_at
    )
    
    return GitHubAccountResponse(
        success=True,
        message="GitHub账号添加成功",
        account=safe_account
    )


@router.get("/accounts", response_model=GitHubAccountResponse)
async def get_github_accounts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有GitHub账号"""
    
    accounts = db.query(GitHubAccount).filter(
        GitHubAccount.user_id == current_user.id
    ).all()
    
    safe_accounts = [
        GitHubAccountSafe(
            id=account.id,
            user_id=account.user_id,
            username=account.username,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
        for account in accounts
    ]
    
    return GitHubAccountResponse(
        success=True,
        message="获取账号列表成功",
        accounts=safe_accounts
    )


@router.get("/accounts/{account_id}", response_model=GitHubAccountResponse)
async def get_github_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定GitHub账号详情（包含解密的密码和密钥）"""
    
    account = db.query(GitHubAccount).filter(
        GitHubAccount.id == account_id,
        GitHubAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账号不存在"
        )
    
    # 解密敏感数据
    try:
        decrypted_password = decrypt_data(account.encrypted_password)
        decrypted_totp_secret = decrypt_data(account.encrypted_totp_secret)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="解密数据失败"
        )
    
    # 返回包含真实密码和密钥的账号信息
    full_account = GitHubAccountSafe(
        id=account.id,
        user_id=account.user_id,
        username=account.username,
        password=decrypted_password,  # 真实密码
        totp_secret=decrypted_totp_secret,  # 真实密钥
        created_at=account.created_at,
        updated_at=account.updated_at
    )
    
    return GitHubAccountResponse(
        success=True,
        message="获取账号详情成功",
        account=full_account
    )


@router.put("/accounts/{account_id}", response_model=GitHubAccountResponse)
async def update_github_account(
    account_id: int,
    account_data: GitHubAccountUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新GitHub账号"""
    
    account = db.query(GitHubAccount).filter(
        GitHubAccount.id == account_id,
        GitHubAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账号不存在"
        )
    
    # 更新账号信息
    if account_data.username is not None:
        account.username = account_data.username
    
    if account_data.password is not None:
        account.encrypted_password = encrypt_data(account_data.password)
    
    if account_data.totp_secret is not None:
        if not validate_totp_secret(account_data.totp_secret):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="TOTP密钥格式不正确"
            )
        account.encrypted_totp_secret = encrypt_data(account_data.totp_secret)
    
    if account_data.created_at is not None:
        account.created_at = account_data.created_at
    
    db.commit()
    db.refresh(account)
    
    safe_account = GitHubAccountSafe(
        id=account.id,
        user_id=account.user_id,
        username=account.username,
        created_at=account.created_at,
        updated_at=account.updated_at
    )
    
    return GitHubAccountResponse(
        success=True,
        message="账号更新成功",
        account=safe_account
    )


@router.delete("/accounts/{account_id}")
async def delete_github_account(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除GitHub账号"""
    
    account = db.query(GitHubAccount).filter(
        GitHubAccount.id == account_id,
        GitHubAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账号不存在"
        )
    
    db.delete(account)
    db.commit()
    
    return {
        "success": True,
        "message": "账号删除成功"
    }


@router.get("/accounts/{account_id}/totp", response_model=TOTPResponse)
async def get_totp_token(
    account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定账号的TOTP验证码"""
    
    account = db.query(GitHubAccount).filter(
        GitHubAccount.id == account_id,
        GitHubAccount.user_id == current_user.id
    ).first()
    
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="账号不存在"
        )
    
    try:
        # 解密TOTP密钥
        totp_secret = decrypt_data(account.encrypted_totp_secret)
        
        # 生成TOTP令牌
        token_info = generate_totp_token(totp_secret)
        
        totp_token = TOTPToken(**token_info)
        
        return TOTPResponse(
            success=True,
            token=totp_token
        )
    except Exception as e:
        return TOTPResponse(
            success=False,
            message=f"生成TOTP令牌失败: {str(e)}"
        )


@router.get("/totp/batch", response_model=TOTPBatchResponse)
async def get_all_totp_tokens(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量获取所有账号的TOTP验证码"""
    
    accounts = db.query(GitHubAccount).filter(
        GitHubAccount.user_id == current_user.id
    ).all()
    
    batch_items = []
    
    for account in accounts:
        try:
            # 解密TOTP密钥
            totp_secret = decrypt_data(account.encrypted_totp_secret)
            
            # 生成TOTP令牌
            token_info = generate_totp_token(totp_secret)
            
            batch_item = TOTPBatchItem(
                id=account.id,
                username=account.username,
                token=token_info["token"],
                time_remaining=token_info["time_remaining"]
            )
            
            batch_items.append(batch_item)
        except Exception:
            # 如果某个账号的TOTP生成失败，跳过
            continue
    
    return TOTPBatchResponse(
        success=True,
        accounts=batch_items
    )


@router.post("/accounts/batch-import", response_model=BatchImportResponse)
async def batch_import_github_accounts(
    import_data: BatchImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量导入GitHub账号"""
    
    success_count = 0
    error_count = 0
    errors = []
    
    for account_data in import_data.accounts:
        try:
            # 验证TOTP密钥格式
            if not validate_totp_secret(account_data.totp_secret):
                error_count += 1
                errors.append(f"账号 {account_data.username}: TOTP密钥格式不正确")
                continue
            
            # 检查是否已存在相同用户名的账号
            existing_account = db.query(GitHubAccount).filter(
                GitHubAccount.user_id == current_user.id,
                GitHubAccount.username == account_data.username
            ).first()
            
            if existing_account:
                error_count += 1
                errors.append(f"账号 {account_data.username}: 该GitHub用户名已存在")
                continue
            
            # 加密敏感数据
            encrypted_password = encrypt_data(account_data.password)
            encrypted_totp_secret = encrypt_data(account_data.totp_secret)
            
            # 创建新账号
            new_account = GitHubAccount(
                user_id=current_user.id,
                username=account_data.username,
                encrypted_password=encrypted_password,
                encrypted_totp_secret=encrypted_totp_secret,
                created_at=account_data.created_at
            )
            
            db.add(new_account)
            success_count += 1
            
        except Exception as e:
            error_count += 1
            errors.append(f"账号 {account_data.username}: {str(e)}")
            continue
    
    # 提交所有成功的更改
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        return BatchImportResponse(
            success=False,
            message=f"批量导入失败: {str(e)}"
        )
    
    # 构造结果
    result = BatchImportResult(
        success_count=success_count,
        error_count=error_count,
        errors=errors
    )
    
    if success_count > 0:
        message = f"批量导入完成: 成功 {success_count} 个"
        if error_count > 0:
            message += f", 失败 {error_count} 个"
        return BatchImportResponse(
            success=True,
            message=message,
            result=result
        )
    else:
        return BatchImportResponse(
            success=False,
            message="批量导入失败: 没有成功导入任何账号",
            result=result
        )


@router.post("/oauth-login/{github_account_id}", response_model=GitHubOAuthLoginResponse)
async def github_oauth_login(
    github_account_id: int,
    website_url: str = "https://anyrouter.top",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    使用GitHub账号通过OAuth登录第三方网站（如anyrouter.top）
    """
    # 获取GitHub账号信息
    github_account = db.query(GitHubAccount).filter(
        GitHubAccount.id == github_account_id,
        GitHubAccount.user_id == current_user.id
    ).first()
    
    if not github_account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="GitHub账号不存在"
        )
    
    try:
        # 解密GitHub账号信息
        github_username = github_account.username
        github_password = decrypt_data(github_account.encrypted_password)
        totp_secret = decrypt_data(github_account.encrypted_totp_secret)
        
        # 导入WebsiteSimulator
        from utils.website_simulator import website_simulator
        
        # 执行GitHub OAuth登录
        success, message, session_data = website_simulator.simulate_github_oauth_login(
            website_url,
            github_username,
            github_password,
            totp_secret
        )
        
        if success:
            return GitHubOAuthLoginResponse(
                success=True,
                message=message,
                login_method="github_oauth",
                session_info="GitHub OAuth登录成功，会话已建立",
                oauth_details={
                    "github_account": github_username,
                    "target_website": website_url,
                    "login_time": session_data.get("login_time"),
                    "cookies_count": len(session_data.get("cookies", {}))
                }
            )
        else:
            return GitHubOAuthLoginResponse(
                success=False,
                message=message,
                login_method="github_oauth",
                session_info=None,
                oauth_details={
                    "github_account": github_username,
                    "target_website": website_url,
                    "error_details": message
                }
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"GitHub OAuth登录失败: {str(e)}"
        )


@router.post("/oauth-login-anyrouter/{github_account_id}", response_model=GitHubOAuthLoginResponse)  
async def github_oauth_login_anyrouter(
    github_account_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    专门用于anyrouter.top的GitHub OAuth登录快捷方式
    """
    return await github_oauth_login(
        github_account_id=github_account_id,
        website_url="https://anyrouter.top",
        current_user=current_user,
        db=db
    )