from fastapi import APIRouter, Path, Query, Body, Depends
from typing import List, Optional, Annotated
from datetime import datetime
from utils.result import Result
# 统一项目导入规范
from config.database import  get_db
from schemas.service_order import ServiceOrder
from service.service_order_service import ServiceOrderService
from pydantic import BeforeValidator

# 路由配置
router = APIRouter(prefix="/order", tags=["订单管理接口"])

# ===================== 1. 创建订单 =====================
@router.post("", summary="创建订单")
def create_order(
    order: ServiceOrder = Body(...),
    db = Depends(get_db)
):
    service = ServiceOrderService(db)
    service.create_order(order)
    return Result.success_msg("创建成功", order)


# ===================== 4. 获取订单列表 =====================
from fastapi import Query, Depends
from typing import Optional, Union

# 关键：把参数类型改成 Union[str, None]，手动转！
# 这样就能接收 "" 空字符串
@router.get("/list", summary="获取订单列表")
def get_order_list(
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    userId: Union[str, None] = Query(None),  # 这里改 str
    staffId: Union[str, None] = Query(None), # 这里改 str
    status: Union[str, None] = Query(None),  # 这里改 str
    db = Depends(get_db)
):
    # 自动把空字符串、空白 转成 None
    def to_int_or_none(val):
        if val is None or val.strip() == "":
            return None
        try:
            return int(val)
        except:
            return None

    # 转换
    userId = to_int_or_none(userId)
    staffId = to_int_or_none(staffId)
    status = to_int_or_none(status)

    service = ServiceOrderService(db)
    data = service.get_orders_by_page(userId, staffId, status, pageNum, pageSize)
    return Result.success_data(data)
# ===================== 5. 按时间段获取订单列表 =====================
@router.get("/list/time", summary="按时间段获取订单列表")
def get_order_list_by_time(
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    userId: Optional[int] = Query(None),
    staffId: Optional[int] = Query(None),
    status: Optional[int] = Query(None),
    startTime: Optional[str] = Query(None),
    endTime: Optional[str] = Query(None),
    db = Depends(get_db)
):
    # 时间格式化：yyyy-MM-dd HH:mm:ss
    formatter = "%Y-%m-%d %H:%M:%S"
    start = None
    end = None

    try:
        if startTime:
            start = datetime.strptime(startTime, formatter)
        if endTime:
            end = datetime.strptime(endTime, formatter)
    except ValueError:
        return Result.error_msg("日期格式错误，请使用yyyy-MM-dd HH:mm:ss格式")

    service = ServiceOrderService(db)
    
    # 参数顺序 100% 对齐
    data = service.get_orders_by_page(
        userId, staffId, status, 
        pageNum, pageSize,  # 页码必须放时间前面
        start, end
    )
    
    return Result.success_data(data)
# ===================== 8. 批量删除订单 =====================
@router.delete("/batch", summary="批量删除订单")
def batch_delete_orders(
    ids: List[int] = Body(...),
    db = Depends(get_db)
):
    service = ServiceOrderService(db)
    service.batch_delete_orders(ids)
    return Result.success_msg("批量删除成功", None)

# ===================== 7. 删除订单 =====================
@router.delete("/{id}", summary="删除订单")
def delete_order(
    id: int = Path(...),
    db = Depends(get_db)
):
    service = ServiceOrderService(db)
    service.delete_order(id)
    return Result.success_msg("订单删除成功", None)

# ===================== 2. 更新订单状态 =====================
@router.put("/{id}/status", summary="更新订单状态")
def update_order_status(
    id: int = Path(...),
    status: int = Query(...),
    reason: Optional[str] = Query(None),
    db = Depends(get_db)
):
    service = ServiceOrderService(db)
    service.update_order_status(id, status, reason)
    return Result.success_msg("状态更新成功", None)

# ===================== 6. 取消订单 =====================
@router.put("/{id}/cancel", summary="取消订单")
def cancel_order(
    id: int = Path(...),
    reason: str = Query(...),
    db = Depends(get_db)
):
    service = ServiceOrderService(db)
    service.cancel_order(id, reason)
    return Result.success_msg("订单取消成功", None)

# ===================== 3. 获取订单详情 =====================
@router.get("/{id}", summary="获取订单详情")
def get_order(
    id: int = Path(...),
    db = Depends(get_db)
):
    service = ServiceOrderService(db)
    data = service.get_order_by_id(id)
    return Result.success_data(data)

