import logging
from typing import List, Optional, Dict, Set
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import  desc, not_, text

# 导入你项目已有的文件
from schemas.service_order import ServiceOrder
from schemas.user import User
from schemas.service_staff import ServiceStaff
from schemas.service_item import ServiceItem
from schemas.service_category import ServiceCategory
from schemas.service_review import ServiceReview
from schemas.staff_service_item import StaffServiceItem
from utils.exceptions.service_exception import ServiceException
from utils.enums.order_status import OrderStatus

# 导入 SQLAlchemy Model
from models.service_order_model import ServiceOrderModel
from models.user_model import UserModel
from models.service_staff_model import ServiceStaffModel
from models.service_item_model import ServiceItemModel
from models.service_category_model import ServiceCategoryModel
from models.service_review_model import ServiceReviewModel
from models.staff_service_item_model import StaffServiceItemModel

# 日志配置
logger = logging.getLogger(__name__)

class ServiceOrderService:
    def __init__(self, db: Session):
        self.db = db

    # ===================== 核心功能：创建订单 =====================
    def create_order(self, order: ServiceOrder) -> None:
        """
        创建订单
        """
        try:
            # 1. 检查用户是否存在
            user = self.db.get(UserModel, order.user_id)
            if not user:
                raise ServiceException("用户不存在")

            # 2. 检查服务人员是否存在
            staff = self.db.get(ServiceStaffModel, order.staff_id)
            if not staff:
                raise ServiceException("服务人员不存在")

            # 3. 检查服务项目是否存在
            item = self.db.get(ServiceItemModel, order.service_id)
            if not item:
                raise ServiceException("服务项目不存在")

            # 4. 检查服务人员是否提供该服务项目
            staff_service_item = self.db.query(StaffServiceItemModel)\
                .filter(
                    StaffServiceItemModel.staff_id == order.staff_id,
                    StaffServiceItemModel.service_id == order.service_id,
                    StaffServiceItemModel.status == 1
                )\
                .first()
            if not staff_service_item:
                raise ServiceException("该服务人员不提供此服务项目，请重新选择")

            logger.info(f"验证通过：服务人员 {order.staff_id} 提供服务项目 {order.service_id}")

            # 5. 检查服务时间和时长是否有效
            if not order.service_time:
                raise ServiceException("服务时间不能为空")
            if not order.duration or order.duration <= 0:
                raise ServiceException("服务时长无效")

            # 6. 计算服务结束时间
            service_end_time = order.service_time + timedelta(minutes=round(order.duration * 60))

            # 7. 检查同一时间段是否已有其他预约
            # 重叠条件：A开始 < B结束 && B开始 < A结束
            conflicting_orders = self.db.query(ServiceOrderModel)\
                .filter(
                    ServiceOrderModel.staff_id == order.staff_id,
                    ServiceOrderModel.is_deleted == 0,
                    not_(ServiceOrderModel.order_status.in_([
                        OrderStatus.CANCELLED.get_value(),
                        OrderStatus.CLOSED.get_value()
                    ])),
                    # 已有订单的开始时间 < 新订单的结束时间
                    ServiceOrderModel.service_time < service_end_time,
                    # 已有订单的结束时间 > 新订单的开始时间
                    text(f"DATE_ADD(service_time, INTERVAL ROUND(duration * 60) MINUTE) > '{order.service_time}'")
                )\
                .all()

            if conflicting_orders:
                raise ServiceException("该服务人员在所选时间段已被预约，请选择其他时间")

            # 8. 设置初始状态
        #     now = datetime.now()
        # #如果 service_time 只有日期，自动补上当前时分秒
        #     service_time = order.service_time
        #     if service_time and service_time.hour == 0 and service_time.minute == 0:
        #         service_time = datetime.combine(service_time.date(), now.time())

        #     db_order = ServiceOrderModel(
        #         **order.model_dump(exclude_unset=True, exclude={"service_time"}),
        #         service_time=service_time,  # 使用补全后的时间
        #         order_status=OrderStatus.WAITING_PAY.get_value(),
        #         create_time=now,
        #         update_time=now
        #     )
            now = datetime.now()
            db_order = ServiceOrderModel(
                **order.model_dump(exclude_unset=True),
                order_status=OrderStatus.WAITING_PAY.get_value(),
                create_time=now,
                update_time=now
            )
            self.db.add(db_order)

            self.db.commit()
            logger.info(f"创建订单成功: {db_order.id}")
        except Exception as e:
            self.db.rollback()
            raise e
    # ===================== 更新订单状态 =====================
    def update_order_status(self, id: int, status: int, reason: Optional[str] = None) -> None:
        """
        更新订单状态
        """
        try:
            order = self._get_order_by_id(id)

            # 检查状态变更是否合法
            self._check_status_change(order.order_status, status)

            # 更新订单状态
            db_order = self.db.get(ServiceOrderModel, id)
            db_order.order_status = status
            db_order.update_time = datetime.now()

            # 处理特殊状态
            if status == OrderStatus.CANCELLED.get_value():
                db_order.cancel_time = datetime.now()
                db_order.cancel_reason = reason
            elif status == OrderStatus.COMPLETED.get_value():
                db_order.complete_time = datetime.now()

            self.db.commit()

            # 如果订单状态变更为已完成，更新家政人员的订单数量和完成率
            if status == OrderStatus.COMPLETED.get_value():
                try:
                    # 这里假设你有 StaffService，我先注释掉，你可以根据实际情况取消注释
                    # from service.service_staff_service import ServiceStaffService
                    # staff_service = ServiceStaffService(self.db)
                    # staff_service.update_service_staff_orders(order.staff_id)
                    logger.info(f"已更新家政人员订单数量: staffId={order.staff_id}")
                except Exception as e:
                    logger.error(f"更新家政人员订单数量失败: staffId={order.staff_id}", exc_info=e)

            logger.info(f"更新订单状态成功: {id}, status: {status}")
        except Exception as e:
            self.db.rollback()
            raise e

    # ===================== 状态流转校验 =====================
    def _check_status_change(self, current_status: int, new_status: int) -> None:
        """
        检查订单状态变更是否合法
        """
        # 终态订单不能变更状态
        if self._is_terminal_status(current_status):
            raise ServiceException("订单已是终态，不能变更状态")

        # 获取当前状态和新状态的枚举对象
        current = OrderStatus.get_by_value(current_status)
        target = OrderStatus.get_by_value(new_status)
        if not current or not target:
            raise ServiceException("无效的订单状态")

        # 检查状态流转是否合法
        if current == OrderStatus.WAITING_PAY:
            # 待支付状态只能变更为已取消或待接单
            if target not in [OrderStatus.CANCELLED, OrderStatus.WAITING_ACCEPT]:
                raise ServiceException("待支付订单只能取消或支付")
        elif current == OrderStatus.WAITING_ACCEPT:
            # 待接单状态只能变更为已接单或已取消
            if target not in [OrderStatus.ACCEPTED, OrderStatus.CANCELLED]:
                raise ServiceException("待接单订单只能接单或取消")
        elif current == OrderStatus.ACCEPTED:
            # 已接单状态只能变更为服务中或已取消
            if target not in [OrderStatus.IN_SERVICE, OrderStatus.CANCELLED]:
                raise ServiceException("已接单订单只能开始服务或取消")
        elif current == OrderStatus.IN_SERVICE:
            # 服务中状态只能变更为已完成或已取消
            if target not in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
                raise ServiceException("服务中订单只能完成或取消")
        elif current in [OrderStatus.COMPLETED, OrderStatus.CANCELLED, OrderStatus.CLOSED]:
            # 终态订单不能变更状态
            raise ServiceException("订单状态不能变更")
        else:
            raise ServiceException("未知的订单状态")

        # 记录状态变更日志
        logger.info(f"订单状态变更检查通过: {current.get_desc()} -> {target.get_desc()}")

    def _is_terminal_status(self, status: int) -> bool:
        """
        判断是否是终态
        """
        return status in [
            OrderStatus.COMPLETED.get_value(),
            OrderStatus.CANCELLED.get_value(),
            OrderStatus.CLOSED.get_value()
        ]

    # ===================== 查询订单 =====================
    def _get_order_by_id(self, id: int) -> ServiceOrderModel:
        """
        内部方法：获取订单Model
        """
        order = self.db.get(ServiceOrderModel, id)
        if not order:
            raise ServiceException("订单不存在")
        return order

    def get_order_by_id(self, id: int) -> ServiceOrder:
        """
        获取订单详情
        """
        order = self._get_order_by_id(id)
        order_Schema = ServiceOrder.model_validate(order, from_attributes=True)
        self._fill_order_info(order_Schema)
        return order_Schema

    # ===================== 删除订单 =====================
    def delete_order(self, id: int) -> None:
        """
        删除订单（软删除）
        """
        try:
            # 检查订单是否存在
            order = self._get_order_by_id(id)

            # 检查订单状态
            if order.order_status not in [
                OrderStatus.CANCELLED.get_value(),
                OrderStatus.COMPLETED.get_value(),
                OrderStatus.CLOSED.get_value()
            ]:
                raise ServiceException("只能删除已完成、已取消或已关闭的订单")

            # 删除关联的评价记录
            self.db.query(ServiceReviewModel)\
                .filter(ServiceReviewModel.order_id == id)\
                .delete(synchronize_session=False)
            logger.info(f"删除订单相关评价记录: orderId={id}")

            # 执行软删除
            order.is_deleted = 1
            order.update_time = datetime.now()

            self.db.commit()
            logger.info(f"订单软删除成功: {id}")
        except Exception as e:
            self.db.rollback()
            raise e

    def batch_delete_orders(self, ids: List[int]) -> None:
        """
        批量删除订单（软删除）
        """
        if not ids:
            return

        try:
            # 检查订单状态
            orders = self.db.query(ServiceOrderModel)\
                .filter(ServiceOrderModel.id.in_(ids))\
                .all()
            for order in orders:
                if order.order_status not in [
                    OrderStatus.CANCELLED.get_value(),
                    OrderStatus.COMPLETED.get_value(),
                    OrderStatus.CLOSED.get_value()
                ]:
                    raise ServiceException("只能删除已完成、已取消或已关闭的订单")

            # 删除关联的评价记录
            self.db.query(ServiceReviewModel)\
                .filter(ServiceReviewModel.order_id.in_(ids))\
                .delete(synchronize_session=False)
            logger.info(f"批量删除订单相关评价记录: orderIds={ids}")

            # 执行批量软删除
            now = datetime.now()
            for order in orders:
                order.is_deleted = 1
                order.update_time = now

            self.db.commit()
            logger.info(f"批量软删除订单成功: count={len(ids)}")
        except Exception as e:
            self.db.rollback()
            raise ServiceException("批量删除订单失败")

   # ===================== 分页查询 =====================
    def get_orders_by_page(
        self,
        user_id: Optional[int],
        staff_id: Optional[int],
        status: Optional[int],
        page_num: int,
        page_size: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ):
        """
        分页查询订单列表
        """
        query = self.db.query(ServiceOrderModel)

        if user_id:
            query = query.filter(ServiceOrderModel.user_id == user_id)
        if staff_id:
            query = query.filter(ServiceOrderModel.staff_id == staff_id)
        if status is not None:
            query = query.filter(ServiceOrderModel.order_status == status)
        if start_time:
            query = query.filter(ServiceOrderModel.service_time >= start_time)
        if end_time:
            query = query.filter(ServiceOrderModel.service_time <= end_time)

        query = query.filter(ServiceOrderModel.is_deleted == 0)
        query = query.order_by(desc(ServiceOrderModel.create_time))

        total = query.count()
        offset = (page_num - 1) * page_size
        records = query.offset(offset).limit(page_size).all()

        # 填充关联信息
        order_list = [ServiceOrder.model_validate(r.__dict__) for r in records]
        self._fill_order_info_list(order_list)

        return {
            "records": order_list,
            "total": total,
            "current": page_num,
            "size": page_size
        }
    # ===================== 取消订单 =====================
    def cancel_order(self, id: int, reason: str) -> None:
        """
        取消订单
        """
        try:
            order = self._get_order_by_id(id)

            # 检查订单状态是否可以取消
            if self._is_terminal_status(order.order_status):
                raise ServiceException("订单已是终态，不能取消")

            # 更新订单状态为已取消
            db_order = self.db.get(ServiceOrderModel, id)
            db_order.order_status = OrderStatus.CANCELLED.get_value()
            db_order.cancel_time = datetime.now()
            db_order.cancel_reason = reason
            db_order.update_time = datetime.now()

            self.db.commit()

            # 订单取消时，更新家政人员的完成率
            try:
                # 这里假设你有 StaffService，我先注释掉，你可以根据实际情况取消注释
                # from service.service_staff_service import ServiceStaffService
                # staff_service = ServiceStaffService(self.db)
                # staff_service.update_service_staff_orders(order.staff_id)
                logger.info(f"订单取消，已更新家政人员完成率: staffId={order.staff_id}")
            except Exception as e:
                logger.error(f"更新家政人员完成率失败: staffId={order.staff_id}", exc_info=e)

            logger.info(f"订单取消成功: {id}, reason: {reason}")
        except Exception as e:
            self.db.rollback()
            raise e

    # ===================== 私有方法：填充关联信息 =====================
    def _fill_order_info(self, order: ServiceOrder) -> None:
        """
        填充单个订单的关联信息
        """
        if not order:
            return

        # 填充用户信息
        if order.user_id:
            user = self.db.get(UserModel, order.user_id)
            if user:
                order.user = User.model_validate(user.__dict__)

        # 填充服务人员信息
        if order.staff_id:
            staff = self.db.get(ServiceStaffModel, order.staff_id)
            if staff:
                staff_Schema = ServiceStaff.model_validate(staff.__dict__)
                # 填充服务人员的用户信息
                if staff.user_id:
                    staff_user = self.db.get(UserModel, staff.user_id)
                    if staff_user:
                        staff_Schema.user = User.model_validate(staff_user.__dict__)
                order.staff = staff_Schema

        # 填充服务项目信息
        if order.service_id:
            item = self.db.get(ServiceItemModel, order.service_id)
            if item:
                item_Schema = ServiceItem.model_validate(item.__dict__)
                # 填充服务项目类别信息
                if item.category_id:
                    category = self.db.get(ServiceCategoryModel, item.category_id)
                    if category:
                        item_Schema.category = ServiceCategory.model_validate(category.__dict__)
                order.service_item = item_Schema

        # 填充评价信息
        review = self.db.query(ServiceReviewModel)\
            .filter(ServiceReviewModel.order_id == order.id)\
            .first()
        if review:
            order.review = ServiceReview.model_validate(review.__dict__)

    def _fill_order_info_list(self, orders: List[ServiceOrder]) -> None:
        if not orders:
            return

        user_ids: Set[int] = set()
        staff_ids: Set[int] = set()
        item_ids: Set[int] = set()
        order_ids: Set[int] = set()
        for order in orders:
            if order.user_id:
                user_ids.add(order.user_id)
            if order.staff_id:
                staff_ids.add(order.staff_id)
            if order.service_id:
                item_ids.add(order.service_id)
            if order.id:
                order_ids.add(order.id)

        users: Dict[int, User] = {}
        if user_ids:
            user_list = self.db.query(UserModel).filter(UserModel.id.in_(user_ids)).all()
            users = {u.id: User.model_validate(u.__dict__) for u in user_list}

        staffs: Dict[int, ServiceStaff] = {}
        staff_user_ids: Set[int] = set()
        if staff_ids:
            staff_list = self.db.query(ServiceStaffModel).filter(ServiceStaffModel.id.in_(staff_ids)).all()
            staffs = {s.id: ServiceStaff.model_validate(s.__dict__) for s in staff_list}
            for staff in staffs.values():
                if staff.user_id:
                    staff_user_ids.add(staff.user_id)

        staff_users: Dict[int, User] = {}
        if staff_user_ids:
            staff_user_list = self.db.query(UserModel).filter(UserModel.id.in_(staff_user_ids)).all()
            staff_users = {u.id: User.model_validate(u.__dict__) for u in staff_user_list}

        for staff in staffs.values():
            if staff.user_id and staff.user_id in staff_users:
                staff.user = staff_users[staff.user_id]

        items: Dict[int, ServiceItem] = {}
        category_ids: Set[int] = set()
        if item_ids:
            item_list = self.db.query(ServiceItemModel).filter(ServiceItemModel.id.in_(item_ids)).all()
            items = {i.id: ServiceItem.model_validate(i.__dict__) for i in item_list}
            for item in items.values():
                if item.category_id:
                    category_ids.add(item.category_id)

        categories: Dict[int, ServiceCategory] = {}
        if category_ids:
            category_list = self.db.query(ServiceCategoryModel).filter(ServiceCategoryModel.id.in_(category_ids)).all()
            categories = {c.id: ServiceCategory.model_validate(c.__dict__) for c in category_list}

        for item in items.values():
            if item.category_id and item.category_id in categories:
                item.category = categories[item.category_id]

        reviews: Dict[int, ServiceReview] = {}
        if order_ids:
            review_list = self.db.query(ServiceReviewModel).filter(ServiceReviewModel.order_id.in_(order_ids)).all()
            reviews = {r.order_id: ServiceReview.model_validate(r.__dict__) for r in review_list}

        for order in orders:
            if order.user_id and order.user_id in users:
                order.user = users[order.user_id]
            if order.staff_id and order.staff_id in staffs:
                order.staff = staffs[order.staff_id]
            if order.service_id and order.service_id in items:
                order.service_item = items[order.service_id]
            if order.id and order.id in reviews:
                order.review = reviews[order.id]