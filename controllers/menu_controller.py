from fastapi import APIRouter, Path, Query, Body, Depends
from typing import List
from utils.result import Result
from config.database import  get_db
# 从你的项目导入核心依赖（完全匹配你的目录）
from schemas.menu import Menu
from schemas.user import User
from service.menu_service import MenuService
from models.user_model import UserModel

# 路由配置
router = APIRouter(prefix="/menu", tags=["菜单管理接口"])

# ===================== 1. 获取指定角色的菜单 =====================
@router.get("/role/{roleCode}", summary="获取指定角色的菜单")
def get_menus_by_role(
    roleCode: str = Path(...),
    db = Depends(get_db)
):
    service = MenuService(db)
    menus = service.get_menus_by_role_code(roleCode)
    return Result.success_data(menus)

# ===================== 2. 保存菜单 =====================
@router.post("", summary="保存菜单")
def save_menu(
    menu: Menu = Body(...),
    db = Depends(get_db)
):
    service = MenuService(db)
    service.save_menu(menu)
    return Result.success_msg("保存成功", None)

# ===================== 3. 更新菜单 =====================
@router.put("/{id}", summary="更新菜单")
def update_menu(
    id: int = Path(...),
    menu: Menu = Body(...),
    db = Depends(get_db)
):
    menu.id = id
    service = MenuService(db)
    service.update_menu(menu)
    return Result.success_msg("更新成功", None)

# ===================== 4. 批量删除菜单 =====================
@router.delete("/batch", summary="批量删除菜单")
def delete_batch(
    ids: List[int] = Query(...),
    db = Depends(get_db)
):
    service = MenuService(db)
    service.delete_batch(ids)
    return Result.success_msg("删除成功", None)



# ===================== 7. 查询所有菜单(树形) =====================
@router.get("", summary="查询所有菜单(树形)")
def find_all(db = Depends(get_db)):
    service = MenuService(db)
    menu_tree = service.get_all_menu_tree()
    return Result.success_data(menu_tree)

# ===================== 8. 分页查询一级菜单 =====================
@router.get("/page", summary="分页查询一级菜单")
def find_parent_menus(
    currentPage: int = Query(1),
    size: int = Query(10),
    db = Depends(get_db)
):
    service = MenuService(db)
    page = service.get_parent_menu_page(currentPage, size)
    return Result.success_data(page)

# ===================== 9. 查询子菜单 =====================
@router.get("/children/{parentId}", summary="查询子菜单")
def find_children_menus(
    parentId: int = Path(...),
    db = Depends(get_db)
):
    service = MenuService(db)
    children = service.get_children_menus(parentId)
    return Result.success_data(children)

# ===================== 10. 获取用户的菜单树 =====================
@router.get("/user/{userId}", summary="获取用户的菜单树")
def get_menu_tree(
    userId: int = Path(...),
    db = Depends(get_db)
):
    user = db.query(UserModel).filter(UserModel.id == userId).first()
    if not user:
        return Result.error_code("-1", "用户不存在")
    
    service = MenuService(db)
    menus = service.get_menus_by_role_code(user.role_code)
    return Result.success_data(menus)

# ===================== 11. 为角色分配菜单 =====================
@router.post("/role/{roleId}", summary="为角色分配菜单")
def assign_menus_to_role(
    roleId: int = Path(...),
    menuIds: List[int] = Body(...),
    db = Depends(get_db)
):
    service = MenuService(db)
    service.assign_menus_to_role(roleId, menuIds)
    return Result.success_data("分配成功")

# ===================== 6. 根据ID查询菜单 =====================
@router.get("/{id}", summary="根据ID查询菜单")
def find_by_id(
    id: int = Path(...),
    db = Depends(get_db)
):
    service = MenuService(db)
    menu = service.get_by_id(id)
    return Result.success_data(menu)

# ===================== 5. 删除菜单 =====================
@router.delete("/{id}", summary="删除菜单")
def delete_by_id(
    id: int = Path(...),
    db = Depends(get_db)
):
    service = MenuService(db)
    service.delete_by_id(id)
    return Result.success_msg("删除成功", None)