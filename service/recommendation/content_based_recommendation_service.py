import logging
from typing import List, Dict, Set
from sqlalchemy.orm import Session
#基于内容的推荐,智能相似推荐服务看某个服务 →推荐【相似的家政服务】
import jieba
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from schemas.service_item import ServiceItem
from schemas.service_category import ServiceCategory

from models.service_item_model import ServiceItemModel
from models.service_order_model import ServiceOrderModel
from models.service_category_model import ServiceCategoryModel


from utils.enums.order_status import OrderStatus

logger = logging.getLogger(__name__)

class ContentBasedRecommendationService:
    """
    基于内容的智能推荐系统（机器学习）

    当前算法：
    - 中文分词（jieba）
    - TF-IDF 文本向量化
    - 余弦相似度计算

    推荐依据：
    - 服务标题
    - 服务描述
    - 服务分类
    - 真正机器学习推荐
    - 支持中文
    - 推荐结果按相似度排序
    """

    def __init__(self, db: Session):
        self.db = db

        # 中文 TF-IDF 向量器
        self.vectorizer = TfidfVectorizer(
            tokenizer=self._chinese_tokenizer,
            lowercase=False,

            # 忽略太常见词
            max_df=0.8,

            # 忽略太少词
            min_df=1,

            # 1-2词组合
            ngram_range=(1, 2)
        )

    # =========================================================
    # 中文分词
    # =========================================================
    def _chinese_tokenizer(self, text):
        """
        jieba 中文分词
        """
        if not text:
            return []

        return jieba.lcut(text)

    # =========================================================
    # 获取推荐服务（主入口）
    # =========================================================
    def get_recommendations(
        self,
        service_id: int,
        limit: int = 6
    ) -> List[ServiceItem]:

        try:

            # ===================== 查询当前服务 =====================
            target_service = self.db.get(ServiceItemModel, service_id)

            if not target_service:
                return []

            # ===================== 查询所有可推荐服务 =====================
            all_services = (
                self.db.query(ServiceItemModel)
                .filter(
                    ServiceItemModel.status == 1,
                    ServiceItemModel.id != service_id
                )
                .all()
            )

            if not all_services:
                return []

            # ===================== 转换 Schema =====================
            target_schema = ServiceItem.model_validate(
                target_service,
                from_attributes=True
            )

            service_schemas = [
                ServiceItem.model_validate(
                    service,
                    from_attributes=True
                )
                for service in all_services
            ]

            # ===================== 计算相似度 =====================
            similarity_map = self._calculate_service_similarities(
                target_schema,
                service_schemas
            )

            if not similarity_map:
                return []

            # ===================== 按相似度排序 =====================
            sorted_services = sorted(
                similarity_map.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # ===================== 获取 TopN 服务ID =====================
            top_service_ids = [
                sid for sid, score in sorted_services[:limit]
            ]

            if not top_service_ids:
                return []

            # ===================== 查询服务详情 =====================
            result_services = (
                self.db.query(ServiceItemModel)
                .filter(ServiceItemModel.id.in_(top_service_ids))
                .all()
            )

            # ===================== 保持排序=====================
            service_map = {
                service.id: service
                for service in result_services
            }

            ordered_services = [
                service_map[sid]
                for sid in top_service_ids
                if sid in service_map
            ]

            # ===================== 转换 Schema =====================
            result = [
                ServiceItem.model_validate(
                    service,
                    from_attributes=True
                )
                for service in ordered_services
            ]

            # ===================== 填充分类 =====================
            self._fill_category(result)

            return result

        except Exception as e:
            logger.error(f"获取推荐服务失败: {e}")
            return []

    # =========================================================
    # 核心机器学习
    # =========================================================
    def _calculate_service_similarities(
        self,
        target_service: ServiceItem,
        services: List[ServiceItem]
    ) -> Dict[int, float]:

        try:

            corpus = []
            service_ids = []

            # ===================== 当前服务文本 =====================
            target_text = self._build_service_text(target_service)

            corpus.append(target_text)
            service_ids.append(target_service.id)

            # ===================== 其他服务文本 =====================
            for service in services:

                text = self._build_service_text(service)

                corpus.append(text)
                service_ids.append(service.id)

            # ===================== TF-IDF 向量化 =====================
            tfidf_matrix = self.vectorizer.fit_transform(corpus)

            # ===================== 余弦相似度 =====================
            cosine_similarities = linear_kernel(
                tfidf_matrix[0:1],
                tfidf_matrix
            ).flatten()

            # ===================== 构建结果 =====================
            similarity_map = {}

            for index, sid in enumerate(service_ids):

                if sid == target_service.id:
                    continue

                similarity_score = float(cosine_similarities[index])

                # 避免负数和异常值
                if similarity_score < 0:
                    similarity_score = 0.0

                similarity_map[sid] = round(similarity_score, 4)
            # ===================== 打印日志 =====================
            logger.info(f"基于内容的智能推荐算法-当前服务: {target_service.title}")
            logger.info(f"相似度结果: {similarity_map}")
            service_info = []
            for sid, score in similarity_map.items():# 打印：所有候选服务的 ID + 名称
                # 从数据库查服务名称
                service = self.db.query(ServiceItemModel).get(sid)
                name = service.title if service else "未知服务"
                service_info.append(f"[{sid}] {name} (相似度:{score})")

            logger.info(f"推荐候选服务列表（ID+名称）: {service_info}")
            return similarity_map

        except Exception as e:
            logger.error(f"推荐算法计算失败: {e}")

            return {
                service.id: 0.0
                for service in services
            }

    # =========================================================
    # 构建服务文本
    # =========================================================
    def _build_service_text(
        self,
        service: ServiceItem
    ) -> str:

        try:

            title = service.title or ""
            description = service.description or ""

            # ===================== 获取分类名 =====================
            category_name = ""

            if service.category_id:

                category = self.db.get(
                    ServiceCategoryModel,
                    service.category_id
                )

                if category:
                    category_name = getattr(category, "category_name", "")

            # ===================== 价格特征 =====================
            price_text = ""

            if service.price:

                price = float(service.price)

                if price <= 100:
                    price_text = "低价"

                elif price <= 300:
                    price_text = "中价"

                else:
                    price_text = "高价"

            # ===================== 关键词增强 =====================
            keywords = []

            content = f"{title} {description}"

            if "保洁" in content:
                keywords.extend([
                    "家庭保洁",
                    "卫生清洁",
                    "家政保洁"
                ])

            if "月嫂" in content:
                keywords.extend([
                    "母婴护理",
                    "婴儿护理",
                    "产后护理"
                ])

            if "护工" in content:
                keywords.extend([
                    "老人护理",
                    "医院陪护",
                    "康复护理"
                ])

            if "空调" in content:
                keywords.extend([
                    "家电清洗",
                    "深度清洁"
                ])

            keyword_text = " ".join(keywords)

            # ===================== 推荐文本 =====================
            text = f"""
                {title}
                {title}
                {title}

                {category_name}
                {category_name}

                {description}

                {keyword_text}

                {price_text}
            """

            return text.strip()

        except Exception as e:
            logger.error(f"构建服务文本失败: {e}")
            return ""

    # =========================================================
    # 获取购买过该服务的用户
    # =========================================================
    def _get_service_users(
        self,
        service_id: int
    ) -> Set[int]:

        orders = (
            self.db.query(ServiceOrderModel)
            .filter(
                ServiceOrderModel.service_id == service_id,
                ServiceOrderModel.order_status ==
                OrderStatus.COMPLETED.get_value()
            )
            .all()
        )

        user_ids = set()

        for order in orders:

            if order.user_id:
                user_ids.add(order.user_id)

        return user_ids

    # =========================================================
    # 填充分类信息
    # =========================================================
    def _fill_category(
        self,
        services: List[ServiceItem]
    ) -> None:

        try:

            if not services:
                return

            category_ids = set()

            for service in services:

                if service.category_id:
                    category_ids.add(service.category_id)

            if not category_ids:
                return

            categories = (
                self.db.query(ServiceCategoryModel)
                .filter(ServiceCategoryModel.id.in_(category_ids))
                .all()
            )

            category_map = {
                category.id: ServiceCategory.model_validate(
                    category,
                    from_attributes=True
                )
                for category in categories
            }

            for service in services:

                if (
                    service.category_id
                    and service.category_id in category_map
                ):
                    service.category = category_map[
                        service.category_id
                    ]

        except Exception as e:
            logger.error(f"填充分类失败: {e}")