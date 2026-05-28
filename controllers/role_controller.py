from fastapi import APIRouter, Path, Query, Body, Depends
from typing import List
from utils.result import Result
    # 项目核心导入（统一规范）
from config.database import  get_db
from schemas.role import Role
from schemas.menu import Menu
from service.role_service import RoleService

    # 路由配置
router = APIRouter(prefix="/role", tags=["角色管理接口"])

    # ===================== 1. 创建角色 =====================
@router.post("", summary="创建角色")
def create_role(
        role: Role = Body(...),
        db = Depends(get_db)
    ):
        service = RoleService(db)
        service.create_role(role)
        return Result.success_msg("创建成功", None)

    # ===================== 2. 更新角色 =====================
@router.put("/{id}", summary="更新角色")
def update_role(
        id: int = Path(...),
        role: Role = Body(...),
        db = Depends(get_db)
    ):
        role.id = id
        service = RoleService(db)
        service.update_role(role)
        return Result.success_msg("更新成功", None)

    # ===================== 3. 删除角色 =====================
@router.delete("/{id}", summary="删除角色")
def delete_role(
        id: int = Path(...),
        db = Depends(get_db)
    ):
        service = RoleService(db)
        service.delete_role(id)
        return Result.success_msg("删除成功", None)

    # ===================== 5. 获取所有角色 =====================
@router.get("/all", summary="获取所有角色")
def get_all_roles(db = Depends(get_db)):
        service = RoleService(db)
        roles = service.get_all_roles()
        #   用带数据的方法：success_data(数据, 提示语)
        return Result.success_data(roles)
    # ===================== 6. 分页查询角色 =====================
@router.get("/page", summary="分页查询角色")
def get_roles_by_page(
        currentPage: int = Query(1),
        pageSize: int = Query(10),
        code: str = "",
        name: str = "",
        db = Depends(get_db)
    ):
        service = RoleService(db)
        page = service.get_roles_by_page(code, name, currentPage, pageSize)
        return Result.success_data(page)
    # ===================== 4. 获取角色信息 =====================
@router.get("/{id}", summary="获取角色信息")
def get_role_by_id(
        id: int = Path(...),
        db = Depends(get_db)
    ):
        service = RoleService(db)
        role = service.get_role_by_id(id)
        #   统一用 success_data
        return Result.success_data(role)
    # ===================== 7. 获取角色的菜单 =====================
@router.get("/{id}/menus", summary="获取角色的菜单")
def get_role_menus(
        id: int = Path(...),
        db = Depends(get_db)
    ):
        service = RoleService(db)
        menus = service.get_role_menus(id)
        return Result.success_data(menus)

    # ===================== 8. 为角色分配菜单 =====================
@router.post("/{id}/menus", summary="为角色分配菜单")
def assign_menus_to_role(
        id: int = Path(...),
        menuIds: List[int] = Body(...),
        db = Depends(get_db)
    ):
        service = RoleService(db)
        service.assign_menus_to_role(id, menuIds)
        return Result.success_msg("菜单分配成功", None)

    # ===================== 9. 获取角色的菜单ID列表 =====================
@router.get("/{id}/menuIds", summary="获取角色的菜单ID列表")
def get_role_menu_ids(
        id: int = Path(...),
        db = Depends(get_db)
    ):
        service = RoleService(db)
        menu_ids = service.get_role_menu_ids(id)
        return Result.success_data(menu_ids)