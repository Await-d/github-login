"""
仓库收藏管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from sqlalchemy import func
import asyncio

from models.database import get_db, User, GitHubAccount
from models.repository_star import RepositoryStarTask, RepositoryStarRecord
from models.schemas import (
    RepositoryStarTaskCreate,
    RepositoryStarTaskUpdate,
    RepositoryStarTaskResponse,
    RepositoryStarTaskWithStats,
    RepositoryStarRecordResponse,
    RepositoryStarRecordSchema,
    RepositoryStarExecuteRequest,
    RepositoryStarExecuteResponse,
    RepositoryBatchImportRequest,
    RepositoryBatchExecuteRequest,
    RepositoryBatchExecuteResponse,
    BaseResponse
)
from utils.auth import get_current_user
from utils.encryption import decrypt_data
from utils.github_star import parse_repository_url, star_repository_simple
from utils.repository_star_queue import repository_star_queue
from utils.rate_limiter import (
    check_batch_execute_rate_limit,
    check_task_execute_rate_limit,
    check_batch_import_rate_limit
)

router = APIRouter()


# 队列执行器函数
async def _queue_executor(
    task_items: list[tuple[int, str]],
    user_id: int,
    account_ids: list[int],
    force_execute: bool
) -> dict:
    """
    队列任务执行器 - 按账号为中心执行star操作（带智能策略）

    新策略：
    1. 按账号循环（而不是按仓库循环）
    2. 每个账号登录一次，执行所有仓库的收藏操作
    3. 之后切换到下一个账号
    """
    from models.database import SessionLocal
    import random

    # 从配置文件读取参数
    from utils.config import config
    ACCOUNT_DELAY_MIN = config.ACCOUNT_DELAY_MIN
    ACCOUNT_DELAY_MAX = config.ACCOUNT_DELAY_MAX
    MAX_RETRY = config.MAX_RETRY
    RETRY_DELAY = config.RETRY_DELAY

    db = SessionLocal()
    try:
        # 初始化统计
        total_success_count = 0
        total_failed_count = 0
        total_already_starred_count = 0
        details = []

        # 随机打乱账号顺序，避免固定模式
        shuffled_account_ids = account_ids.copy()
        random.shuffle(shuffled_account_ids)

        # ========== 新逻辑：按账号为中心 ==========
        for account_idx, account_id in enumerate(shuffled_account_ids):
            account = db.query(GitHubAccount).filter(
                GitHubAccount.id == account_id,
                GitHubAccount.user_id == user_id
            ).first()

            if not account:
                continue

            # 账号间延迟（除了第一个账号）
            if account_idx > 0:
                delay = random.uniform(ACCOUNT_DELAY_MIN, ACCOUNT_DELAY_MAX)
                print(f"⏰ 账号间延迟 {delay:.1f} 秒...")
                await asyncio.sleep(delay)

            print(f"👤 开始执行账号: {account.username} ({account_idx + 1}/{len(shuffled_account_ids)})")

            # 解密一次账号信息（为该账号的所有仓库操作服用）
            try:
                github_password = decrypt_data(account.encrypted_password)
                totp_secret = decrypt_data(account.encrypted_totp_secret)
            except Exception as e:
                print(f"❌ 账号 {account.username} 解密失败: {e}")
                for task_id, _ in task_items:
                    details.append({
                        "task_id": task_id,
                        "account_id": account_id,
                        "username": account.username,
                        "status": "failed",
                        "message": f"账号信息解密失败"
                    })
                continue

            # 对该账号执行所有仓库的收藏操作
            for repo_idx, (task_id, repository_url) in enumerate(task_items):
                # 仓库间延迟（除了该账号的第一个仓库）
                if repo_idx > 0:
                    repo_delay = random.uniform(1, 3)  # 仓库间延迟较短
                    print(f"  ⏰ 仓库间延迟 {repo_delay:.1f} 秒...")
                    await asyncio.sleep(repo_delay)

                print(f"  📦 执行仓库: {repository_url} ({repo_idx + 1}/{len(task_items)})")

                retry_count = 0
                success = False
                message = ""

                # 重试循环
                while retry_count <= MAX_RETRY:
                    try:
                        # 执行star操作
                        success, message = await star_repository_simple(
                            repository_url,
                            account.username,
                            github_password,
                            totp_secret,
                            force_execute
                        )

                        # 如果成功或已收藏，跳出重试循环
                        if success:
                            break

                        # 失败且还有重试机会
                        if retry_count < MAX_RETRY:
                            retry_count += 1
                            print(f"  ⚠️ 仓库执行失败，{RETRY_DELAY}秒后进行第{retry_count}次重试...")
                            await asyncio.sleep(RETRY_DELAY)
                        else:
                            break

                    except Exception as e:
                        # 异常处理
                        import logging
                        logging.error(f"账号 {account.username} 执行仓库 {repository_url} 异常: {type(e).__name__}", exc_info=True)
                        message = f"执行失败: {type(e).__name__}"
                        if retry_count < MAX_RETRY:
                            retry_count += 1
                            print(f"  ❌ 执行异常，{RETRY_DELAY}秒后进行第{retry_count}次重试...")
                            await asyncio.sleep(RETRY_DELAY)
                        else:
                            print(f"  ❌ 重试{MAX_RETRY}次后仍失败")
                            break

                # 判断最终状态并记录
                if success:
                    if "已收藏" in message:
                        record_status = "already_starred"
                        total_already_starred_count += 1
                    else:
                        record_status = "success"
                        total_success_count += 1
                else:
                    record_status = "failed"
                    total_failed_count += 1

                # 创建或更新执行记录
                existing_record = db.query(RepositoryStarRecord).filter(
                    RepositoryStarRecord.task_id == task_id,
                    RepositoryStarRecord.github_account_id == account_id
                ).first()

                if existing_record:
                    # 更新记录
                    existing_record.status = record_status
                    existing_record.error_message = None if success else message
                    existing_record.executed_at = func.now()
                else:
                    # 创建新记录
                    record = RepositoryStarRecord(
                        task_id=task_id,
                        github_account_id=account_id,
                        status=record_status,
                        error_message=None if success else message
                    )
                    db.add(record)

                details.append({
                    "task_id": task_id,
                    "account_id": account_id,
                    "username": account.username,
                    "status": record_status,
                    "message": message
                })

        db.commit()

        return {
            "success_count": total_success_count,
            "failed_count": total_failed_count,
            "already_starred_count": total_already_starred_count,
            "total": len(account_ids) * len(task_items),
            "task_count": len(task_items),
            "account_count": len(account_ids),
            "details": details
        }

    finally:
        db.close()


@router.post("/tasks", response_model=RepositoryStarTaskResponse)
async def create_repository_star_task(
    task_data: RepositoryStarTaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建仓库收藏任务"""
    
    # 解析仓库URL
    owner, repo_name = parse_repository_url(task_data.repository_url)
    
    if not owner or not repo_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="无效的GitHub仓库URL"
        )
    
    # 检查是否已存在相同仓库的任务
    existing_task = db.query(RepositoryStarTask).filter(
        RepositoryStarTask.user_id == current_user.id,
        RepositoryStarTask.owner == owner,
        RepositoryStarTask.repo_name == repo_name
    ).first()
    
    if existing_task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"该仓库的收藏任务已存在: {owner}/{repo_name}"
        )
    
    # 创建新任务
    new_task = RepositoryStarTask(
        user_id=current_user.id,
        repository_url=task_data.repository_url,
        owner=owner,
        repo_name=repo_name,
        description=task_data.description
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    # 如果设置了立即执行
    if task_data.execute_immediately:
        # 确定要执行的账号列表
        account_ids_to_execute = task_data.github_account_ids or []

        # 如果没有指定账号，使用所有可用账号
        if not account_ids_to_execute:
            all_accounts = db.query(GitHubAccount).filter(
                GitHubAccount.user_id == current_user.id
            ).all()
            account_ids_to_execute = [acc.id for acc in all_accounts]

        # 异步执行star操作
        for account_id in account_ids_to_execute:
            # 验证账号是否属于当前用户
            account = db.query(GitHubAccount).filter(
                GitHubAccount.id == account_id,
                GitHubAccount.user_id == current_user.id
            ).first()

            if account:
                # 执行star操作
                try:
                    github_password = decrypt_data(account.encrypted_password)
                    totp_secret = decrypt_data(account.encrypted_totp_secret)

                    success, message = await star_repository_simple(
                        task_data.repository_url,
                        account.username,
                        github_password,
                        totp_secret,
                        False  # 创建任务时不强制执行
                    )

                    # 创建执行记录
                    record = RepositoryStarRecord(
                        task_id=new_task.id,
                        github_account_id=account_id,
                        status="success" if success else "failed",
                        error_message=None if success else message
                    )
                    db.add(record)

                except Exception as e:
                    # 记录失败
                    record = RepositoryStarRecord(
                        task_id=new_task.id,
                        github_account_id=account_id,
                        status="failed",
                        error_message=str(e)
                    )
                    db.add(record)

        db.commit()
    
    # 获取任务统计信息
    task_stats = _get_task_with_stats(db, new_task)
    
    return RepositoryStarTaskResponse(
        success=True,
        message="仓库收藏任务创建成功",
        task=task_stats
    )


@router.get("/tasks", response_model=RepositoryStarTaskResponse)
async def get_repository_star_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有仓库收藏任务"""
    
    tasks = db.query(RepositoryStarTask).filter(
        RepositoryStarTask.user_id == current_user.id
    ).order_by(RepositoryStarTask.created_at.desc()).all()
    
    # 为每个任务添加统计信息
    tasks_with_stats = [_get_task_with_stats(db, task) for task in tasks]
    
    return RepositoryStarTaskResponse(
        success=True,
        message="获取任务列表成功",
        tasks=tasks_with_stats
    )


@router.get("/tasks/{task_id}", response_model=RepositoryStarTaskResponse)
async def get_repository_star_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定仓库收藏任务详情"""
    
    task = db.query(RepositoryStarTask).filter(
        RepositoryStarTask.id == task_id,
        RepositoryStarTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    task_stats = _get_task_with_stats(db, task)
    
    return RepositoryStarTaskResponse(
        success=True,
        message="获取任务详情成功",
        task=task_stats
    )


@router.put("/tasks/{task_id}", response_model=RepositoryStarTaskResponse)
async def update_repository_star_task(
    task_id: int,
    task_data: RepositoryStarTaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新仓库收藏任务"""
    
    task = db.query(RepositoryStarTask).filter(
        RepositoryStarTask.id == task_id,
        RepositoryStarTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 更新任务信息
    if task_data.repository_url is not None:
        owner, repo_name = parse_repository_url(task_data.repository_url)
        if not owner or not repo_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的GitHub仓库URL"
            )
        task.repository_url = task_data.repository_url
        task.owner = owner
        task.repo_name = repo_name
    
    if task_data.description is not None:
        task.description = task_data.description
    
    db.commit()
    db.refresh(task)
    
    task_stats = _get_task_with_stats(db, task)
    
    return RepositoryStarTaskResponse(
        success=True,
        message="任务更新成功",
        task=task_stats
    )


@router.delete("/tasks/{task_id}")
async def delete_repository_star_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除仓库收藏任务"""
    
    task = db.query(RepositoryStarTask).filter(
        RepositoryStarTask.id == task_id,
        RepositoryStarTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    db.delete(task)
    db.commit()
    
    return BaseResponse(
        success=True,
        message="任务删除成功"
    )


@router.post("/tasks/{task_id}/execute", response_model=RepositoryStarExecuteResponse)
async def execute_repository_star_task(
    task_id: int,
    execute_data: RepositoryStarExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手动执行仓库收藏任务（加入队列）"""

    # 速率限制检查
    check_task_execute_rate_limit(current_user.id)

    task = db.query(RepositoryStarTask).filter(
        RepositoryStarTask.id == task_id,
        RepositoryStarTask.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    # 确定要执行的账号列表
    if execute_data.github_account_ids:
        # 使用指定的账号
        account_ids = execute_data.github_account_ids
    else:
        # 获取所有用户的GitHub账号
        all_accounts = db.query(GitHubAccount).filter(
            GitHubAccount.user_id == current_user.id
        ).all()
        account_ids = [acc.id for acc in all_accounts]

    if not account_ids:
        return RepositoryStarExecuteResponse(
            success=False,
            message="没有可执行的GitHub账号",
            total=0,
            success_count=0,
            failed_count=0,
            already_starred_count=0
        )

    # 将单个任务作为单项任务加入队列（兼容单个任务执行）
    try:
        queue_task = await repository_star_queue.add_task(
            user_id=current_user.id,
            account_ids=account_ids,
            force_execute=execute_data.force_execute,
            task_id=task_id,
            repository_url=task.repository_url
        )

        return RepositoryStarExecuteResponse(
            success=True,
            message=f"任务已加入队列，共{len(account_ids)}个账号待执行",
            total=len(account_ids),
            success_count=0,
            failed_count=0,
            already_starred_count=0,
            queue_status=repository_star_queue.get_task_status(task_id=task_id)
        )
    except Exception as e:
        return RepositoryStarExecuteResponse(
            success=False,
            message=f"任务加入队列失败: {str(e)}",
            total=0,
            success_count=0,
            failed_count=0,
            already_starred_count=0
        )


@router.get("/tasks/{task_id}/records", response_model=RepositoryStarRecordResponse)
async def get_task_records(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务的执行记录"""
    
    task = db.query(RepositoryStarTask).filter(
        RepositoryStarTask.id == task_id,
        RepositoryStarTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )
    
    # 获取执行记录并关联GitHub账号信息
    records = db.query(RepositoryStarRecord).filter(
        RepositoryStarRecord.task_id == task_id
    ).order_by(RepositoryStarRecord.executed_at.desc()).all()
    
    # 转换为schema并添加GitHub用户名
    records_with_username = []
    for record in records:
        github_account = db.query(GitHubAccount).filter(
            GitHubAccount.id == record.github_account_id
        ).first()
        
        record_schema = RepositoryStarRecordSchema(
            id=record.id,
            task_id=record.task_id,
            github_account_id=record.github_account_id,
            status=record.status,
            error_message=record.error_message,
            executed_at=record.executed_at,
            github_username=github_account.username if github_account else "未知"
        )
        records_with_username.append(record_schema)
    
    return RepositoryStarRecordResponse(
        success=True,
        message="获取执行记录成功",
        records=records_with_username
    )


@router.post("/batch-import", response_model=RepositoryStarTaskResponse)
async def batch_import_repository_star_tasks(
    import_data: RepositoryBatchImportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量导入仓库收藏任务"""
    
    # 速率限制检查
    check_batch_import_rate_limit(current_user.id)
    
    # 限制批量导入数量,防止滥用
    from utils.config import config
    if len(import_data.repository_urls) > config.MAX_BATCH_IMPORT_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"一次最多导入{config.MAX_BATCH_IMPORT_SIZE}个仓库"
        )
    
    created_tasks = []
    
    for repo_url in import_data.repository_urls:
        # 解析仓库URL
        owner, repo_name = parse_repository_url(repo_url)
        
        if not owner or not repo_name:
            continue  # 跳过无效的URL
        
        # 检查是否已存在
        existing_task = db.query(RepositoryStarTask).filter(
            RepositoryStarTask.user_id == current_user.id,
            RepositoryStarTask.owner == owner,
            RepositoryStarTask.repo_name == repo_name
        ).first()
        
        if existing_task:
            continue  # 跳过已存在的任务
        
        # 创建新任务
        new_task = RepositoryStarTask(
            user_id=current_user.id,
            repository_url=repo_url,
            owner=owner,
            repo_name=repo_name,
            description=f"批量导入: {owner}/{repo_name}"
        )
        
        db.add(new_task)
        created_tasks.append(new_task)
    
    db.commit()

    # 如果设置了立即执行，则执行star操作
    if import_data.execute_immediately and created_tasks:
        # 确定要执行的账号列表
        account_ids_to_execute = import_data.github_account_ids or []

        # 如果没有指定账号，使用所有可用账号
        if not account_ids_to_execute:
            all_accounts = db.query(GitHubAccount).filter(
                GitHubAccount.user_id == current_user.id
            ).all()
            account_ids_to_execute = [acc.id for acc in all_accounts]

        for task in created_tasks:
            db.refresh(task)
            for account_id in account_ids_to_execute:
                account = db.query(GitHubAccount).filter(
                    GitHubAccount.id == account_id,
                    GitHubAccount.user_id == current_user.id
                ).first()

                if account:
                    try:
                        github_password = decrypt_data(account.encrypted_password)
                        totp_secret = decrypt_data(account.encrypted_totp_secret)

                        success, message = await star_repository_simple(
                            task.repository_url,
                            account.username,
                            github_password,
                            totp_secret,
                            False  # 批量导入时不强制执行
                        )

                        record = RepositoryStarRecord(
                            task_id=task.id,
                            github_account_id=account_id,
                            status="success" if success else "failed",
                            error_message=None if success else message
                        )
                        db.add(record)

                    except Exception as e:
                        record = RepositoryStarRecord(
                            task_id=task.id,
                            github_account_id=account_id,
                            status="failed",
                            error_message=str(e)
                        )
                        db.add(record)

        db.commit()
    
    # 获取创建的任务列表（带统计）
    tasks_with_stats = [_get_task_with_stats(db, task) for task in created_tasks]
    
    return RepositoryStarTaskResponse(
        success=True,
        message=f"成功导入{len(created_tasks)}个仓库收藏任务",
        tasks=tasks_with_stats
    )


@router.post("/batch-execute", response_model=RepositoryBatchExecuteResponse)
async def batch_execute_repository_star_tasks(
    execute_data: RepositoryBatchExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """批量执行仓库收藏任务"""

    # 速率限制检查
    check_batch_execute_rate_limit(current_user.id)

    if not execute_data.task_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="任务ID列表不能为空"
        )

    # 验证所有任务的所有权
    tasks = db.query(RepositoryStarTask).filter(
        RepositoryStarTask.id.in_(execute_data.task_ids),
        RepositoryStarTask.user_id == current_user.id
    ).all()

    if len(tasks) != len(execute_data.task_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="部分任务不存在或无权访问"
        )

    # 获取所有用户的GitHub账号
    all_accounts = db.query(GitHubAccount).filter(
        GitHubAccount.user_id == current_user.id
    ).all()
    account_ids = [acc.id for acc in all_accounts]

    if not account_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="没有可用的GitHub账号"
        )

    # ========== 新逻辑：将所有任务作为一个批处理加入队列 ==========
    # 构建任务项列表 [(task_id, repository_url), ...]
    task_items = [(task.id, task.repository_url) for task in tasks]

    try:
        queue_task = await repository_star_queue.add_task(
            user_id=current_user.id,
            account_ids=account_ids,
            force_execute=execute_data.force_execute,
            task_items=task_items
        )

        batch_id = queue_task.batch_id

        return RepositoryBatchExecuteResponse(
            success=True,
            message=f"成功将 {len(tasks)} 个仓库任务加入执行队列（按账号中心执行）",
            total_tasks=len(execute_data.task_ids),
            queued_tasks=len(execute_data.task_ids)
        )
    except Exception as e:
        print(f"⚠️ 批处理加入队列失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批处理加入队列失败: {str(e)}"
        )


@router.post("/tasks/{task_id}/unstar", response_model=RepositoryStarExecuteResponse)
async def unstar_repository_task(
    task_id: int,
    execute_data: RepositoryStarExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消仓库收藏任务"""

    task = db.query(RepositoryStarTask).filter(
        RepositoryStarTask.id == task_id,
        RepositoryStarTask.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    # 确定要执行的账号列表
    if execute_data.github_account_ids:
        # 使用指定的账号
        account_ids = execute_data.github_account_ids
    else:
        # 获取所有已star的账号
        starred_account_ids = db.query(RepositoryStarRecord.github_account_id).filter(
            RepositoryStarRecord.task_id == task_id,
            RepositoryStarRecord.status.in_(["success", "already_starred"])
        ).all()
        account_ids = [record[0] for record in starred_account_ids]

    if not account_ids:
        return RepositoryStarExecuteResponse(
            success=False,
            message="没有可取消收藏的GitHub账号",
            total=0,
            success_count=0,
            failed_count=0,
            already_starred_count=0
        )

    # 导入unstar函数
    from utils.github_star import unstar_repository_simple

    # 执行unstar操作
    total = len(account_ids)
    success_count = 0
    failed_count = 0
    not_starred_count = 0
    details = []

    for account_id in account_ids:
        account = db.query(GitHubAccount).filter(
            GitHubAccount.id == account_id,
            GitHubAccount.user_id == current_user.id
        ).first()

        if not account:
            continue

        try:
            # 解密账号信息
            github_password = decrypt_data(account.encrypted_password)
            totp_secret = decrypt_data(account.encrypted_totp_secret)

            # 执行unstar操作
            success, message = await unstar_repository_simple(
                task.repository_url,
                account.username,
                github_password,
                totp_secret
            )

            # 判断状态
            if success:
                if "未收藏" in message or "无需取消" in message:
                    record_status = "not_starred"
                    not_starred_count += 1
                else:
                    record_status = "unstarred"
                    success_count += 1
            else:
                record_status = "failed"
                failed_count += 1

            # 删除或更新执行记录
            existing_record = db.query(RepositoryStarRecord).filter(
                RepositoryStarRecord.task_id == task_id,
                RepositoryStarRecord.github_account_id == account_id
            ).first()

            if existing_record:
                # 如果成功取消，删除记录
                if record_status == "unstarred":
                    db.delete(existing_record)
                else:
                    # 更新记录状态
                    existing_record.status = record_status
                    existing_record.error_message = None if success else message

            # 添加到详情列表
            details.append({
                "account_id": account_id,
                "username": account.username,
                "status": record_status,
                "message": message
            })

        except Exception as e:
            failed_count += 1

            details.append({
                "account_id": account_id,
                "username": account.username,
                "status": "failed",
                "message": str(e)
            })

    db.commit()

    return RepositoryStarExecuteResponse(
        success=True,
        message=f"取消收藏完成: 成功{success_count}个，失败{failed_count}个，未收藏{not_starred_count}个",
        total=total,
        success_count=success_count,
        failed_count=failed_count,
        already_starred_count=not_starred_count,
        details=details
    )


@router.get("/tasks/{task_id}/queue-status")
async def get_task_queue_status(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务的队列状态"""

    # 验证任务是否属于当前用户
    task = db.query(RepositoryStarTask).filter(
        RepositoryStarTask.id == task_id,
        RepositoryStarTask.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    queue_status = repository_star_queue.get_task_status(task_id)

    if not queue_status:
        return BaseResponse(
            success=True,
            message="任务不在队列中",
            data=None
        )

    return BaseResponse(
        success=True,
        message="获取队列状态成功",
        data=queue_status
    )


@router.get("/queue/info")
async def get_queue_info(
    current_user: User = Depends(get_current_user)
):
    """获取队列信息（需要登录）"""
    queue_info = repository_star_queue.get_queue_info()
    return BaseResponse(
        success=True,
        message="获取队列信息成功",
        data=queue_info
    )


@router.post("/tasks/{task_id}/cancel")
async def cancel_task_in_queue(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """取消队列中的任务"""

    # 验证任务是否属于当前用户
    task = db.query(RepositoryStarTask).filter(
        RepositoryStarTask.id == task_id,
        RepositoryStarTask.user_id == current_user.id
    ).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="任务不存在"
        )

    success = await repository_star_queue.cancel_task(task_id)

    if success:
        return BaseResponse(
            success=True,
            message="任务已取消"
        )
    else:
        return BaseResponse(
            success=False,
            message="无法取消任务（任务可能已在执行或已完成）"
        )


def _get_task_with_stats(db: Session, task: RepositoryStarTask) -> RepositoryStarTaskWithStats:
    """获取带统计信息的任务"""
    
    # 获取所有用户的GitHub账号数量
    total_accounts = db.query(func.count(GitHubAccount.id)).filter(
        GitHubAccount.user_id == task.user_id
    ).scalar()
    
    # 获取已经star的账号数量
    starred_accounts = db.query(func.count(RepositoryStarRecord.id)).filter(
        RepositoryStarRecord.task_id == task.id,
        RepositoryStarRecord.status.in_(["success", "already_starred"])
    ).scalar()
    
    # 获取成功和失败的次数
    success_count = db.query(func.count(RepositoryStarRecord.id)).filter(
        RepositoryStarRecord.task_id == task.id,
        RepositoryStarRecord.status == "success"
    ).scalar()
    
    failed_count = db.query(func.count(RepositoryStarRecord.id)).filter(
        RepositoryStarRecord.task_id == task.id,
        RepositoryStarRecord.status == "failed"
    ).scalar()
    
    return RepositoryStarTaskWithStats(
        id=task.id,
        user_id=task.user_id,
        repository_url=task.repository_url,
        owner=task.owner,
        repo_name=task.repo_name,
        description=task.description,
        created_at=task.created_at,
        updated_at=task.updated_at,
        total_accounts=total_accounts or 0,
        starred_accounts=starred_accounts or 0,
        success_count=success_count or 0,
        failed_count=failed_count or 0
    )
