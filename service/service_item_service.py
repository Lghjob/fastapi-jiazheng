import logging
from typing import List, Optional, Dict, Set
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, not_

# 导入你项目已有的文件
from schemas.service_item import ServiceItem
from schemas.service_category import ServiceCategory
from schemas.service_order import ServiceOrder
from utils.exceptions.service_exception import ServiceException
from utils.enums.order_status import OrderStatus

# 导入 SQLAlchemy Model
from models.service_item_model import ServiceItemModel
from models.service_category_model import ServiceCategoryModel
from models.service_order_model import ServiceOrderModel

# 日志配置
logger = logging.getLogger(__name__)

class ServiceItemService:
    def __init__(self, db: Session):
        self.db = db

    # ===================== 项目CRUD =====================
    def create_service_item(self, item: ServiceItem) -> None:
        """
        创建服务项目
        """
        try:
            # 检查类别是否存在
            if item.category_id:
                category = self.db.get(ServiceCategoryModel, item.category_id)
                if not category:
                    raise ServiceException("服务类别不存在")

            # 设置默认状态
            if item.status is None:
                item.status = 1  # 默认上架

            # 保存服务项目
            now = datetime.now()
            db_item = ServiceItemModel(
                **item.model_dump(exclude_unset=True, exclude={"category","create_time", "update_time"}),
            )
            self.db.add(db_item)

            self.db.commit()
            logger.info(f"创建服务项目成功: {db_item.id}")
        except Exception as e:
            self.db.rollback()
            raise e

    def update_service_item(self, item: ServiceItem) -> None:
        """
        更新服务项目
        """
        try:
            # 检查服务项目是否存在
            exist_item = self.db.get(ServiceItemModel, item.id)
            if not exist_item:
                raise ServiceException("服务项目不存在")

            # 如果修改了类别，检查新类别是否存在
            if item.category_id:
                category = self.db.get(ServiceCategoryModel, item.category_id)
                if not category:
                    raise ServiceException("服务类别不存在")

            # 更新服务项目
            for key, value in item.model_dump(exclude_unset=True).items():
                setattr(exist_item, key, value)
            exist_item.update_time = datetime.now()

            self.db.commit()
            logger.info(f"更新服务项目成功: {item.id}")
        except Exception as e:
            self.db.rollback()
            raise ServiceException("更新服务项目失败")

    def get_service_item_by_id(self, id: int) -> ServiceItem:
        """
        获取服务项目详情
        """
        item = self.db.query(ServiceItemModel)\
            .filter(
                ServiceItemModel.id == id,
                ServiceItemModel.is_deleted == 0
            )\
            .first()
        if not item:
            raise ServiceException("服务项目不存在")
        
        # 填充类别信息
        item_Schema = ServiceItem.model_validate(item.__dict__)
        self._fill_category(item_Schema)
        return item_Schema

    # ===================== 分页查询 =====================
    def get_service_items_by_page(
        self,
        title: Optional[str],  
        category_id: str,
        status: str,
        page_num: int,
        page_size: int
    ):
        """
        分页查询服务项目列表
        """
        query = self.db.query(ServiceItemModel)

        if title and title.strip():
            query = query.filter(ServiceItemModel.title.like(f"%{title}%"))

        # 字符串转int，空字符串不查询
        if category_id and category_id.strip():
            query = query.filter(ServiceItemModel.category_id == int(category_id))
        if status and status.strip():
            query = query.filter(ServiceItemModel.status == int(status))

        # 只查询未删除的项目
        query = query.filter(ServiceItemModel.is_deleted == 0)

        total = query.count()
        offset = (page_num - 1) * page_size
        records = query.offset(offset).limit(page_size).all()

        # 填充类别信息
        item_list = [ServiceItem.model_validate(r.__dict__) for r in records]
        self._fill_category_list(item_list)

        return {
            "records": item_list,
            "total": total,
            "page_num": page_num,
            "page_size": page_size
        }

    # ===================== 删除 =====================
    def delete_service_item(self, id: int) -> None:
        """
        删除服务项目（软删除）
        """
        try:
            # 检查服务项目是否存在
            item = self.db.get(ServiceItemModel, id)
            if not item:
                raise ServiceException("服务项目不存在")

            # 检查是否存在未完成的订单
            unfinished_count = self.db.query(ServiceOrderModel)\
                .filter(
                    ServiceOrderModel.service_id == id,
                    not_(ServiceOrderModel.order_status.in_([
                        OrderStatus.COMPLETED.get_value(),
                        OrderStatus.CANCELLED.get_value(),
                        OrderStatus.CLOSED.get_value()
                    ]))
                )\
                .count()
            if unfinished_count > 0:
                raise ServiceException("该服务项目存在未完成的订单，不能删除")

            # 执行软删除
            item.is_deleted = 1
            item.update_time = datetime.now()

            self.db.commit()
            logger.info(f"服务项目软删除成功: {id}")
        except Exception as e:
            self.db.rollback()
            raise e

    def batch_delete_service_items(self, ids: List[int]) -> None:
        """
        批量删除服务项目（软删除）
        """
        if not ids:
            return

        try:
            # 检查是否存在未完成的订单
            unfinished_count = self.db.query(ServiceOrderModel)\
                .filter(
                    ServiceOrderModel.service_id.in_(ids),
                    not_(ServiceOrderModel.order_status.in_([
                        OrderStatus.COMPLETED.get_value(),
                        OrderStatus.CANCELLED.get_value(),
                        OrderStatus.CLOSED.get_value()
                    ]))
                )\
                .count()
            if unfinished_count > 0:
                raise ServiceException("选中的服务项目中存在未完成的订单，不能删除")

            # 执行批量软删除
            now = datetime.now()
            items = self.db.query(ServiceItemModel)\
                .filter(ServiceItemModel.id.in_(ids))\
                .all()
            for item in items:
                item.is_deleted = 1
                item.update_time = now

            self.db.commit()
            logger.info(f"批量软删除服务项目成功: count={len(ids)}")
        except Exception as e:
            self.db.rollback()
            raise ServiceException("批量删除服务项目失败")

    # ===================== 状态管理 =====================
    def update_status(self, id: int, status: int) -> None:
        """
        修改服务项目状态
        """
        try:
            item = self.db.get(ServiceItemModel, id)
            if not item:
                raise ServiceException("服务项目不存在")

            item.status = status
            item.update_time = datetime.now()

            self.db.commit()
            logger.info(f"修改服务项目状态成功: {id}, status: {status}")
        except Exception as e:
            self.db.rollback()
            raise ServiceException("修改状态失败")

    # ===================== 按类别查询 =====================
    def get_service_items_by_category(self, category_id: int) -> List[ServiceItem]:
        """
        根据类别ID获取服务项目列表（包含子类别的项目）
        """
        # 获取类别及其所有子类别
        category_ids: List[int] = [category_id]
        category_ids.extend(self._get_sub_category_ids(category_id))

        # 查询服务项目
        items = self.db.query(ServiceItemModel)\
            .filter(
                ServiceItemModel.category_id.in_(category_ids),
                ServiceItemModel.status == 1,
                ServiceItemModel.is_deleted == 0
            )\
            .all()

        # 填充类别信息
        item_list = [ServiceItem.model_validate(i.__dict__) for i in items]
        self._fill_category_list(item_list)
        return item_list

    # ===================== 搜索 =====================
    def search_service_items(self, keyword: str) -> List[ServiceItem]:
        """
        搜索服务项目
        """
        if not keyword or not keyword.strip():
            return []

        # 构建查询条件
        query = self.db.query(ServiceItemModel)\
            .filter(
                and_(
                    or_(
                        ServiceItemModel.title.like(f"%{keyword}%"),
                        ServiceItemModel.description.like(f"%{keyword}%")
                    ),
                    ServiceItemModel.status == 1,
                    ServiceItemModel.is_deleted == 0
                )
            )\
            .order_by(desc(ServiceItemModel.create_time))\
            .limit(10)

        # 执行查询
        items = query.all()
        item_list = [ServiceItem.model_validate(i.__dict__) for i in items]
        self._fill_category_list(item_list)
        return item_list

    # ===================== 私有方法 =====================
    def _fill_category(self, item: ServiceItem) -> None:
        """
        填充单个服务项目的类别信息
        """
        if not item or not item.category_id:
            return

        category = self.db.get(ServiceCategoryModel, item.category_id)
        if category:
            item.category = ServiceCategory.model_validate(category.__dict__)

    def _fill_category_list(self, items: List[ServiceItem]) -> None:
        """
        批量填充服务项目的类别信息
        """
        if not items:
            return

        # 提取所有类别ID
        category_ids: Set[int] = set()
        for item in items:
            if item.category_id:
                category_ids.add(item.category_id)

        if not category_ids:
            return

        # 批量查询类别信息
        categories = self.db.query(ServiceCategoryModel)\
            .filter(ServiceCategoryModel.id.in_(category_ids))\
            .all()
        category_map= {
            c.id: ServiceCategory.model_validate(c.__dict__) for c in categories
        }

        # 填充类别信息
        for item in items:
            if item.category_id and item.category_id in category_map:
                item.category = category_map[item.category_id]
    def _get_sub_category_ids(self, parent_id: int) -> List[int]:
        """
        递归获取子类别ID列表
        """
        ids: List[int] = []

        children = self.db.query(ServiceCategoryModel)\
            .filter(
                ServiceCategoryModel.parent_id == parent_id,
                ServiceCategoryModel.status == 1,
                ServiceCategoryModel.is_deleted == 0
            )\
            .all()

        if children:
            for child in children:
                ids.append(child.id)
                ids.extend(self._get_sub_category_ids(child.id))

        return ids