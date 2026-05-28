import logging
import time
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

# 导入你项目已有的文件（直接用你写的，不用改）
from schemas.service_order import ServiceOrder
from utils.exceptions.service_exception import ServiceException
from utils.enums.order_status import OrderStatus
from utils.enums.payment_method import PaymentMethod

# 导入 SQLAlchemy Model
from models.service_order_model import ServiceOrderModel

# 日志配置
logger = logging.getLogger(__name__)

class PaymentService:
    def __init__(self, db: Session):
        self.db = db

    # ===================== 核心功能：模拟支付 =====================
    def mock_payment(self, order_id: int, payment_method: str) -> bool:
        """
        模拟支付
        """
        logger.info(f"开始模拟支付: orderId={order_id}, paymentMethod={payment_method}")

        try:
            # 1. 查询订单
            order = self.db.get(ServiceOrderModel, order_id)
            if not order:
                raise ServiceException("订单不存在")

            # 2. 检查订单状态（必须是待支付）
            # 适配你现有的枚举类：get_value() 是方法，带括号
            if order.order_status != OrderStatus.WAITING_PAY.get_value():
                status_enum = OrderStatus.get_by_value(order.order_status)
                status_desc = status_enum.get_desc() if status_enum else "未知"
                raise ServiceException(f"订单状态不正确，当前状态：{status_desc}")

            # 3. 验证支付方式
            # 适配你现有的枚举类：get_by_code() 是方法
            method = PaymentMethod.get_by_code(payment_method)
            if not method:
                raise ServiceException("不支持的支付方式")

            # 4. 模拟支付处理（模拟网络延迟 1秒）
            time.sleep(1)
            logger.info(f"模拟支付成功: orderId={order_id}")

            # 5. 更新订单状态
            order.order_status = OrderStatus.WAITING_ACCEPT.get_value()
            order.payment_method = payment_method
            order.payment_time = datetime.now()
            order.paid_amount = order.total_amount
            order.refund_amount = 0.0
            order.refund_status = 0

            self.db.commit()
            logger.info(f"订单支付成功: orderId={order_id}, amount={order.total_amount}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"模拟支付异常: {str(e)}")
            if isinstance(e, ServiceException):
                raise e
            else:
                raise ServiceException("支付处理异常")

    # ===================== 取消支付 =====================
    def cancel_payment(self, order_id: int) -> None:
        """
        取消支付
        """
        logger.info(f"取消支付: orderId={order_id}")

        try:
            order = self.db.get(ServiceOrderModel, order_id)
            if not order:
                raise ServiceException("订单不存在")

            # 适配你现有的枚举类：get_value() 带括号
            if order.order_status != OrderStatus.WAITING_PAY.get_value():
                raise ServiceException("只能取消待支付的订单")

            # 更新订单状态为已取消
            order.order_status = OrderStatus.CANCELLED.get_value()
            order.cancel_reason = "用户取消支付"
            order.cancel_time = datetime.now()

            self.db.commit()
            logger.info(f"取消支付成功: orderId={order_id}")
        except Exception as e:
            self.db.rollback()
            raise e

    # ===================== 查询支付状态 =====================
    def get_payment_status(self, order_id: int) -> ServiceOrder:
        """
        查询支付状态
        """
        order = self.db.get(ServiceOrderModel, order_id)
        if not order:
            raise ServiceException("订单不存在")
        return ServiceOrder.model_validate(order, from_attributes=True)