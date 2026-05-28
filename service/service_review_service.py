import logging
import re
from typing import List, Dict, Optional
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from sqlalchemy import desc

# Schema（使用你提供的 ServiceReview）
from schemas.service_review import ServiceReview
from schemas.user import User
from schemas.service_staff import ServiceStaff
from schemas.service_order import ServiceOrder

# Model
from models.service_review_model import ServiceReviewModel
from models.user_model import UserModel
from models.service_staff_model import ServiceStaffModel
from models.service_order_model import ServiceOrderModel

# 异常 & 枚举
from utils.exceptions.service_exception import ServiceException
from utils.enums.order_status import OrderStatus

logger = logging.getLogger(__name__)

class ServiceReviewService:
    def __init__(self, db: Session):
        self.db = db
        self.sensitive_words = set()
        self.init_sensitive_words()

    def init_sensitive_words(self):
        self.sensitive_words = {
                "傻逼", "垃圾", "混蛋", "骗子", "滚蛋", "sb", "fuck", "shit", "傻子",
                "操你", "滚", "骂人", "脏话", "色情", "赌博", "毒品"
        }
        logger.info("使用默认敏感词列表")

    # ===================== 创建评价 =====================
    def create_review(self, review: ServiceReview):
        # 1. 校验订单
        order = self.db.get(ServiceOrderModel, review.order_id)
        if not order:
            raise ServiceException("订单不存在")
        if order.order_status != OrderStatus.COMPLETED.get_value():
            raise ServiceException("订单未完成，不能评价")

        # 2. 校验是否已评价
        exists = self.db.query(ServiceReviewModel).filter(
            ServiceReviewModel.order_id == review.order_id
        ).first()
        if exists:
            raise ServiceException("订单已评价")

        # 3. 计算总体评分
        total = review.skill_rating + review.attitude_rating + review.experience_rating
        overall = Decimal(str(total)) / Decimal("3")
        overall_rating = float(overall.quantize(Decimal("0.0"), rounding=ROUND_HALF_UP))

        # 4. 敏感词过滤
        content = self.filter_sensitive(review.content)

        # 5. 入库
        db_review = ServiceReviewModel(
            order_id=review.order_id,
            user_id=review.user_id,
            staff_id=review.staff_id,
            skill_rating=review.skill_rating,
            attitude_rating=review.attitude_rating,
            experience_rating=review.experience_rating,
            overall_rating=overall_rating,
            content=content,
            create_time=review.create_time,
            update_time=review.update_time
        )
        self.db.add(db_review)
        self.db.commit()
        self.db.refresh(db_review)

        # 6. 更新服务人员评分
        self.update_staff_rating(review.staff_id)

    # ===================== 删除评价 =====================
    def delete_review(self, review_id: int):
        review = self.db.get(ServiceReviewModel, review_id)
        if not review:
            raise ServiceException("评价不存在")
        self.db.delete(review)
        self.db.commit()

    # ===================== 敏感词过滤 =====================
    def filter_sensitive(self, text: Optional[str]) -> Optional[str]:
        if not text:
            return text
        result = text
        for word in self.sensitive_words:
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            result = pattern.sub("*" * len(word), result)
        return result

    # ===================== 更新服务人员评分 =====================
    def update_staff_rating(self, staff_id: int):
        reviews = self.db.query(ServiceReviewModel).filter(
            ServiceReviewModel.staff_id == staff_id
        ).all()

        if not reviews:
            return

        total = Decimal("0")
        for r in reviews:
            total += Decimal(str(r.overall_rating))

        avg = total / Decimal(str(len(reviews)))
        avg_rating = float(avg.quantize(Decimal("0.0"), rounding=ROUND_HALF_UP))

        staff = self.db.get(ServiceStaffModel, staff_id)
        if staff:
            staff.rating = avg_rating
            self.db.commit()

    # ===================== 根据ID查询 =====================
    def get_review_by_id(self, review_id: int) -> ServiceReview:
        review = self.db.get(ServiceReviewModel, review_id)
        # if not review:
        #     raise ServiceException("评价不存在")
        return self._fill_review_info(review)

    # ===================== 分页查询 =====================
    def get_reviews_by_page(
        self,
        user_id: Optional[int],
        staff_id: Optional[int],
        order_id: Optional[int],
        page_num: int,
        page_size: int
    ):
        query = self.db.query(ServiceReviewModel)

        if user_id:
            query = query.filter(ServiceReviewModel.user_id == user_id)
        if staff_id:
            query = query.filter(ServiceReviewModel.staff_id == staff_id)
        if order_id:
            query = query.filter(ServiceReviewModel.order_id == order_id)

        total = query.count()
        query = query.order_by(desc(ServiceReviewModel.create_time))
        query = query.offset((page_num - 1) * page_size).limit(page_size)

        records = [self._fill_review_info(r) for r in query.all()]

        return {
            "total": total,
            "records": records,
            "pageNum": page_num,
            "pageSize": page_size
        }

    # ===================== 填充关联信息（单个） =====================
    def _fill_review_info(self, db_review: ServiceReviewModel) -> ServiceReview:
        # 用户
        user = self.db.get(UserModel, db_review.user_id)
        user_schema = User.model_validate(user.__dict__) if user else None

        # 服务人员
        staff = self.db.get(ServiceStaffModel, db_review.staff_id)
        staff_schema = ServiceStaff.model_validate(staff.__dict__) if staff else None

        # 订单
        order = self.db.get(ServiceOrderModel, db_review.order_id)
        order_schema = ServiceOrder.model_validate(order.__dict__) if order else None

        return ServiceReview(
            id=db_review.id,
            order_id=db_review.order_id,
            user_id=db_review.user_id,
            staff_id=db_review.staff_id,
            skill_rating=db_review.skill_rating,
            attitude_rating=db_review.attitude_rating,
            experience_rating=db_review.experience_rating,
            overall_rating=db_review.overall_rating,
            content=db_review.content,
            create_time=db_review.create_time,
            update_time=db_review.update_time,
            user=user_schema,
            staff=staff_schema,
            order=order_schema
        )