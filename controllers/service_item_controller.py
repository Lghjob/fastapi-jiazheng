from fastapi import APIRouter, Path, Query, Body, Depends
from utils.result import Result
from config.database import get_db
from schemas.service_item import ServiceItem
from service.service_item_service import ServiceItemService
from typing import Optional

# 路由配置
router = APIRouter(prefix="/service", tags=["服务项目管理接口"])

# ===================== 1. 创建服务项目 =====================
@router.post("", summary="创建服务项目")
def create_service_item(
    item: ServiceItem = Body(...),
    db=Depends(get_db)
):
    service = ServiceItemService(db)
    service.create_service_item(item)
    return Result.success_msg("创建成功", None)

# ===================== 4. 获取服务项目列表（分页） =====================
@router.get("/list", summary="获取服务项目列表")
def get_service_item_list(
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    title: str = Query(None),
    categoryId: str = Query(""),  # 正确
    status: str = Query(""),      # 正确
    db=Depends(get_db)
):
    service = ServiceItemService(db)
    data = service.get_service_items_by_page(
        title, categoryId, status, pageNum, pageSize
    )
    return Result.success_data(data)

# ===================== 7. 获取类别下的所有服务项目 =====================
@router.get("/category/{categoryId}", summary="获取类别下的所有服务项目")
def get_service_items_by_category(
    categoryId: int = Path(...),  # 这里必须是 int！不能是 str
    db=Depends(get_db)
):
    service = ServiceItemService(db)
    data = service.get_service_items_by_category(categoryId)
    return Result.success_data(data)

# ===================== 5. 删除服务项目 =====================
@router.delete("/{id}", summary="删除服务项目")
def delete_service_item(
    id: int = Path(...),
    db=Depends(get_db)
):
    service = ServiceItemService(db)
    service.delete_service_item(id)
    return Result.success_msg("删除成功", None)

# ===================== 6. 修改服务项目状态 =====================
@router.put("/{id}/status", summary="修改服务项目状态")
def update_status(
    id: int = Path(...),
    status: int = Query(...),
    db=Depends(get_db)
):
    service = ServiceItemService(db)
    service.update_status(id, status)
    return Result.success_msg("状态修改成功", None)

# ===================== 2. 更新服务项目 =====================
@router.put("/{id}", summary="更新服务项目")
def update_service_item(
    id: int = Path(...),
    item: ServiceItem = Body(...),
    db=Depends(get_db)
):
    item.id = id
    service = ServiceItemService(db)
    service.update_service_item(item)
    return Result.success_msg("更新成功", None)

# ===================== 3. 获取服务项目详情 =====================
@router.get("/{id}", summary="获取服务项目详情")
def get_service_item(
    id: int = Path(...),
    db=Depends(get_db)
):
    service = ServiceItemService(db)
    data = service.get_service_item_by_id(id)
    return Result.success_data(data)