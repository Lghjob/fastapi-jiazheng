from fastapi import APIRouter, Path, Query, Depends
from utils.result import Result
# 适配你的项目核心导入
from config.database import  get_db
from schemas.order_refund import OrderRefund
from service.refund_service import RefundService
from typing import Optional 
# 路由配置
router = APIRouter(prefix="/refund", tags=["退款管理接口"])

# ===================== 1. 申请退款 =====================
@router.post("/apply", summary="申请退款")
def apply_refund(
    orderId: int = Query(...),
    userId: int = Query(...),
    refundReason: str = Query(...),
    refundType: int = Query(1),
    db = Depends(get_db)
):
    service = RefundService(db)
    refund = service.apply_refund(orderId, userId, refundReason, refundType)
    return Result.success_msg("退款申请已提交", refund)

# ===================== 2. 审核退款 =====================
@router.post("/audit/{refundId}", summary="审核退款")
def audit_refund(
    refundId: int = Path(...),
    auditUserId: int = Query(...),
    auditResult: int = Query(...),
    auditRemark: str = Query(None),
    db = Depends(get_db)
):
    service = RefundService(db)
    service.audit_refund(refundId, auditUserId, auditResult, auditRemark)
    return Result.success_msg("审核完成", None)
# ===================== 4. 退款列表 =====================
@router.get("/list", summary="退款列表")
def ultimate_refund_list(db=Depends(get_db)):
    try:
        service = RefundService(db)
        data = service.get_refund_list(None, None, 1, 10)
        return Result.success_data(data)
    except Exception as e:
        print("❌ 【终极接口】报错：", str(e))
        import traceback
        traceback.print_exc()
        return Result.error_msg(str(e))
# ===================== 3. 查询退款详情 =====================
@router.get("/{refundId}", summary="查询退款详情")
def get_refund_detail(
    refundId: int = Path(...),
    db = Depends(get_db)
):
    service = RefundService(db)
    data = service.get_refund_detail(refundId)
    return Result.success_data(data)

