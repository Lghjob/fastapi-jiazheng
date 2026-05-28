import logging
from typing import List, Optional, Dict, Set
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

# 导入你项目已有的文件
from schemas.service_favorite import ServiceFavorite
from schemas.user import User
from schemas.service_item import ServiceItem
from utils.exceptions.service_exception import ServiceException

# 导入 SQLAlchemy Model
from models.service_favorite_model import ServiceFavoriteModel
from models.user_model import UserModel
from models.service_item_model import ServiceItemModel

# 日志配置
logger = logging.getLogger(__name__)

class ServiceFavoriteService:
    def __init__(self, db: Session):
        self.db = db

    # ===================== 核心功能：添加收藏 =====================
    def add_favorite(self, favorite: ServiceFavorite) -> None:
        """
        添加收藏
        """
        try:
            # 1. 检查用户是否存在
            user = self.db.get(UserModel, favorite.user_id)
            if not user:
                raise ServiceException("用户不存在")

            # 2. 检查服务项目是否存在
            service_item = self.db.get(ServiceItemModel, favorite.service_id)
            if not service_item:
                raise ServiceException("服务项目不存在")
            if service_item.status == 0:
                raise ServiceException("该服务项目已下架")

            # 3. 检查是否已收藏
            existing_count = self.db.query(ServiceFavoriteModel)\
                .filter(
                    ServiceFavoriteModel.user_id == favorite.user_id,
                    ServiceFavoriteModel.service_id == favorite.service_id
                )\
                .count()
            if existing_count > 0:
                raise ServiceException("已经收藏过该服务项目")

            # 4. 保存收藏信息
            now = datetime.now()
            db_favorite = ServiceFavoriteModel(
                **favorite.model_dump(exclude_unset=True),
                create_time=now
            )
            self.db.add(db_favorite)

            self.db.commit()
            logger.info(f"添加收藏成功: {db_favorite.id}")
        except Exception as e:
            self.db.rollback()
            raise e

    # ===================== 取消收藏 =====================
    def cancel_favorite(self, user_id: int, service_id: int) -> None:
        """
        取消收藏
        """
        try:
            count = self.db.query(ServiceFavoriteModel)\
                .filter(
                    ServiceFavoriteModel.user_id == user_id,
                    ServiceFavoriteModel.service_id == service_id
                )\
                .delete(synchronize_session=False)

            if count <= 0:
                raise ServiceException("取消收藏失败")

            self.db.commit()
            logger.info(f"取消收藏成功: userId={user_id}, serviceId={service_id}")
        except Exception as e:
            self.db.rollback()
            raise e

    # ===================== 查询收藏 =====================
    def get_favorite_by_id(self, id: int) -> ServiceFavorite:
        """
        获取收藏详情
        """
        favorite = self.db.get(ServiceFavoriteModel, id)
        if not favorite:
            raise ServiceException("收藏记录不存在")
        
        # 填充关联信息
        favorite_Schema = ServiceFavorite.model_validate(favorite.__dict__)
        self._fill_favorite_info(favorite_Schema)
        return favorite_Schema

    def get_favorites_by_page(
        self,
        user_id: str,
        service_id: str,
        page_num: int,
        page_size: int
    ):
        """
        分页查询收藏列表 
        """
        query = self.db.query(ServiceFavoriteModel)

        # 条件查询
        if user_id and user_id.strip():
            query = query.filter(ServiceFavoriteModel.user_id == int(user_id))
        if service_id and service_id.strip():
            query = query.filter(ServiceFavoriteModel.service_id == int(service_id))

        query = query.order_by(desc(ServiceFavoriteModel.create_time))

        total = query.count()
        offset = (page_num - 1) * page_size
        records = query.offset(offset).limit(page_size).all()

        # ========================
        # ========================

        # 1. 收集所有用户ID、服务ID
        user_ids = set()
        service_ids = set()
        for f in records:
            user_ids.add(f.user_id)
            service_ids.add(f.service_id)

        # 2. 批量查询用户
        user_map = {}
        if user_ids:
            users = self.db.query(UserModel).filter(UserModel.id.in_(user_ids)).all()
            user_map = {u.id: u for u in users}

        # 3. 批量查询服务
        service_map = {}
        if service_ids:
            service_items = self.db.query(ServiceItemModel).filter(ServiceItemModel.id.in_(service_ids)).all()
            service_map = {s.id: s for s in service_items}

        # 4. 组装数据
        favorite_list = []
        for item in records:
            user = user_map.get(item.user_id)
            service = service_map.get(item.service_id)

            favorite_list.append({
                "id": item.id,
                "userId": item.user_id,
                "serviceId": item.service_id,
                "createTime": item.create_time,
                # 批量查询出来的用户信息
                "user": {
                    "id": user.id,
                    "name": user.username
                } if user else {},
                # 批量查询出来的服务信息
                "serviceItem": {
                    "id": service.id,
                    "title": service.title,
                    "price": service.price
                } if service else {}
            })

        # 返回格式
        return {
            "records": favorite_list,
            "total": total,
            "current": page_num,
            "size": page_size,
            "pages": (total + page_size - 1) // page_size
        }
    def is_favorite(self, user_id: int, service_id: int) -> bool:
        """
        检查是否已收藏
        """
        count = self.db.query(ServiceFavoriteModel)\
            .filter(
                ServiceFavoriteModel.user_id == user_id,
                ServiceFavoriteModel.service_id == service_id
            )\
            .count()
        return count > 0

    # ===================== 私有方法：填充关联信息 =====================
    def _fill_favorite_info(self, favorite: ServiceFavorite) -> None:
        """
        填充单个收藏的关联信息
        """
        if not favorite:
            return

        # 填充用户信息
        if favorite.user_id:
            user = self.db.get(UserModel, favorite.user_id)
            if user:
                favorite.user = User.model_validate(user.__dict__)

        # 填充服务项目信息
        if favorite.service_id:
            service_item = self.db.get(ServiceItemModel, favorite.service_id)
            if service_item:
                favorite.service_item = ServiceItem.model_validate(service_item.__dict__)

    def _fill_favorite_info_list(self, favorites: List[ServiceFavorite]) -> None:
        """
        批量填充收藏关联信息（优化性能，避免N+1查询）
        """
        if not favorites:
            return

        # 收集所有需要查询的ID（去重）
        user_ids: Set[int] = set()
        service_ids: Set[int] = set()
        for f in favorites:
            if f.user_id:
                user_ids.add(f.user_id)
            if f.service_id:
                service_ids.add(f.service_id)

        # 批量查询用户
        users: Dict[int, User] = {}
        if user_ids:
            user_list = self.db.query(UserModel)\
                .filter(UserModel.id.in_(user_ids))\
                .all()
            users = {u.id: User.model_validate(u.__dict__) for u in user_list}

        # 批量查询服务项目
        service_items: Dict[int, ServiceItem] = {}
        if service_ids:
            service_item_list = self.db.query(ServiceItemModel)\
                .filter(ServiceItemModel.id.in_(service_ids))\
                .all()
            service_items = {s.id: ServiceItem.model_validate(s.__dict__) for s in service_item_list}

        # 填充关联信息
        for favorite in favorites:
            if favorite.user_id and favorite.user_id in users:
                favorite.user = users[favorite.user_id]
            if favorite.service_id and favorite.service_id in service_items:
                favorite.service_item = service_items[favorite.service_id]