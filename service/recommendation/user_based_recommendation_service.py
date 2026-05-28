import logging
from typing import List, Dict, Set
from sqlalchemy.orm import Session

# 你的 
from schemas.user import User
from schemas.service_order import ServiceOrder
from schemas.service_item import ServiceItem
from schemas.service_category import ServiceCategory

# 枚举 & 异常
from utils.enums.order_status import OrderStatus
from utils.exceptions.service_exception import ServiceException

# 模型
from models.user_model import UserModel
from models.service_order_model import ServiceOrderModel
from models.service_item_model import ServiceItemModel
from models.service_category_model import ServiceCategoryModel

logger = logging.getLogger(__name__)

class UserBasedRecommendationService:
    """
    基于用户的协同过滤推荐服务
    通过分析用户相似度进行推荐，找到相似用户，推荐他们用过的服务
    """

    def __init__(self, db: Session):
        self.db = db

    # ===================== 核心推荐接口 =====================
    def get_recommendations(self, user_id: int, limit: int) -> List[ServiceItem]:
        # 1. 获取目标用户
        target_user = self.db.get(UserModel, user_id)
        if not target_user:
            return []

        target_user = User.model_validate(target_user.__dict__)

        # 2. 获取所有用户
        all_users = self.db.query(UserModel).all()
        all_users = [User.model_validate(u.__dict__) for u in all_users]

        # 3. 获取所有用户的订单
        user_ids = [u.id for u in all_users]
        user_orders = self._get_user_orders(user_ids)

        # 4. 计算用户相似度
        user_similarities = self._calculate_user_similarities(target_user, all_users)

        # 5. 取最相似的 5 个用户
        similar_user_ids = [
            uid for uid, score in
            sorted(user_similarities.items(), key=lambda x: x[1], reverse=True)
        ][:5]
       # ===================== 用户相似度 =====================
        logger.info("=" * 50)
        logger.info(f"用户协同过滤 - 当前用户 ID: {user_id}")
        logger.info(f"所有用户相似度结果: {user_similarities}")
        logger.info(f"选出最相似的 5 个用户: {similar_user_ids}")
        logger.info("=" * 50)
        # 6. 目标用户已经用过的服务
        target_services = {
            order.service_id for order in user_orders.get(user_id, [])
        }

        # 7. 统计相似用户用过的服务频率
        service_freq: Dict[int, int] = {}
        for uid in similar_user_ids:
            orders = user_orders.get(uid, [])
            for order in orders:
                sid = order.service_id
                if sid not in target_services:
                    service_freq[sid] = service_freq.get(sid, 0) + 1

        # 8. 排序 + 取前 limit
        sorted_services = sorted(
            service_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )
        top_ids = [sid for sid, cnt in sorted_services[:limit]]
        # ===================== 兜底推荐：没有相似用户时返回热门服务 =====================
        from sqlalchemy import func  # 只需要加一次在文件顶部也可以
        if not top_ids:
            logger.info("⚠️ 相似用户可推荐量不足，使用热门服务兜底推荐")
            hot_orders = self.db.query(ServiceOrderModel.service_id)\
                .filter(ServiceOrderModel.order_status == OrderStatus.COMPLETED.get_value())\
                .group_by(ServiceOrderModel.service_id)\
                .order_by(func.count().desc())\
                .limit(limit).all()
            top_ids = [sid[0] for sid in hot_orders]
        # ===================== 结束 =====================
        # 9. 查询服务详情
        items = self.db.query(ServiceItemModel) \
            .filter(ServiceItemModel.id.in_(top_ids)) \
            .all()
        res = [ServiceItem.model_validate(item.__dict__) for item in items]

        # 10. 填充分类
        self._fill_category(res)
        logger.info("========== 用户协同过滤推荐 ==========")
        logger.info(f"当前用户: {user_id}")

        for item in res:
            logger.info(
                f"推荐服务: {item.id} - {item.title}"
            )
        return res

    # ===================== 获取用户订单 =====================
    def _get_user_orders(self, user_ids: List[int]) -> Dict[int, List[ServiceOrder]]:
        result = {}
        for uid in user_ids:
            orders = self.db.query(ServiceOrderModel) \
                .filter(
                ServiceOrderModel.user_id == uid,
                ServiceOrderModel.order_status == OrderStatus.COMPLETED.get_value()
            ).all()

            result[uid] = [ServiceOrder.model_validate(o.__dict__) for o in orders]
        return result

    # ===================== 计算所有用户相似度 =====================
    def _calculate_user_similarities(self, target_user: User, users: List[User]) -> Dict[int, float]:
        sim_map = {}
        for user in users:
            if user.id == target_user.id:
                continue
            sim = self._calculate_similarity(target_user, user)
            sim_map[user.id] = sim
        return sim_map

    # ===================== 两个用户相似度计算 =====================
    def _calculate_similarity(self, u1: User, u2: User) -> float:
        match = 0
        total = 0

        # 年龄 ±5 
        age1 = u1.age if u1.age is not None else 0
        age2 = u2.age if u2.age is not None else 0
        if abs(age1 - age2) <= 5:
            match += 1
        total += 1

        # 性别
        if u1.gender == u2.gender:
            match += 1
        total += 1

        # 地址前6位匹配
        addr1 = u1.address or ""
        addr2 = u2.address or ""
        min_len = min(6, len(addr1), len(addr2))
        if addr1[:min_len] == addr2[:min_len]:
            match += 1
        total += 1

        if total == 0:
            return 0.0
        return match / total

    # ===================== 填充分类信息 =====================
    def _fill_category(self, services: List[ServiceItem]):
        if not services:
            return

        cids = {s.category_id for s in services if s.category_id}
        categories = self.db.query(ServiceCategoryModel) \
            .filter(ServiceCategoryModel.id.in_(cids)) \
            .all()
        cat_map = {c.id: ServiceCategory.model_validate(c.__dict__) for c in categories}

        for s in services:
            if s.category_id in cat_map:
                s.category = cat_map[s.category_id]