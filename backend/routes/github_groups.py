"""
GitHub账号分组管理路由
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from models.database import get_db, User, GitHubAccount, GitHubAccountGroup
from models.schemas import (
    GitHubAccountGroupCreate,
    GitHubAccountGroupUpdate,
    GitHubAccountGroupResponse,
    GitHubAccountGroupWithCount,
    BaseResponse
)
from utils.auth import get_current_user

router = APIRouter()


@router.post("/groups", response_model=GitHubAccountGroupResponse)
async def create_group(
    group_data: GitHubAccountGroupCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """创建GitHub账号分组"""

    # 检查是否已存在同名分组
    existing_group = db.query(GitHubAccountGroup).filter(
        GitHubAccountGroup.user_id == current_user.id,
        GitHubAccountGroup.name == group_data.name
    ).first()

    if existing_group:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"分组名称已存在: {group_data.name}"
        )

    # 创建新分组
    new_group = GitHubAccountGroup(
        user_id=current_user.id,
        name=group_data.name,
        description=group_data.description,
        color=group_data.color
    )

    db.add(new_group)
    db.commit()
    db.refresh(new_group)

    return GitHubAccountGroupResponse(
        success=True,
        message="分组创建成功",
        group=new_group
    )


@router.get("/groups", response_model=GitHubAccountGroupResponse)
async def get_groups(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取所有GitHub账号分组"""

    groups = db.query(GitHubAccountGroup).filter(
        GitHubAccountGroup.user_id == current_user.id
    ).order_by(GitHubAccountGroup.created_at.desc()).all()

    # 为每个分组添加账号数量
    groups_with_count = []
    for group in groups:
        account_count = db.query(func.count(GitHubAccount.id)).filter(
            GitHubAccount.group_id == group.id
        ).scalar()

        group_dict = {
            "id": group.id,
            "user_id": group.user_id,
            "name": group.name,
            "description": group.description,
            "color": group.color,
            "created_at": group.created_at,
            "updated_at": group.updated_at,
            "account_count": account_count or 0
        }
        groups_with_count.append(GitHubAccountGroupWithCount(**group_dict))

    return GitHubAccountGroupResponse(
        success=True,
        message="获取分组列表成功",
        groups=groups_with_count
    )


@router.get("/groups/{group_id}", response_model=GitHubAccountGroupResponse)
async def get_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """获取指定GitHub账号分组详情"""

    group = db.query(GitHubAccountGroup).filter(
        GitHubAccountGroup.id == group_id,
        GitHubAccountGroup.user_id == current_user.id
    ).first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分组不存在"
        )

    return GitHubAccountGroupResponse(
        success=True,
        message="获取分组详情成功",
        group=group
    )


@router.put("/groups/{group_id}", response_model=GitHubAccountGroupResponse)
async def update_group(
    group_id: int,
    group_data: GitHubAccountGroupUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """更新GitHub账号分组"""

    group = db.query(GitHubAccountGroup).filter(
        GitHubAccountGroup.id == group_id,
        GitHubAccountGroup.user_id == current_user.id
    ).first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分组不存在"
        )

    # 如果要修改名称，检查是否与其他分组重名
    if group_data.name is not None and group_data.name != group.name:
        existing_group = db.query(GitHubAccountGroup).filter(
            GitHubAccountGroup.user_id == current_user.id,
            GitHubAccountGroup.name == group_data.name,
            GitHubAccountGroup.id != group_id
        ).first()

        if existing_group:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"分组名称已存在: {group_data.name}"
            )

        group.name = group_data.name

    if group_data.description is not None:
        group.description = group_data.description

    if group_data.color is not None:
        group.color = group_data.color

    db.commit()
    db.refresh(group)

    return GitHubAccountGroupResponse(
        success=True,
        message="分组更新成功",
        group=group
    )


@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """删除GitHub账号分组"""

    group = db.query(GitHubAccountGroup).filter(
        GitHubAccountGroup.id == group_id,
        GitHubAccountGroup.user_id == current_user.id
    ).first()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="分组不存在"
        )

    # 将该分组下的账号的group_id设为None
    db.query(GitHubAccount).filter(
        GitHubAccount.group_id == group_id
    ).update({"group_id": None})

    db.delete(group)
    db.commit()

    return BaseResponse(
        success=True,
        message="分组删除成功"
    )
