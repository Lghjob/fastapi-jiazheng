from fastapi import APIRouter, Query, Depends
from typing import List, Optional
from utils.result import Result
# 统一项目导入规范
from config.database import  get_db
from schemas.staff_service_item import StaffServiceItem
from service.staff_service_item_service import StaffServiceItemService

# 路由配置
router = APIRouter(
    prefix="/staff/service-items",
    tags=["服务人员服务项目接口"]
)

# ===================== 1. 添加服务项目 =====================
@router.post("/add", summary="添加服务项目")
def add_service_item(
    staffId: int = Query(..., description="服务人员ID不能为空"),
    serviceId: int = Query(..., description="服务项目ID不能为空"),
    db = Depends(get_db)
):
    service = StaffServiceItemService(db)
    service.add_service_item(staffId, serviceId)
    return Result.success_msg("添加成功", None)

# ===================== 2. 批量添加服务项目 =====================
@router.post("/batch-add", summary="批量添加服务项目")
def batch_add_service_items(
    staffId: int = Query(..., description="服务人员ID不能为空"),
    serviceIds: List[int] = Query(..., description="服务项目ID列表不能为空"),
    db = Depends(get_db)
):
    service = StaffServiceItemService(db)
    service.batch_add_service_items(staffId, serviceIds)
    return Result.success_msg("添加成功", None)

# ===================== 3. 移除服务项目 =====================
@router.post("/remove", summary="移除服务项目")
def remove_service_item(
    staffId: int = Query(..., description="服务人员ID不能为空"),
    serviceId: int = Query(..., description="服务项目ID不能为空"),
    db = Depends(get_db)
):
    service = StaffServiceItemService(db)
    service.remove_service_item(staffId, serviceId)
    return Result.success_msg("移除成功", None)

# ===================== 4. 批量移除服务项目 =====================
@router.post("/batch-remove", summary="批量移除服务项目")
def batch_remove_service_items(
    staffId: int = Query(..., description="服务人员ID不能为空"),
    serviceIds: List[int] = Query(..., description="服务项目ID列表不能为空"),
    db = Depends(get_db)
):
    service = StaffServiceItemService(db)
    service.batch_remove_service_items(staffId, serviceIds)
    return Result.success_msg("移除成功", None)

# ===================== 5. 更新服务项目状态 =====================
@router.post("/update-status", summary="更新服务项目状态")
def update_service_item_status(
    staffId: int = Query(..., description="服务人员ID不能为空"),
    serviceId: int = Query(..., description="服务项目ID不能为空"),
    status: int = Query(..., description="状态不能为空"),
    db = Depends(get_db)
):
    service = StaffServiceItemService(db)
    service.update_service_item_status(staffId, serviceId, status)
    return Result.success_msg("更新成功", None)

# ===================== 6. 获取服务项目列表 =====================
@router.get("/list", summary="获取服务项目列表")
def get_service_items(
    staffId: int = Query(..., description="服务人员ID不能为空"),
    db = Depends(get_db)
):
    service = StaffServiceItemService(db)
    items = service.get_service_items(staffId)
    return Result.success_data(items)

# ===================== 7. 分配服务项目（先删后增） =====================
@router.post("/assign", summary="分配服务项目")
def assign_service_items(
    staffId: int = Query(..., description="服务人员ID不能为空"),
    serviceIds: str = Query(..., description="服务项目ID，逗号分隔 1,2,3"),  
    status: int = Query(1, description="服务状态，默认1"),
    db = Depends(get_db)
):
    # 自动把字符串转成整数列表
    service_ids_list = [int(i.strip()) for i in serviceIds.split(",") if i.strip()]

    service = StaffServiceItemService(db)

    # 1. 移除原有
    existing_items = service.get_service_items(staffId)
    if existing_items:
        existing_ids = [item.service_id for item in existing_items]
        service.batch_remove_service_items(staffId, existing_ids)

    # 2. 添加新的（用转换后的 service_ids_list）
    if service_ids_list:
        service.batch_add_service_items(staffId, service_ids_list)
        if status != 1:
            for service_id in service_ids_list:
                service.update_service_item_status(staffId, service_id, status)

    return Result.success_msg("分配成功", None)