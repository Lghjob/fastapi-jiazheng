import logging
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

# 导入你项目已有的文件
from schemas.service_browse_history import ServiceBrowseHistory
from schemas.user import User
from schemas.service_item import ServiceItem
from utils.exceptions.service_exception import ServiceException

# 导入 SQLAlchemy Model
from models.service_browse_history_model import ServiceBrowseHistoryModel
from models.user_model import UserModel
from models.service_item_model import ServiceItemModel

# 日志配置
logger = logging.getLogger(__name__)

class ServiceBrowseHistoryService:
    def __init__(self, db: Session):
        self.db = db

    # ===================== 核心功能：记录浏览历史 =====================
    def record_browse_history(self, user_id: int, service_id: int) -> None:
        """
        记录浏览历史（去重更新）
        """
        try:
            # 1. 检查用户是否存在
            user = self.db.get(UserModel, user_id)
            if not user:
                raise ServiceException("用户不存在")

            # 2. 检查服务项目是否存在
            service_item = self.db.get(ServiceItemModel, service_id)
            if not service_item:
                raise ServiceException("服务项目不存在")

            # 3. 查询是否已有浏览记录
            history = self.db.query(ServiceBrowseHistoryModel)\
                .filter(
                    ServiceBrowseHistoryModel.user_id == user_id,
                    ServiceBrowseHistoryModel.service_id == service_id
                )\
                .first()

            now = datetime.now()
            if not history:
                # 创建新记录
                new_history = ServiceBrowseHistoryModel(
                    user_id=user_id,
                    service_id=service_id,
                    last_browse_time=now
                )
                self.db.add(new_history)
            else:
                # 更新已有记录
                history.last_browse_time = now

            self.db.commit()
            logger.info(f"记录浏览历史成功: userId={user_id}, serviceId={service_id}")
        except Exception as e:
            self.db.rollback()
            raise e

    # ===================== 清除浏览历史 =====================
    def clear_browse_history(self, user_id: int) -> None:
        """
        清除浏览历史
        """
        try:
            count = self.db.query(ServiceBrowseHistoryModel)\
                .filter(ServiceBrowseHistoryModel.user_id == user_id)\
                .delete(synchronize_session=False)
            self.db.commit()
            logger.info(f"清除浏览历史成功: userId={user_id}, count={count}")
        except Exception as e:
            self.db.rollback()
            raise e

    # ===================== 查询浏览历史 =====================
    def get_history_by_id(self, id: int) -> ServiceBrowseHistory:
        """
        获取浏览历史详情
        """
        history = self.db.get(ServiceBrowseHistoryModel, id)
        if not history:
            raise ServiceException("浏览记录不存在")
        
        # 填充关联信息
        history_Schema = ServiceBrowseHistory.model_validate(history.__dict__)
        self._fill_history_info(history_Schema)
        return history_Schema

    def get_history_by_page(
        self,
        user_id: Optional[int],
        service_id: Optional[int],
        page_num: int,
        page_size: int
    ):
        """
        分页查询浏览历史
        """
        query = self.db.query(ServiceBrowseHistoryModel)

        if user_id:
            query = query.filter(ServiceBrowseHistoryModel.user_id == user_id)
        if service_id:
            query = query.filter(ServiceBrowseHistoryModel.service_id == service_id)

        # 按最后浏览时间降序
        query = query.order_by(desc(ServiceBrowseHistoryModel.last_browse_time))

        total = query.count()
        offset = (page_num - 1) * page_size
        records = query.offset(offset).limit(page_size).all()

        # 转换为 并填充关联信息
        history_list = [ServiceBrowseHistory.model_validate(r.__dict__) for r in records]
        self._fill_history_info_list(history_list)

        return {
            "records": history_list,
            "total": total,
            "page_num": page_num,
            "page_size": page_size
        }

    # ===================== 私有方法：填充关联信息 =====================
    def _fill_history_info(self, history: ServiceBrowseHistory) -> None:
        """
        填充单个浏览记录的关联信息
        """
        if not history:
            return

        # 填充用户信息
        if history.user_id:
            user = self.db.get(UserModel, history.user_id)
            if user:
                history.user = User.model_validate(user.__dict__)

        # 填充服务项目信息
        if history.service_id:
            service_item = self.db.get(ServiceItemModel, history.service_id)
            if service_item:
                history.service_item = ServiceItem.model_validate(service_item.__dict__)

    def _fill_history_info_list(self, histories: List[ServiceBrowseHistory]) -> None:
        """
        批量填充浏览记录关联信息（优化性能，避免N+1查询）
        """
        if not histories:
            return

        # 收集所有需要查询的ID
        user_ids = [h.user_id for h in histories if h.user_id]
        service_ids = [h.service_id for h in histories if h.service_id]

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
        for history in histories:
            if history.user_id and history.user_id in users:
                history.user = users[history.user_id]
            if history.service_id and history.service_id in service_items:
                history.service_item = service_items[history.service_id]