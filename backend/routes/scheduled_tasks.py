"""
定时任务管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json
from datetime import datetime

from models.database import get_db, User, ScheduledTask, TaskExecutionLog, GitHubAccount
from models.schemas import (
    ScheduledTaskCreate,
    ScheduledTaskUpdate,
    ScheduledTaskResponse,
    ScheduledTaskSchema,
    TaskExecutionLogResponse,
    TaskExecutionLogSchema,
    CreateGitHubOAuthTaskRequest,
    GitHubOAuthTaskParams
)
from utils.auth import get_current_user

router = APIRouter()


@router.get("/tasks", response_model=ScheduledTaskResponse)
async def get_scheduled_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取用户的所有定时任务"""
    try:
        tasks = db.query(ScheduledTask).filter(
            ScheduledTask.user_id == current_user.id
        ).all()
        
        task_schemas = []
        for task in tasks:
            task_schema = ScheduledTaskSchema(
                id=task.id,
                user_id=task.user_id,
                name=task.name,
                description=task.description,
                task_type=task.task_type,
                cron_expression=task.cron_expression,
                timezone=task.timezone,
                task_params=json.loads(task.task_params) if task.task_params else {},
                is_active=task.is_active,
                last_run_time=task.last_run_time,
                next_run_time=task.next_run_time,
                last_result=task.last_result,
                run_count=task.run_count,
                success_count=task.success_count,
                error_count=task.error_count,
                created_at=task.created_at,
                updated_at=task.updated_at
            )
            task_schemas.append(task_schema)
        
        return ScheduledTaskResponse(
            success=True,
            message="获取定时任务列表成功",
            tasks=task_schemas
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取定时任务失败: {str(e)}"
        )


@router.get("/tasks/{task_id}", response_model=ScheduledTaskResponse)
async def get_scheduled_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定定时任务详情"""
    task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id,
        ScheduledTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="定时任务未找到"
        )
    
    try:
        task_schema = ScheduledTaskSchema(
            id=task.id,
            user_id=task.user_id,
            name=task.name,
            description=task.description,
            task_type=task.task_type,
            cron_expression=task.cron_expression,
            timezone=task.timezone,
            task_params=json.loads(task.task_params) if task.task_params else {},
            is_active=task.is_active,
            last_run_time=task.last_run_time,
            next_run_time=task.next_run_time,
            last_result=task.last_result,
            run_count=task.run_count,
            success_count=task.success_count,
            error_count=task.error_count,
            created_at=task.created_at,
            updated_at=task.updated_at
        )
        
        return ScheduledTaskResponse(
            success=True,
            message="获取定时任务详情成功",
            task=task_schema
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取定时任务详情失败: {str(e)}"
        )


@router.post("/tasks/github-oauth", response_model=ScheduledTaskResponse)
async def create_github_oauth_task(
    task_data: CreateGitHubOAuthTaskRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建GitHub OAuth登录定时任务"""
    try:
        # 验证GitHub账号是否存在且属于当前用户
        github_accounts = db.query(GitHubAccount).filter(
            GitHubAccount.id.in_(task_data.github_account_ids),
            GitHubAccount.user_id == current_user.id
        ).all()
        
        if len(github_accounts) != len(task_data.github_account_ids):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="部分GitHub账号不存在或不属于当前用户"
            )
        
        # 准备任务参数
        task_params = GitHubOAuthTaskParams(
            github_account_ids=task_data.github_account_ids,
            target_website=task_data.target_website,
            retry_count=task_data.retry_count
        )
        
        # 创建定时任务
        new_task = ScheduledTask(
            user_id=current_user.id,
            name=task_data.name,
            description=task_data.description,
            task_type="github_oauth_login",
            cron_expression=task_data.cron_expression,
            task_params=task_params.model_dump_json(),
            is_active=task_data.is_active
        )
        
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        # 计算下次执行时间
        from utils.task_scheduler import calculate_next_run_time
        next_run = calculate_next_run_time(task_data.cron_expression)
        new_task.next_run_time = next_run
        db.commit()
        
        task_schema = ScheduledTaskSchema(
            id=new_task.id,
            user_id=new_task.user_id,
            name=new_task.name,
            description=new_task.description,
            task_type=new_task.task_type,
            cron_expression=new_task.cron_expression,
            timezone=new_task.timezone,
            task_params=json.loads(new_task.task_params) if new_task.task_params else {},
            is_active=new_task.is_active,
            last_run_time=new_task.last_run_time,
            next_run_time=new_task.next_run_time,
            last_result=new_task.last_result,
            run_count=new_task.run_count,
            success_count=new_task.success_count,
            error_count=new_task.error_count,
            created_at=new_task.created_at,
            updated_at=new_task.updated_at
        )
        
        return ScheduledTaskResponse(
            success=True,
            message="GitHub OAuth定时任务创建成功",
            task=task_schema
        )
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建定时任务失败: {str(e)}"
        )


@router.put("/tasks/{task_id}", response_model=ScheduledTaskResponse)
async def update_scheduled_task(
    task_id: int,
    task_data: ScheduledTaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新定时任务"""
    task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id,
        ScheduledTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="定时任务未找到"
        )
    
    try:
        # 更新字段
        if task_data.name is not None:
            task.name = task_data.name
        if task_data.description is not None:
            task.description = task_data.description
        if task_data.cron_expression is not None:
            task.cron_expression = task_data.cron_expression
            # 重新计算下次执行时间
            from utils.task_scheduler import calculate_next_run_time
            task.next_run_time = calculate_next_run_time(task_data.cron_expression)
        if task_data.timezone is not None:
            task.timezone = task_data.timezone
        if task_data.task_params is not None:
            task.task_params = json.dumps(task_data.task_params)
        if task_data.is_active is not None:
            task.is_active = task_data.is_active
        
        db.commit()
        db.refresh(task)
        
        task_schema = ScheduledTaskSchema(
            id=task.id,
            user_id=task.user_id,
            name=task.name,
            description=task.description,
            task_type=task.task_type,
            cron_expression=task.cron_expression,
            timezone=task.timezone,
            task_params=json.loads(task.task_params) if task.task_params else {},
            is_active=task.is_active,
            last_run_time=task.last_run_time,
            next_run_time=task.next_run_time,
            last_result=task.last_result,
            run_count=task.run_count,
            success_count=task.success_count,
            error_count=task.error_count,
            created_at=task.created_at,
            updated_at=task.updated_at
        )
        
        return ScheduledTaskResponse(
            success=True,
            message="定时任务更新成功",
            task=task_schema
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新定时任务失败: {str(e)}"
        )


@router.delete("/tasks/{task_id}")
async def delete_scheduled_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除定时任务"""
    task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id,
        ScheduledTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="定时任务未找到"
        )
    
    try:
        db.delete(task)
        db.commit()
        
        return {
            "success": True,
            "message": "定时任务删除成功"
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除定时任务失败: {str(e)}"
        )


@router.post("/tasks/{task_id}/run")
async def run_task_manually(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """手动执行定时任务"""
    task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id,
        ScheduledTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="定时任务未找到"
        )
    
    try:
        # 执行任务
        from utils.task_executor import execute_task
        success, result = await execute_task(task, db)
        
        return {
            "success": success,
            "message": result if success else f"任务执行失败: {result}"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"执行任务失败: {str(e)}"
        )


@router.get("/tasks/{task_id}/logs", response_model=TaskExecutionLogResponse)
async def get_task_execution_logs(
    task_id: int,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取任务执行日志"""
    # 验证任务归属
    task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id,
        ScheduledTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="定时任务未找到"
        )
    
    try:
        logs = db.query(TaskExecutionLog).filter(
            TaskExecutionLog.task_id == task_id
        ).order_by(TaskExecutionLog.start_time.desc()).limit(limit).all()
        
        log_schemas = []
        for log in logs:
            log_schema = TaskExecutionLogSchema(
                id=log.id,
                task_id=log.task_id,
                start_time=log.start_time,
                end_time=log.end_time,
                duration=log.duration,
                status=log.status,
                result_message=log.result_message,
                error_details=log.error_details,
                execution_data=json.loads(log.execution_data) if log.execution_data else {}
            )
            log_schemas.append(log_schema)
        
        return TaskExecutionLogResponse(
            success=True,
            message="获取执行日志成功",
            logs=log_schemas
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取执行日志失败: {str(e)}"
        )


@router.post("/tasks/{task_id}/toggle")
async def toggle_task_status(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """切换任务启用/禁用状态"""
    task = db.query(ScheduledTask).filter(
        ScheduledTask.id == task_id,
        ScheduledTask.user_id == current_user.id
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="定时任务未找到"
        )
    
    try:
        task.is_active = not task.is_active
        db.commit()
        
        return {
            "success": True,
            "message": f"任务已{'启用' if task.is_active else '禁用'}",
            "is_active": task.is_active
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"切换任务状态失败: {str(e)}"
        )