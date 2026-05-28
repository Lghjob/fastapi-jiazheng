from fastapi import APIRouter, Path, Query, Depends
from utils.result import Result
# 适配你的项目导入
from config.database import  get_db
from service.payment_service import PaymentService

# 路由配置
router = APIRouter(prefix="/payment", tags=["支付管理接口"])

# ===================== 1. 模拟支付 =====================
@router.post("/mock", summary="模拟支付")
def mock_payment(
    orderId: int = Query(...),
    paymentMethod: str = Query(...),
    db = Depends(get_db)
):
    service = PaymentService(db)
    success = service.mock_payment(orderId, paymentMethod)
    
    if success:
        return Result.success_msg("支付成功", None)
    return Result.error_msg("支付失败")

# ===================== 2. 取消支付 =====================
@router.post("/cancel/{orderId}", summary="取消支付")
def cancel_payment(
    orderId: int = Path(...),
    db = Depends(get_db)
):
    service = PaymentService(db)
    service.cancel_payment(orderId)
    return Result.success_msg("取消成功", None)

# ===================== 3. 查询支付状态 =====================
@router.get("/status/{orderId}", summary="查询支付状态")
def get_payment_status(
    orderId: int = Path(...),
    db = Depends(get_db)
):
    service = PaymentService(db)
    data = service.get_payment_status(orderId)
    return Result.success_data(data)