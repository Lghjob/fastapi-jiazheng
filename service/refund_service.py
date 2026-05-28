import logging
import time
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import desc

# Schema
from schemas.order_refund import OrderRefund
from schemas.service_order import ServiceOrder
from schemas.user import User
from schemas.service_staff import ServiceStaff
from schemas.service_item import ServiceItem

# 异常 & 枚举
from utils.exceptions.service_exception import ServiceException
from utils.enums.order_status import OrderStatus
from utils.enums.refund_status import RefundStatus

# 数据库模型
from models.order_refund_model import OrderRefundModel
from models.service_order_model import ServiceOrderModel
from models.user_model import UserModel
from models.service_staff_model import ServiceStaffModel
from models.service_item_model import ServiceItemModel

logger = logging.getLogger(__name__)

class RefundService:
    def __init__(self, db: Session):
        self.db = db

    # ===================== 申请退款 =====================
    def apply_refund(self, order_id: int, user_id: int, refund_reason: str, refund_type: int) -> OrderRefund:
        logger.info(f"申请退款: orderId={order_id}, userId={user_id}")

        try:
            order = self.db.get(ServiceOrderModel, order_id)
            if not order:
                raise ServiceException("订单不存在")

            if order.user_id != user_id:
                raise ServiceException("无权操作此订单")

            if order.order_status == OrderStatus.WAITING_PAY.get_value():
                raise ServiceException("待支付订单无需退款，可直接取消")
            if order.order_status == OrderStatus.COMPLETED.get_value():
                raise ServiceException("已完成的订单不支持退款")
            if order.order_status == OrderStatus.CANCELLED.get_value():
                raise ServiceException("订单已取消")

            if not order.payment_time:
                raise ServiceException("订单未支付，无需退款")

            existing_refund = self.db.query(OrderRefundModel)\
                .filter(
                    OrderRefundModel.order_id == order_id,
                    OrderRefundModel.refund_status.in_([
                        RefundStatus.PENDING_AUDIT.get_value(),
                        RefundStatus.AUDIT_PASSED.get_value(),
                        RefundStatus.REFUNDING.get_value(),
                        RefundStatus.REFUNDED.get_value()
                    ])
                ).first()

            if existing_refund:
                raise ServiceException("该订单已有退款申请，请勿重复提交")

            refund = OrderRefundModel(
                order_id=order_id,
                user_id=user_id,
                refund_amount=order.paid_amount,
                refund_reason=refund_reason,
                refund_status=RefundStatus.PENDING_AUDIT.get_value(),
                refund_type=refund_type,
                create_time=datetime.now(),
                update_time=datetime.now()
            )
            self.db.add(refund)
            order.refund_status = 1
            self.db.commit()

            logger.info(f"退款申请创建成功: refundId={refund.id}, orderId={order_id}")
            return OrderRefund.model_validate(refund.__dict__)

        except Exception as e:
            self.db.rollback()
            raise e

    # ===================== 审核退款 =====================
    def audit_refund(self, refund_id: int, audit_user_id: int, audit_result: int, audit_remark: str) -> None:
        logger.info(f"审核退款: refundId={refund_id}, auditResult={audit_result}")

        try:
            refund = self.db.get(OrderRefundModel, refund_id)
            if not refund:
                raise ServiceException("退款记录不存在")

            if refund.refund_status != RefundStatus.PENDING_AUDIT.get_value():
                raise ServiceException("该退款申请已处理")

            refund.audit_user_id = audit_user_id
            refund.audit_time = datetime.now()
            refund.audit_remark = audit_remark

            if audit_result == RefundStatus.AUDIT_PASSED.get_value():
                refund.refund_status = RefundStatus.AUDIT_PASSED.get_value()
                self.db.commit()
                self._process_refund(refund_id)

            elif audit_result == RefundStatus.AUDIT_REJECTED.get_value():
                refund.refund_status = RefundStatus.AUDIT_REJECTED.get_value()
                order = self.db.get(ServiceOrderModel, refund.order_id)
                if order:
                    order.refund_status = 3
                self.db.commit()
                logger.info(f"退款审核拒绝: refundId={refund_id}")

            else:
                raise ServiceException("无效的审核结果")

        except Exception as e:
            self.db.rollback()
            raise e

    # ===================== 处理退款 =====================
    def _process_refund(self, refund_id: int) -> None:
        logger.info(f"开始处理退款: refundId={refund_id}")

        try:
            refund = self.db.get(OrderRefundModel, refund_id)
            if not refund:
                raise ServiceException("退款记录不存在")

            refund.refund_status = RefundStatus.REFUNDING.get_value()
            self.db.commit()
            time.sleep(1)

            refund.refund_status = RefundStatus.REFUNDED.get_value()
            refund.refund_time = datetime.now()

            order = self.db.get(ServiceOrderModel, refund.order_id)
            if order:
                order.order_status = OrderStatus.CANCELLED.get_value()
                order.refund_status = 2
                order.refund_amount = refund.refund_amount
                order.cancel_reason = "退款成功"
                order.cancel_time = datetime.now()

            self.db.commit()
            logger.info(f"退款处理成功: refundId={refund_id}, amount={refund.refund_amount}")

        except Exception as e:
            self.db.rollback()
            logger.error(f"退款处理异常: {str(e)}")
            refund = self.db.get(OrderRefundModel, refund_id)
            if refund:
                refund.refund_status = RefundStatus.REFUND_FAILED.get_value()
                self.db.commit()
            raise ServiceException("退款处理失败")

    # ===================== 查询退款详情 =====================
    def get_refund_detail(self, refund_id: int) -> OrderRefund:
        refund = self.db.get(OrderRefundModel, refund_id)
        if not refund:
            raise ServiceException("退款记录不存在")

        refund_Schema = OrderRefund.model_validate(refund.__dict__)
        self._fill_refund_info(refund_Schema)
        return refund_Schema

    # ===================== 退款列表 =====================
    def get_refund_list(
        self,
        user_id: Optional[int],
        refund_status: Optional[int],
        page_num: int,
        page_size: int
    ):
        query = self.db.query(OrderRefundModel)

        if user_id:
            query = query.filter(OrderRefundModel.user_id == user_id)
        if refund_status is not None:
            query = query.filter(OrderRefundModel.refund_status == refund_status)

        query = query.order_by(desc(OrderRefundModel.create_time))
        total = query.count()
        offset = (page_num - 1) * page_size
        records = query.offset(offset).limit(page_size).all()

        refund_list = [OrderRefund.model_validate(r.__dict__) for r in records]
        self._fill_refund_info_list(refund_list)

        return {
            "records": refund_list,
            "total": total,
            "page_num": page_num,
            "page_size": page_size
        }

    # ===================== 填充关联信息 =====================
    def _fill_refund_info(self, refund: OrderRefund) -> None:
        if not refund:
            return

        if refund.order_id:
            order = self.db.get(ServiceOrderModel, refund.order_id)
            if order:
                order_Schema = ServiceOrder.model_validate(order.__dict__)
                if order.staff_id:
                    staff = self.db.get(ServiceStaffModel, order.staff_id)
                    if staff:
                        staff_Schema = ServiceStaff.model_validate(staff.__dict__)
                        if staff.user_id:
                            staff_user = self.db.get(UserModel, staff.user_id)
                            if staff_user:
                                staff_Schema.user = User.model_validate(staff_user.__dict__)
                        order_Schema.staff = staff_Schema

                if order.service_id:
                    service_item = self.db.get(ServiceItemModel, order.service_id)
                    if service_item:
                        order_Schema.service_item = ServiceItem.model_validate(service_item.__dict__)

                refund.order = order_Schema

        if refund.user_id:
            user = self.db.get(UserModel, refund.user_id)
            if user:
                refund.user = User.model_validate(user.__dict__)

        if refund.audit_user_id:
            audit_user = self.db.get(UserModel, refund.audit_user_id)
            if audit_user:
                refund.audit_user = User.model_validate(audit_user.__dict__)

    def _fill_refund_info_list(self, refunds: List[OrderRefund]) -> None:
        if not refunds:
            return

        order_ids = [r.order_id for r in refunds if r.order_id]
        user_ids = [r.user_id for r in refunds if r.user_id]
        audit_user_ids = [r.audit_user_id for r in refunds if r.audit_user_id]

        orders = {}
        if order_ids:
            order_list = self.db.query(ServiceOrderModel)\
                .filter(ServiceOrderModel.id.in_(order_ids))\
                .all()
            orders = {o.id: ServiceOrder.model_validate(o.__dict__) for o in order_list}

            staff_ids = [o.staff_id for o in orders.values() if o.staff_id]
            service_item_ids = [o.service_id for o in orders.values() if o.service_id]

            staffs = {}
            if staff_ids:
                staff_list = self.db.query(ServiceStaffModel)\
                    .filter(ServiceStaffModel.id.in_(staff_ids))\
                    .all()
                staffs = {s.id: ServiceStaff.model_validate(s.__dict__) for s in staff_list}

                staff_user_ids = [s.user_id for s in staffs.values() if s.user_id]
                staff_users = {}
                if staff_user_ids:
                    staff_user_list = self.db.query(UserModel)\
                        .filter(UserModel.id.in_(staff_user_ids))\
                        .all()
                    staff_users = {u.id: User.model_validate(u.__dict__) for u in staff_user_list}

                for staff in staffs.values():
                    if staff.user_id and staff.user_id in staff_users:
                        staff.user = staff_users[staff.user_id]

            service_items = {}
            if service_item_ids:
                service_item_list = self.db.query(ServiceItemModel)\
                    .filter(ServiceItemModel.id.in_(service_item_ids))\
                    .all()
                service_items = {s.id: ServiceItem.model_validate(s.__dict__) for s in service_item_list}

            for order in orders.values():
                if order.staff_id and order.staff_id in staffs:
                    order.staff = staffs[order.staff_id]
                if order.service_id and order.service_id in service_items:
                    order.service_item = service_items[order.service_id]

        all_user_ids = list(set(user_ids + audit_user_ids))
        users = {}
        if all_user_ids:
            user_list = self.db.query(UserModel)\
                .filter(UserModel.id.in_(all_user_ids))\
                .all()
            users = {u.id: User.model_validate(u.__dict__) for u in user_list}

        for refund in refunds:
            if refund.order_id and refund.order_id in orders:
                refund.order = orders[refund.order_id]
            if refund.user_id and refund.user_id in users:
                refund.user = users[refund.user_id]
            if refund.audit_user_id and refund.audit_user_id in users:
                refund.audit_user = users[refund.audit_user_id]