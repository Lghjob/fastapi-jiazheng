from fastapi import APIRouter, Path, Query, Body, Depends
from typing import List, Optional
from utils.result import Result
# 统一项目导入规范
from config.database import  get_db
from schemas.service_category import ServiceCategory
from service.service_category_service import ServiceCategoryService

# 路由配置
router = APIRouter(prefix="/category", tags=["服务类别管理接口"])

# ===================== 1. 创建服务类别 =====================
@router.post("/create", summary="创建服务类别")
def create_category(
    category: ServiceCategory = Body(...),
    db = Depends(get_db)
):
    service = ServiceCategoryService(db)
    service.create_category(category)
    return Result.success_msg("创建成功", None)

# ===================== 2. 更新服务类别 =====================
@router.put("/update", summary="更新服务类别")
def update_category(
    category: ServiceCategory = Body(...),
    db = Depends(get_db)
):
    service = ServiceCategoryService(db)
    service.update_category(category)
    return Result.success_msg("更新成功", None)

# ===================== 4. 获取服务类别树 =====================
@router.get("/tree", summary="获取服务类别树")
def get_category_tree(db = Depends(get_db)):
    service = ServiceCategoryService(db)
    data = service.get_category_tree()
    return Result.success_data(data)


# ===================== 6. 获取子类别列表 =====================
@router.get("/children/{parentId}", summary="获取子类别列表")
def get_child_categories(
    parentId: int = Path(...),
    db = Depends(get_db)
):
    service = ServiceCategoryService(db)
    data = service.get_child_categories(parentId)
    return Result.success_data(data)

# ===================== 7. 获取服务类别分页列表 =====================
@router.get("/page", summary="获取服务类别分页列表")
def get_category_list(
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    categoryName: Optional[str] = Query(""),
    status: Optional[str] = Query(""), 
    db = Depends(get_db)
):
    service = ServiceCategoryService(db)
    data = service.get_categories_by_page(categoryName, status, pageNum, pageSize)
    return Result.success_data(data)

# ===================== 8. 批量删除服务类别 =====================
@router.delete("/batch", summary="批量删除服务类别")
def batch_delete_categories(
    ids: List[int] = Body(...),
    db = Depends(get_db)
):
    service = ServiceCategoryService(db)
    service.batch_delete_categories(ids)
    return Result.success_msg("批量删除成功", None)

# ===================== 3. 获取服务类别详情 =====================
@router.get("/{id}", summary="获取服务类别详情")
def get_category(
    id: int = Path(...),
    db = Depends(get_db)
):
    service = ServiceCategoryService(db)
    data = service.get_category_by_id(id)
    return Result.success_data(data)

# ===================== 5. 删除服务类别 =====================
@router.delete("/{id}", summary="删除服务类别")
def delete_category(
    id: int = Path(...),
    db = Depends(get_db)
):
    service = ServiceCategoryService(db)
    service.delete_category(id)
    return Result.success_msg("删除成功", None)
