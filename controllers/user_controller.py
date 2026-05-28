from fastapi import APIRouter, Path, Query, Body, Depends
from typing import List, Optional
import sys
# 统一项目导入规范
from config.database import get_db
from utils.result import Result
from schemas.user import User
from schemas.user_dto import UserPasswordUpdateDTO
from service.user_service import UserService
from schemas.user_dto import UserLoginDTO,UserUpdate

# 路由配置
router = APIRouter(
    prefix="/user",
    tags=["用户管理接口"]
)

# ===================== 1. 用户注册 =====================
@router.post("/register", summary="用户注册")
def register(
    user: User = Body(...),
    db = Depends(get_db)
):
    service = UserService(db)
    service.create_user(user)
    return Result.success_msg("注册成功", None)

# ===================== 2. 用户登录 =====================
@router.post("/login", summary="用户登录")
def login(
    login_dto: UserLoginDTO = Body(...),
    db = Depends(get_db)
):
    service = UserService(db)
    data = service.login(login_dto)
    return Result.success_data(data)

# ===================== 3. 更新用户信息 =====================
@router.put("/info", summary="更新用户信息")
def update_user_info(
    user_update: UserUpdate = Body(...),  # 用你的新DTO
    db = Depends(get_db)
):
    
    service = UserService(db)
    
    # 👇 👇 👇 直接从数据库查出现有数据，只更新需要改的字段
    exist_user = service.get_user_by_id(user_update.id)
    
    # 用 model_dump 只更新前端传了的字段
    update_data = user_update.model_dump(exclude_unset=True)
    
    # 循环赋值，不碰 password、email
    for key, value in update_data.items():
        setattr(exist_user, key, value)

    # 直接存，不走 service.update_user，彻底绕开类型问题
    db.commit()
    db.refresh(exist_user)

    return Result.success_msg("更新成功", None)
# ===================== 4. 修改密码 =====================
@router.put("/password/{id}", summary="修改密码")
def update_password(
    id: int = Path(...),
    dto: UserPasswordUpdateDTO = Body(...),
    db = Depends(get_db)
):
    service = UserService(db)
    service.update_password(id, dto)
    return Result.success_msg("密码修改成功", None)

# ===================== 5. 获取用户列表（分页） =====================
@router.get("/list", summary="获取用户列表")
def get_user_list(
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    username: Optional[str] = Query(None),
    roleCode: Optional[str] = Query(None),
    db = Depends(get_db)
):
    service = UserService(db)
    data = service.get_users_by_page(username, roleCode, pageNum, pageSize)
    
    #     # 👇 在这里加一行 强制打印！！！
    # print("=== 返回前端的用户数据 ===", data)
    return Result.success_data(data)

# ===================== 6. 删除用户 =====================
@router.delete("/{id}", summary="删除用户")
def delete_user(
    id: int = Path(...),
    db = Depends(get_db)
):
    service = UserService(db)
    service.delete_user_by_id(id)
    return Result.success_msg("删除成功", None)

# ===================== 7. 批量删除用户 =====================
@router.delete("/batch", summary="批量删除用户")
def batch_delete_users(
    ids: List[int] = Body(...),
    db = Depends(get_db)
):
    service = UserService(db)
    service.batch_delete_users(ids)
    return Result.success_msg("批量删除成功", None)

# ===================== 8. 重置用户密码 =====================
@router.put("/{id}/reset-password", summary="重置用户密码")
def reset_password(
    id: int = Path(...),
    db = Depends(get_db)
):
    service = UserService(db)
    new_pwd = service.reset_password(id)
    
    #   正确打印字符串
    print("==================== 打印新密码 ====================")
    print("密码为：", new_pwd)
    print("===================================================")
    return Result.success_msg(f"密码重置成功,新密码为:{new_pwd}",new_pwd )

# ===================== 9. 根据角色查找用户 =====================
@router.get("/role/{roleCode}", summary="根据角色查找用户")
def get_users_by_role(
    roleCode: str = Path(...),
    db = Depends(get_db)
):
    service = UserService(db)
    data = service.get_users_by_page(None, roleCode, 1, sys.maxsize)
    
    return Result.success_data(data)
