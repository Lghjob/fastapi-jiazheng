import logging
from typing import List, Optional, Dict, Set
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

# 导入你项目已有的文件
from schemas.staff_service_item import StaffServiceItem
from schemas.service_item import ServiceItem
from utils.exceptions.service_exception import ServiceException

# 导入 SQLAlchemy Model
from models.staff_service_item_model import StaffServiceItemModel
from models.service_item_model import ServiceItemModel

# 日志配置
logger = logging.getLogger(__name__)

class StaffServiceItemService:
    def __init__(self, db: Session):
        self.db = db

    # ===================== 添加服务项目 =====================
    def add_service_item(self, staff_id: int, service_id: int) -> None:
        """
        为服务人员添加服务项目
        """
        try:
            # 检查是否已存在关联
            if self._check_service_item_exists(staff_id, service_id):
                raise ServiceException("该服务项目已添加")

            # 创建关联记录
            now = datetime.now()
            item = StaffServiceItemModel(
                staff_id=staff_id,
                service_id=service_id,
                status=1,  # 默认启用
                create_time=now,
                update_time=now
            )
            self.db.add(item)

            self.db.commit()
            logger.info(f"服务人员添加服务项目成功: staffId={staff_id}, serviceId={service_id}")
        except Exception as e:
            self.db.rollback()
            raise e

    def batch_add_service_items(self, staff_id: int, service_ids: List[int]) -> None:
        """
        批量添加服务项目
        """
        if not service_ids:
            return

        try:
            now = datetime.now()
            for service_id in service_ids:
                if not self._check_service_item_exists(staff_id, service_id):
                    item = StaffServiceItemModel(
                        staff_id=staff_id,
                        service_id=service_id,
                        status=1,
                        create_time=now,
                        update_time=now
                    )
                    self.db.add(item)

            self.db.commit()
            logger.info(f"服务人员批量添加服务项目成功: staffId={staff_id}, count={len(service_ids)}")
        except Exception as e:
            self.db.rollback()
            raise e

    # ===================== 移除服务项目 =====================
    def remove_service_item(self, staff_id: int, service_id: int) -> None:
        """
        移除服务项目
        """
        try:
            result = self.db.query(StaffServiceItemModel)\
                .filter(
                    StaffServiceItemModel.staff_id == staff_id,
                    StaffServiceItemModel.service_id == service_id
                )\
                .delete(synchronize_session=False)

            if result <= 0:
                raise ServiceException("移除服务项目失败")

            self.db.commit()
            logger.info(f"服务人员移除服务项目成功: staffId={staff_id}, serviceId={service_id}")
        except Exception as e:
            self.db.rollback()
            raise e

    def batch_remove_service_items(self, staff_id: int, service_ids: List[int]) -> None:
        """
        批量移除服务项目
        """
        if not service_ids:
            return

        try:
            self.db.query(StaffServiceItemModel)\
                .filter(
                    StaffServiceItemModel.staff_id == staff_id,
                    StaffServiceItemModel.service_id.in_(service_ids)
                )\
                .delete(synchronize_session=False)

            self.db.commit()
            logger.info(f"服务人员批量移除服务项目成功: staffId={staff_id}, count={len(service_ids)}")
        except Exception as e:
            self.db.rollback()
            raise e

    # ===================== 更新服务项目状态 =====================
    def update_service_item_status(self, staff_id: int, service_id: int, status: int) -> None:
        """
        更新服务项目状态
        """
        try:
            item = self.db.query(StaffServiceItemModel)\
                .filter(
                    StaffServiceItemModel.staff_id == staff_id,
                    StaffServiceItemModel.service_id == service_id
                )\
                .first()

            if not item:
                raise ServiceException("更新服务项目状态失败")

            item.status = status
            item.update_time = datetime.now()

            self.db.commit()
            logger.info(f"更新服务项目状态成功: staffId={staff_id}, serviceId={service_id}, status={status}")
        except Exception as e:
            self.db.rollback()
            raise e

    # ===================== 查询服务项目 =====================
    def get_service_items(self, staff_id: int) -> List[StaffServiceItem]:
        """
        获取服务人员的所有服务项目
        """
        items = self.db.query(StaffServiceItemModel)\
            .filter(StaffServiceItemModel.staff_id == staff_id)\
            .all()


        result = [StaffServiceItem.model_validate(i.__dict__) for i in items]

        # 填充服务项目详情
        if result:
            service_ids: Set[int] = set()
            for item in result:
                if item.service_id:
                    service_ids.add(item.service_id)

            if service_ids:
                # 批量查询服务项目
                service_items = self.db.query(ServiceItemModel)\
                    .filter(ServiceItemModel.id.in_(service_ids))\
                    .all()
                service_item_map: Dict[int, ServiceItem] = {
                    s.id: ServiceItem.model_validate(s.__dict__) for s in service_items
                }

                # 填充服务项目详情
                for item in result:
                    if item.service_id and item.service_id in service_item_map:
                        item.service_item = service_item_map[item.service_id]

        return result

    def get_staffs_by_service_item(self, service_id: int) -> List[StaffServiceItem]:
        """
        根据服务项目获取提供该服务的服务人员关联记录
        """
        items = self.db.query(StaffServiceItemModel)\
            .filter(
                StaffServiceItemModel.service_id == service_id,
                StaffServiceItemModel.status == 1  # 只查询启用状态的关联
            )\
            .all()
        return [StaffServiceItem.model_validate(i.__dict__) for i in items]

    # ===================== 私有方法 =====================
    def _check_service_item_exists(self, staff_id: int, service_id: int) -> bool:
        """
        检查服务项目是否已存在
        """
        count = self.db.query(StaffServiceItemModel)\
            .filter(
                StaffServiceItemModel.staff_id == staff_id,
                StaffServiceItemModel.service_id == service_id
            )\
            .count()
        return count > 0