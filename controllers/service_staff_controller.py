from fastapi import APIRouter, Path, Query, Body, Depends
from typing import Optional
from decimal import Decimal
from utils.result import Result
from config.database import get_db
from schemas.service_staff import ServiceStaff
from service.service_staff_service import ServiceStaffService

router = APIRouter(prefix="/staff", tags=["服务人员管理接口"])

# ===================== 1. 创建服务人员 =====================
@router.post("/create", summary="创建服务人员")
def create_service_staff(
    staff: ServiceStaff = Body(...),
    db = Depends(get_db)
):
    service = ServiceStaffService(db)
    service.create_service_staff(staff)
    return Result.success_msg("创建成功", None)

# ===================== 2. 删除服务人员 =====================
@router.delete("/{id}", summary="删除服务人员")
def delete_service_staff(
    id: int = Path(...),
    db = Depends(get_db)
):
    service = ServiceStaffService(db)
    service.delete_service_staff(id)
    return Result.success_msg("删除成功", None)

# ===================== 3. 更新服务人员信息 =====================
@router.put("/update", summary="更新服务人员信息")
def update_service_staff(
    staff: ServiceStaff = Body(...),
    db = Depends(get_db)
):
    service = ServiceStaffService(db)
    service.update_service_staff(staff)
    return Result.success_msg("更新成功", None)

# ===================== 5. 获取服务人员列表（分页） =====================
@router.get("/list", summary="获取服务人员列表")
def get_service_staff_list(
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    name: Optional[str] = Query(None),
    serviceType: Optional[str] = Query(None),
    minRating: Optional[float] = Query(None),
    db = Depends(get_db)
):
    service = ServiceStaffService(db)
    data = service.get_service_staffs_by_page(
        name, serviceType, pageNum, pageSize, minRating
    )
    return Result.success_data(data)

# ===================== 7. 获取评分前10的服务人员 =====================
@router.get("/top-rated", summary="获取评分前10的服务人员")
def get_top_rated_staff(
    db = Depends(get_db)
):
    service = ServiceStaffService(db)
    data = service.get_top_rated_staff()
    return Result.success_data(data)

# ===================== 8. 获取可提供指定服务的服务人员 =====================
@router.get("/available", summary="获取可提供指定服务的服务人员")
def get_available_staff(
    serviceId: int = Query(...),
    db = Depends(get_db)
):
    service = ServiceStaffService(db)
    data = service.get_available_staff_by_service_item(serviceId)
    return Result.success_data(data)

# ===================== 4. 获取服务人员详情 =====================
@router.get("/{id}", summary="获取服务人员详情")
def get_service_staff(
    id: int = Path(...),
    db = Depends(get_db)
):
    service = ServiceStaffService(db)
    data = service.get_service_staff_by_id(id)
    return Result.success_data(data)


# ===================== 6. 根据用户ID查询服务人员信息 =====================
@router.get("/user/{userId}", summary="根据用户ID查询服务人员信息")
def get_service_staff_by_user_id(
    userId: int = Path(...),
    db = Depends(get_db)
):
    service = ServiceStaffService(db)
    data = service.get_service_staff_by_user_id(userId)
    return Result.success_data(data)


