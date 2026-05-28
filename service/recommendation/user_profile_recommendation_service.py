import logging
from typing import List, Optional, Dict, Set
from decimal import Decimal
from sqlalchemy.orm import Session
# from sqlalchemy import and_, or_, desc, asc, in_

# 导入你项目已有的文件
from schemas.user import User
from schemas.service_item import ServiceItem
from schemas.service_order import ServiceOrder
from schemas.service_category import ServiceCategory
from utils.exceptions.service_exception import ServiceException
from utils.enums.order_status import OrderStatus

# 导入 SQLAlchemy Model
from models.user_model import UserModel
from models.service_item_model import ServiceItemModel
from models.service_order_model import ServiceOrderModel
from models.service_category_model import ServiceCategoryModel

# 导入其他迁移的服务
from service.service_item_service import ServiceItemService

# 日志配置
logger = logging.getLogger(__name__)

class  UserProfileRecommendationService:
    """
    基于内容的推荐服务
    通过分析用户的历史行为和服务的内容特征来进行个性化推荐
    """
    def __init__(self, db: Session):
        self.db = db

    # ===================== 核心推荐方法 =====================
    def get_recommendations(self, user_id: int, limit: int) -> List[ServiceItem]:
        """
        获取推荐服务列表
        """
        # 1. 获取用户信息
        user = self.db.get(UserModel, user_id)
        if not user:
            return []

        # 2. 获取用户的历史订单（已完成的）
        user_orders = self.db.query(ServiceOrderModel)\
            .filter(
                ServiceOrderModel.user_id == user_id,
                ServiceOrderModel.order_status == OrderStatus.COMPLETED.get_value()
            )\
            .all()

        # 3. 分析用户偏好
        category_preferences = self._analyze_category_preferences(user_orders)

        # 4. 获取所有可用服务（上架的）
        available_services = self.db.query(ServiceItemModel)\
            .filter(ServiceItemModel.status == 1)\
            .all()

        # 5. 计算服务匹配度
        service_scores = self._calculate_service_scores(
            available_services,
            category_preferences,
            User.model_validate(user.__dict__)
        )

        # 6. 过滤掉用户已使用的服务
        used_services: Set[int] = set()
        for order in user_orders:
            if order.service_id:
                used_services.add(order.service_id)

        # 7. 排序并返回推荐结果
        # 过滤已使用服务
        filtered_scores = {
            sid: score for sid, score in service_scores.items()
            if sid not in used_services
        }

        # 按得分降序排序
        sorted_services = sorted(
            filtered_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # 取前 limit 个
        top_service_ids = [sid for sid, _ in sorted_services[:limit]]

        # 查询服务详情
        result_services = self.db.query(ServiceItemModel)\
            .filter(ServiceItemModel.id.in_(top_service_ids))\
            .all()


        result = [ServiceItem.model_validate(s.__dict__) for s in result_services]

        # 填充类别信息
        service_item_service = ServiceItemService(self.db)
        # 这里我们手动实现一下 fillCategory，避免循环依赖
        self._fill_category(result)

        # ===================== 用户画像匹配得分 =====================
        logger.info("========== 用户画像推荐 ==========")
        logger.info(f"当前用户: {user_id}")
        logger.info(f"服务匹配得分（相似度）: {filtered_scores}")

        # 按推荐顺序打印：ID + 名称 + 相似度
        for sid in top_service_ids:
            score = filtered_scores.get(sid, 0.0)
            for item in result:
                if item.id == sid:
                    logger.info(f"推荐服务: ID={item.id} 名称={item.title} 相似度={score}")

        return result

    # ===================== 算法核心方法 =====================
    def _analyze_category_preferences(self, orders: List[ServiceOrderModel]) -> Dict[int, int]:
        """
        分析用户对不同类别的偏好
        """
        preferences: Dict[int, int] = {}

        for order in orders:
            if not order.service_id:
                continue

            service = self.db.get(ServiceItemModel, order.service_id)
            if service and service.category_id:
                if service.category_id in preferences:
                    preferences[service.category_id] += 1
                else:
                    preferences[service.category_id] = 1

        return preferences

    def _calculate_service_scores(
        self,
        services: List[ServiceItemModel],
        category_preferences: Dict[int, int],
        user: User
    ) -> Dict[int, float]:
        """
        计算服务的匹配得分
        """
        scores: Dict[int, float] = {}

        for service in services:
            if not service.id:
                continue
            score = self._calculate_service_score(
                ServiceItem.model_validate(service.__dict__),
                category_preferences,
                user
            )
            scores[service.id] = score

        return scores

    def _calculate_service_score(
        self,
        service: ServiceItem,
        category_preferences: Dict[int, int],
        user: User
    ) -> float:
        """
        计算单个服务的匹配得分
        基于类别偏好、价格匹配度等因素
        """
        score = 0.0

        # 1. 类别偏好匹配 (权重: 0.4)
        category_frequency = category_preferences.get(service.category_id, 0)
        score += 0.4 * (1.0 if category_frequency > 0 else 0.0)

        # 2. 价格匹配 (权重: 0.3)
        # 假设根据用户历史订单的平均价格来判断价格匹配度
        avg_order_amount = self._get_average_order_amount(user.id)
        if service.price and avg_order_amount > 0:
            price_ratio = float(service.price) / avg_order_amount
            if 0.8 <= price_ratio <= 1.2:
                score += 0.3

        # 3. 服务时间匹配 (权重: 0.3)
        # 这里可以根据实际需求添加更多匹配逻辑
        score += 0.3

        return score

    def _get_average_order_amount(self, user_id: int) -> float:
        """
        获取用户历史订单的平均金额
        """
        orders = self.db.query(ServiceOrderModel)\
            .filter(
                ServiceOrderModel.user_id == user_id,
                ServiceOrderModel.order_status == OrderStatus.COMPLETED.get_value()
            )\
            .all()

        if not orders:
            return 100.0  # 默认值

        total = Decimal(0)
        count = 0
        for order in orders:
            if order.total_amount:
                total += Decimal(str(order.total_amount))
                count += 1

        if count == 0:
            return 100.0

        avg = total / Decimal(count)
        return float(avg)

    # ===================== 辅助方法 =====================
    def _fill_category(self, services: List[ServiceItem]) -> None:
        """
        填充服务项目的类别信息
        """
        if not services:
            return

        # 收集所有类别ID
        category_ids: Set[int] = set()
        for service in services:
            if service.category_id:
                category_ids.add(service.category_id)

        if not category_ids:
            return

        # 批量查询类别信息
        categories = self.db.query(ServiceCategoryModel)\
            .filter(ServiceCategoryModel.id.in_(category_ids))\
            .all()
        category_map: Dict[int, ServiceCategory] = {
            c.id: ServiceCategory.model_validate(c.__dict__) for c in categories
        }

        # 填充类别信息
        for service in services:
            if service.category_id and service.category_id in category_map:
                service.category = category_map[service.category_id]