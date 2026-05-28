import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, not_

# 你的 Pydantic Schema
from schemas.service_staff import ServiceStaff
from schemas.user import User
from schemas.service_order import ServiceOrder
from schemas.service_review import ServiceReview
from schemas.service_category import ServiceCategory
from schemas.staff_service_item import StaffServiceItem

# 你的异常
from utils.exceptions.service_exception import ServiceException

# 你的枚举
from utils.enums.order_status import OrderStatus

# 你的数据库模型
from models.service_staff_model import ServiceStaffModel
from models.user_model import UserModel
from models.service_order_model import ServiceOrderModel
from models.service_review_model import ServiceReviewModel
from models.service_category_model import ServiceCategoryModel
from models.staff_service_item_model import StaffServiceItemModel

logger = logging.getLogger(__name__)


class ServiceStaffService:
    def __init__(self, db: Session):
        self.db = db

    # ===================== 创建服务人员 =====================
    def create_service_staff(self, staff: ServiceStaff) -> None:
        try:
            user = self.db.get(UserModel, staff.user_id)
            if not user:
                raise ServiceException("关联用户不存在")

            existing = self.db.query(ServiceStaffModel) \
                .filter(ServiceStaffModel.user_id == staff.user_id) \
                .first()
            if existing:
                raise ServiceException("该用户已经是服务人员")

            now = datetime.now()
            db_staff = ServiceStaffModel(
                **staff.model_dump(exclude_unset=True),
                rating=Decimal("5.0"),
                total_orders=0,
                completion_rate=Decimal("100.0"),
                create_time=now,
                update_time=now
            )
            self.db.add(db_staff)
            self.db.commit()
            logger.info(f"创建服务人员成功: {db_staff.id}")
        except Exception as e:
            self.db.rollback()
            raise ServiceException(f"创建服务人员失败: {str(e)}")

    # ===================== 更新服务人员 =====================
    def update_service_staff(self, staff: ServiceStaff) -> None:
        try:
            existing = self.db.get(ServiceStaffModel, staff.id)
            if not existing:
                raise ServiceException("服务人员不存在")

            for key, value in staff.model_dump(exclude_unset=True).items():
                setattr(existing, key, value)
            existing.update_time = datetime.now()

            self.db.commit()
            logger.info(f"更新服务人员信息成功: {staff.id}")
        except Exception as e:
            self.db.rollback()
            raise ServiceException("更新服务人员信息失败")

    # ===================== 填充用户信息 =====================
    def fill_user_info(self, staff: ServiceStaff):
        if not staff or not staff.user_id:
            return
        user = self.db.get(UserModel, staff.user_id)
        if user:
            staff.user = User.model_validate(user.__dict__)

    def _fill_user_info_list(self, staff_list: List[ServiceStaff]):
        if not staff_list:
            return
        user_ids = [s.user_id for s in staff_list if s.user_id]
        if not user_ids:
            return

        users = self.db.query(UserModel).filter(UserModel.id.in_(user_ids)).all()
        user_map = {u.id: User.model_validate(u.__dict__) for u in users}
        for s in staff_list:
            s.user = user_map.get(s.user_id)

    # ===================== 填充订单信息 =====================
    def _fill_orders(self, staff: ServiceStaff):
        if not staff or not staff.id:
            return
        orders = self.db.query(ServiceOrderModel) \
            .filter(ServiceOrderModel.staff_id == staff.id) \
            .order_by(desc(ServiceOrderModel.create_time)).all()
        staff.orders = [ServiceOrder.model_validate(o.__dict__) for o in orders]

    def _fill_orders_list(self, staff_list: List[ServiceStaff]):
        if not staff_list:
            return
        staff_ids = [s.id for s in staff_list if s.id]
        if not staff_ids:
            return

        all_orders = self.db.query(ServiceOrderModel) \
            .filter(ServiceOrderModel.staff_id.in_(staff_ids)) \
            .order_by(desc(ServiceOrderModel.create_time)).all()

        order_map = {}
        for o in all_orders:
            if o.staff_id not in order_map:
                order_map[o.staff_id] = []
            order_map[o.staff_id].append(ServiceOrder.model_validate(o.__dict__))

        for s in staff_list:
            s.orders = order_map.get(s.id, [])

    # ===================== 填充评价信息 =====================
    def _fill_reviews(self, staff: ServiceStaff):
        if not staff or not staff.id:
            return
        reviews = self.db.query(ServiceReviewModel) \
            .filter(ServiceReviewModel.staff_id == staff.id) \
            .order_by(desc(ServiceReviewModel.create_time)).all()
        staff.reviews = [ServiceReview.model_validate(r.__dict__) for r in reviews]

    def _fill_reviews_list(self, staff_list: List[ServiceStaff]):
        if not staff_list:
            return
        staff_ids = [s.id for s in staff_list if s.id]
        if not staff_ids:
            return

        all_reviews = self.db.query(ServiceReviewModel) \
            .filter(ServiceReviewModel.staff_id.in_(staff_ids)) \
            .order_by(desc(ServiceReviewModel.create_time)).all()

        review_map = {}
        for r in all_reviews:
            if r.staff_id not in review_map:
                review_map[r.staff_id] = []
            review_map[r.staff_id].append(ServiceReview.model_validate(r.__dict__))

        for s in staff_list:
            s.reviews = review_map.get(s.id, [])

    # ===================== 填充服务类型 =====================
    def _fill_categories(self, staff: ServiceStaff):
        if not staff or not staff.service_type:
            return

        try:
            # 兼容处理：数据库可能是JSON对象，也可能是字符串
            category_ids = staff.service_type
            if isinstance(category_ids, str):
                category_ids = json.loads(category_ids)

            if not isinstance(category_ids, list) or len(category_ids) == 0:
                return

            categories = self.db.query(ServiceCategoryModel) \
                .filter(ServiceCategoryModel.id.in_(category_ids)) \
                .order_by(asc(ServiceCategoryModel.sort_num)).all()

            staff.categories = [ServiceCategory.model_validate(c.__dict__) for c in categories]
        except Exception as e:
            logger.error(f"解析服务类型JSON失败: {staff.service_type}", exc_info=True)
            staff.categories = []

    def _fill_categories_list(self, staff_list: List[ServiceStaff]):
        for s in staff_list:
            self._fill_categories(s)

    # ===================== 填充服务项目 =====================
    def _fill_service_items(self, staff: ServiceStaff):
        if not staff or not staff.id:
            return
        items = self.db.query(StaffServiceItemModel) \
            .filter(StaffServiceItemModel.staff_id == staff.id).all()
        staff.service_items = [StaffServiceItem.model_validate(i.__dict__) for i in items]

    def _fill_service_items_list(self, staff_list: List[ServiceStaff]):
        for s in staff_list:
            self._fill_service_items(s)

    # ===================== 详情 =====================
    def get_service_staff_detail(self, id: int) -> ServiceStaff:
        staff = self.db.get(ServiceStaffModel, id)
        if not staff:
            raise ServiceException("服务人员不存在")

        schema = ServiceStaff.model_validate(staff.__dict__)
        self.fill_user_info(schema)
        self._fill_orders(schema)
        self._fill_reviews(schema)
        self._fill_categories(schema)
        self._fill_service_items(schema)
        return schema

    def get_service_staff_by_id(self, id: int) -> ServiceStaff:
        staff = self.db.query(ServiceStaffModel) \
            .filter(ServiceStaffModel.id == id, ServiceStaffModel.is_deleted == 0).first()
        if not staff:
            raise ServiceException("服务人员不存在")
        schema = ServiceStaff.model_validate(staff.__dict__)
        self.fill_user_info(schema)
        return schema

    def get_service_staff_by_user_id(self, user_id: int) -> ServiceStaff:
        logger.info(f"userId:{user_id}")
        staff = self.db.query(ServiceStaffModel) \
            .filter(ServiceStaffModel.user_id == user_id).first()
        if not staff:
            raise ServiceException("服务人员不存在")
        schema = ServiceStaff.model_validate(staff.__dict__)
        self.fill_user_info(schema)
        return schema

    # ===================== 分页列表=====================
    def get_service_staffs_by_page(
            self,
            name: Optional[str],
            service_type: Optional[str],
            page_num: int,
            page_size: int,
            min_rating: Optional[float] = None,
            with_orders: bool = False,
            with_reviews: bool = False
    ) -> Dict[str, Any]:
        query = self.db.query(ServiceStaffModel)

        # 名字搜索
        if name and name.strip():
            users = self.db.query(UserModel) \
                .filter(UserModel.name.like(f"%{name.strip()}%")).all()
            user_ids = [u.id for u in users]
            if user_ids:
                query = query.filter(ServiceStaffModel.user_id.in_(user_ids))
            else:
                return {"records": [], "total": 0, "page_num": page_num, "page_size": page_size}

        # 最低评分
        if min_rating is not None:
            query = query.filter(ServiceStaffModel.rating >= min_rating)

        # 未删除 + 排序
        query = query.filter(ServiceStaffModel.is_deleted == 0) \
            .order_by(desc(ServiceStaffModel.rating))

        # 分页查询
        total = query.count()
        offset = (page_num - 1) * page_size
        records = query.offset(offset).limit(page_size).all()

        #  转字典
        staff_list = [ServiceStaff.model_validate({**r.__dict__}) for r in records]

        # 内存过滤服务类型
        if service_type and service_type.strip():
            search_type = service_type.strip()
            filtered = []
            for s in staff_list:
                try:
                    types = s.service_type
                    if isinstance(types, str):
                        types = json.loads(types)
                    if search_type in types:
                        filtered.append(s)
                except Exception as e:
                    logger.error(f"解析服务类型JSON失败: {s.service_type}", exc_info=True)
            staff_list = filtered
            total = len(filtered)

        # 填充关联信息
        self._fill_user_info_list(staff_list)
        if with_orders:
            self._fill_orders_list(staff_list)
        if with_reviews:
            self._fill_reviews_list(staff_list)
        self._fill_categories_list(staff_list)

        return {
            "records": staff_list,
            "total": total,
            "page_num": page_num,
            "page_size": page_size
        }

    # ===================== 评分前10 =====================
    def get_top_rated_staff(self) -> List[ServiceStaff]:
        staff_list = self.db.query(ServiceStaffModel) \
            .filter(ServiceStaffModel.is_deleted == 0) \
            .order_by(desc(ServiceStaffModel.rating)).limit(10).all()

        result = [ServiceStaff.model_validate(s.__dict__) for s in staff_list]
        self._fill_user_info_list(result)
        self._fill_categories_list(result)
        return result

    # ===================== 软删除 =====================
    def delete_service_staff(self, id: int) -> None:
        try:
            staff = self.db.query(ServiceStaffModel) \
                .filter(ServiceStaffModel.id == id, ServiceStaffModel.is_deleted == 0).first()
            if not staff:
                raise ServiceException("服务人员不存在")

            # 检查未完成订单
            unfinished_count = self.db.query(ServiceOrderModel) \
                .filter(
                    ServiceOrderModel.staff_id == id,
                    ServiceOrderModel.is_deleted == 0,
                    not_(ServiceOrderModel.order_status.in_([
                        OrderStatus.COMPLETED.get_value(),
                        OrderStatus.CANCELLED.get_value(),
                        OrderStatus.CLOSED.get_value()
                    ]))
                ).count()

            if unfinished_count > 0:
                raise ServiceException("该服务人员存在未完成的订单，不能删除")

            # 软删除
            staff.is_deleted = 1
            staff.update_time = datetime.now()
            self.db.commit()
            logger.info(f"服务人员软删除成功: {id}")
        except Exception as e:
            self.db.rollback()
            raise ServiceException(f"删除服务人员失败: {str(e)}")

    def batch_delete_service_staff(self, ids: List[int]) -> None:
        if not ids:
            return

        try:
            # 检查未完成订单
            unfinished_count = self.db.query(ServiceOrderModel) \
                .filter(
                    ServiceOrderModel.staff_id.in_(ids),
                    ServiceOrderModel.is_deleted == 0,
                    not_(ServiceOrderModel.order_status.in_([
                        OrderStatus.COMPLETED.get_value(),
                        OrderStatus.CANCELLED.get_value(),
                        OrderStatus.CLOSED.get_value()
                    ]))
                ).count()

            if unfinished_count > 0:
                raise ServiceException("选中的服务人员中存在未完成的订单，不能删除")

            # 批量软删除
            now = datetime.now()
            staffs = self.db.query(ServiceStaffModel) \
                .filter(ServiceStaffModel.id.in_(ids)).all()
            for s in staffs:
                s.is_deleted = 1
                s.update_time = now

            self.db.commit()
            logger.info(f"批量软删除服务人员成功: count={len(ids)}")
        except Exception as e:
            self.db.rollback()
            raise ServiceException(f"批量删除服务人员失败: {str(e)}")

    # ===================== 统计信息 =====================
    def get_service_staff_statistics(self, staff_id: int) -> Dict[str, Any]:
        staff = self.db.query(ServiceStaffModel) \
            .filter(ServiceStaffModel.id == staff_id, ServiceStaffModel.is_deleted == 0).first()
        if not staff:
            raise ServiceException("服务人员不存在")

        statistics = {}

        # 1. 订单统计
        total_orders = self.db.query(ServiceOrderModel) \
            .filter(ServiceOrderModel.staff_id == staff_id, ServiceOrderModel.is_deleted == 0).count()
        statistics["totalOrders"] = total_orders

        order_status_count = {
            "waitingPay": self._get_order_count_by_status(staff_id, OrderStatus.WAITING_PAY.get_value()),
            "waitingAccept": self._get_order_count_by_status(staff_id, OrderStatus.WAITING_ACCEPT.get_value()),
            "accepted": self._get_order_count_by_status(staff_id, OrderStatus.ACCEPTED.get_value()),
            "inService": self._get_order_count_by_status(staff_id, OrderStatus.IN_SERVICE.get_value()),
            "completed": self._get_order_count_by_status(staff_id, OrderStatus.COMPLETED.get_value()),
            "cancelled": self._get_order_count_by_status(staff_id, OrderStatus.CANCELLED.get_value())
        }
        statistics["orderStatusCount"] = order_status_count

        # 2. 评价统计
        reviews = self.db.query(ServiceReviewModel) \
            .filter(ServiceReviewModel.staff_id == staff_id).all()
        total_reviews = len(reviews)
        statistics["totalReviews"] = total_reviews

        if reviews:
            rating_stats = {
                "avgSkillRating": self._calculate_average_rating(reviews, lambda r: r.skill_rating),
                "avgAttitudeRating": self._calculate_average_rating(reviews, lambda r: r.attitude_rating),
                "avgExperienceRating": self._calculate_average_rating(reviews, lambda r: r.experience_rating),
                "avgOverallRating": self._calculate_overall_rating(reviews)
            }
            statistics["ratingStats"] = rating_stats

            good_reviews = sum(1 for r in reviews if self._get_overall_rating(r) >= 4.0)
            good_rate = self._calculate_percentage(good_reviews, total_reviews)
            statistics["goodRate"] = good_rate
        else:
            statistics["ratingStats"] = {
                "avgSkillRating": 5.0,
                "avgAttitudeRating": 5.0,
                "avgExperienceRating": 5.0,
                "avgOverallRating": 5.0
            }
            statistics["goodRate"] = 100.0

        # 3. 收入统计
        total_income = Decimal(0)
        month_income = Decimal(0)
        now = datetime.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        completed_orders = self.db.query(ServiceOrderModel) \
            .filter(
                ServiceOrderModel.staff_id == staff_id,
                ServiceOrderModel.order_status == OrderStatus.COMPLETED.get_value(),
                ServiceOrderModel.is_deleted == 0
            ).all()

        for o in completed_orders:
            if o.total_amount:
                amount = Decimal(str(o.total_amount))
                total_income += amount
                if o.complete_time and o.complete_time > month_start:
                    month_income += amount

        statistics["totalIncome"] = float(total_income)
        statistics["monthIncome"] = float(month_income)

        logger.info(f"获取服务人员统计信息成功: staffId={staff_id}")
        return statistics

    def _calculate_average_rating(self, reviews, rating_getter) -> float:
        total = Decimal(0)
        count = 0
        for r in reviews:
            rating = rating_getter(r)
            if rating is not None:
                total += Decimal(str(rating))
                count += 1
        if count > 0:
            avg = total / Decimal(count)
            return float(avg.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))
        return 5.0

    def _calculate_overall_rating(self, reviews) -> float:
        return self._calculate_average_rating(reviews, self._get_overall_rating)

    def _get_overall_rating(self, review) -> Optional[float]:
        if hasattr(review, 'overall_rating') and review.overall_rating is not None:
            return review.overall_rating
        if hasattr(review, 'rating') and review.rating is not None:
            return review.rating
        return None

    def _calculate_percentage(self, numerator: int, denominator: int) -> float:
        if denominator == 0:
            return 100.0
        rate = Decimal(numerator) * Decimal(100) / Decimal(denominator)
        return float(rate.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP))

    def _get_order_count_by_status(self, staff_id: int, status: int) -> int:
        return self.db.query(ServiceOrderModel) \
            .filter(
                ServiceOrderModel.staff_id == staff_id,
                ServiceOrderModel.order_status == status,
                ServiceOrderModel.is_deleted == 0
            ).count()

    # ===================== 更新订单统计 =====================
    def update_all_service_staff_orders(self) -> None:
        try:
            staff_list = self.db.query(ServiceStaffModel) \
                .filter(ServiceStaffModel.is_deleted == 0).all()
            for s in staff_list:
                self.update_service_staff_orders(s.id)
            logger.info("所有家政人员订单统计更新完成")
        except Exception as e:
            logger.error("更新家政人员订单数量失败", exc_info=True)
            raise ServiceException(f"更新家政人员订单数量失败: {str(e)}")

    def update_service_staff_orders(self, staff_id: int) -> None:
        try:
            staff = self.db.get(ServiceStaffModel, staff_id)
            if not staff:
                logger.warning(f"家政人员不存在，ID: {staff_id}")
                return

            completed = self.db.query(ServiceOrderModel) \
                .filter(
                    ServiceOrderModel.staff_id == staff_id,
                    ServiceOrderModel.order_status == OrderStatus.COMPLETED.get_value(),
                    ServiceOrderModel.is_deleted == 0
                ).count()

            total = self.db.query(ServiceOrderModel) \
                .filter(
                    ServiceOrderModel.staff_id == staff_id,
                    ServiceOrderModel.is_deleted == 0,
                    not_(ServiceOrderModel.order_status.in_([
                        OrderStatus.CANCELLED.get_value(),
                        OrderStatus.CLOSED.get_value()
                    ]))
                ).count()

            if total > 0:
                rate = Decimal(completed) * 100 / Decimal(total)
                rate = rate.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
            else:
                rate = Decimal("100.0")

            staff.total_orders = completed
            staff.completion_rate = rate
            staff.update_time = datetime.now()
            self.db.commit()
            logger.info(f"更新家政人员订单统计成功: staffId={staff_id}, 总订单={completed}, 完成率={rate}%")
        except Exception as e:
            self.db.rollback()
            logger.error(f"更新家政人员订单统计失败: staffId={staff_id}", exc_info=True)
            raise ServiceException(f"更新家政人员订单统计失败: {str(e)}")

    # ===================== 其他功能 =====================
    def get_available_staff_by_service_item(self, service_id: int) -> List[ServiceStaff]:
        staff_service_items = self.db.query(StaffServiceItemModel) \
            .filter(
                StaffServiceItemModel.service_id == service_id,
                StaffServiceItemModel.status == 1
            ).all()
        staff_ids = [s.staff_id for s in staff_service_items if s.staff_id]

        if not staff_ids:
            return []

        staff_list = self.db.query(ServiceStaffModel) \
            .filter(
                ServiceStaffModel.id.in_(staff_ids),
                ServiceStaffModel.is_deleted == 0
            ).all()

        result = [ServiceStaff.model_validate(s.__dict__) for s in staff_list]
        self._fill_user_info_list(result)
        self._fill_service_items_list(result)
        return result

    def search_service_staff(self, keyword: str) -> List[ServiceStaff]:
        if not keyword or not keyword.strip():
            return []

        keyword = keyword.strip()
        users = self.db.query(UserModel) \
            .filter(UserModel.name.like(f"%{keyword}%")).all()
        user_ids = [u.id for u in users]

        if not user_ids:
            return []

        staff_list = self.db.query(ServiceStaffModel) \
            .filter(
                ServiceStaffModel.user_id.in_(user_ids),
                ServiceStaffModel.is_deleted == 0
            ).all()

        result = [ServiceStaff.model_validate(s.__dict__) for s in staff_list]
        self._fill_user_info_list(result)
        self._fill_categories_list(result)
        return result