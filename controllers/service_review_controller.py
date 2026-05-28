from fastapi import APIRouter, Path, Query, Body, Depends
from typing import Optional, Union # 导入 Union
from utils.result import Result
from config.database import get_db
from schemas.service_review import ServiceReview
from service.service_review_service import ServiceReviewService

router = APIRouter(prefix="/review", tags=["评价管理接口"])

# ===================== 创建评价 =====================
@router.post("", summary="创建评价")
def create_review(
    review: ServiceReview = Body(...),
    db = Depends(get_db)
):
    service = ServiceReviewService(db)
    service.create_review(review)
    return Result.success_msg("评价成功", None)

# ===================== 删除评价 =====================
@router.delete("/{id}", summary="删除评价")
def delete_review(
    id: int = Path(...),
    db = Depends(get_db)
):
    service = ServiceReviewService(db)
    service.delete_review(id)
    return Result.success_msg("删除成功", None)

# ===================== 评价列表（分页）=====================
@router.get("/list", summary="获取评价列表")
def get_review_list(
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    # 1. 类型改为 Union[str, None]，兼容空字符串
    userId: Union[str, None] = Query(None),
    staffId: Union[str, None] = Query(None),
    orderId: Union[str, None] = Query(None),
    db = Depends(get_db)
):
    # 2. 辅助函数：空字符串转 None，有效字符串转 int
    def to_int_or_none(val):
        if val is None or str(val).strip() == "":
            return None
        try:
            return int(val)
        except:
            return None

    # 3. 手动转换参数
    userId = to_int_or_none(userId)
    staffId = to_int_or_none(staffId)
    orderId = to_int_or_none(orderId)

    service = ServiceReviewService(db)
    data = service.get_reviews_by_page(userId, staffId, orderId, pageNum, pageSize)
    return Result.success_data(data)

# ===================== 获取服务人员评价列表 =====================
@router.get("/staff/{staffId}", summary="获取服务人员评价列表")
def get_staff_reviews(
    staffId: int = Path(...),
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    db = Depends(get_db)
):
    service = ServiceReviewService(db)
    data = service.get_reviews_by_page(None, staffId, None, pageNum, pageSize)
    return Result.success_data(data)

# ===================== 获取用户评价列表 =====================
@router.get("/user/{userId}", summary="获取用户评价列表")
def get_user_reviews(
    userId: int = Path(...),
    pageNum: int = Query(1),
    pageSize: int = Query(10),
    db = Depends(get_db)
):
    service = ServiceReviewService(db)
    data = service.get_reviews_by_page(userId, None, None, pageNum, pageSize)
    return Result.success_data(data)

# ===================== 根据订单ID+用户ID查询评价 =====================
@router.get("/order/{orderId}/user/{userId}", summary="根据订单id和用户id查询评价")
def get_review_by_order_and_user(
    orderId: int = Path(...),
    userId: int = Path(...),
    db = Depends(get_db)
):
    service = ServiceReviewService(db)
    page = service.get_reviews_by_page(userId, None, orderId, 1, 1)
    records = page.get("records", [])
    return Result.success_data(records[0] if records else None)

# ===================== 获取评价详情 =====================
@router.get("/{id}", summary="获取评价详情")
def get_review(
    id: int = Path(...),
    db = Depends(get_db)
):
    service = ServiceReviewService(db)
    data = service.get_review_by_id(id)
    return Result.success_data(data)