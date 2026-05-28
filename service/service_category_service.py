import logging
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

# 导入你项目已有的文件
from schemas.service_category import ServiceCategory
from schemas.service_item import ServiceItem
from utils.exceptions.service_exception import ServiceException

# 导入 SQLAlchemy Model
from models.service_category_model import ServiceCategoryModel
from models.service_item_model import ServiceItemModel

# 日志配置
logger = logging.getLogger(__name__)

class ServiceCategoryService:
    def __init__(self, db: Session):
        self.db = db

    # ===================== 类别CRUD =====================
    def create_category(self, category: ServiceCategory) -> None:
        """
        创建服务类别
        """
        try:
            # 设置默认值
            if category.status is None:
                category.status = 1
            if category.sort_num is None:
                category.sort_num = 1

            # 检查父类别是否存在
            if category.parent_id:
                parent = self.db.get(ServiceCategoryModel, category.parent_id)
                if not parent:
                    raise ServiceException("父类别不存在")

            # 保存类别信息
            now = datetime.now()
            db_category = ServiceCategoryModel(
                **category.model_dump(exclude_unset=True),
                create_time=now,
                update_time=now
            )
            self.db.add(db_category)

            self.db.commit()
            logger.info(f"创建服务类别成功: {db_category.id}")
        except Exception as e:
            self.db.rollback()
            raise e

    def update_category(self, category: ServiceCategory) -> None:
        """
        更新服务类别
        """
        try:
            # 检查类别是否存在
            exist_category = self.db.get(ServiceCategoryModel, category.id)
            if not exist_category:
                raise ServiceException("服务类别不存在")

            # 检查父类别是否存在且不能设置自己为父类别
            if category.parent_id:
                if category.parent_id == category.id:
                    raise ServiceException("不能设置自己为父类别")
                parent = self.db.get(ServiceCategoryModel, category.parent_id)
                if not parent:
                    raise ServiceException("父类别不存在")

            # 更新类别信息
            for key, value in category.model_dump(exclude_unset=True).items():
                setattr(exist_category, key, value)
            exist_category.update_time = datetime.now()

            self.db.commit()
            logger.info(f"更新服务类别成功: {category.id}")
        except Exception as e:
            self.db.rollback()
            raise ServiceException("更新服务类别失败")

    def get_category_by_id(self, id: int) -> ServiceCategory:
        """
        获取服务类别详情
        """
        category = self.db.query(ServiceCategoryModel)\
            .filter(
                ServiceCategoryModel.id == id,
                ServiceCategoryModel.is_deleted == 0
            )\
            .first()
        if not category:
            raise ServiceException("服务类别不存在")
        return ServiceCategory.model_validate(category.__dict__)

    # ===================== 树形结构 =====================
    def get_category_tree(self) -> List[ServiceCategory]:
        """
        获取服务类别树
        """
        # 查询所有未删除的类别
        all_categories = self.db.query(ServiceCategoryModel)\
            .filter(ServiceCategoryModel.is_deleted == 0)\
            .order_by(asc(ServiceCategoryModel.sort_num))\
            .all()
        category_list = [ServiceCategory.model_validate(c.__dict__) for c in all_categories]
        
        # 构建树形结构
        return self._build_category_tree(category_list)

    # ===================== 删除 =====================
    def delete_category(self, id: int) -> None:
        """
        删除服务类别（软删除）
        """
        try:
            # 检查类别是否存在
            category = self.db.get(ServiceCategoryModel, id)
            if not category:
                raise ServiceException("服务类别不存在")

            # 检查是否存在子类别
            child_count = self.db.query(ServiceCategoryModel)\
                .filter(
                    ServiceCategoryModel.parent_id == id,
                    ServiceCategoryModel.is_deleted == 0
                )\
                .count()
            if child_count > 0:
                raise ServiceException("存在子类别,不能删除")

            # 检查是否有关联的服务项目
            item_count = self.db.query(ServiceItemModel)\
                .filter(
                    ServiceItemModel.category_id == id,
                    ServiceItemModel.is_deleted == 0
                )\
                .count()
            if item_count > 0:
                raise ServiceException("该类别下存在服务项目,不能删除")

            # 执行软删除
            category.is_deleted = 1
            category.update_time = datetime.now()

            self.db.commit()
            logger.info(f"服务类别软删除成功: {id}")
        except Exception as e:
            self.db.rollback()
            raise e

    def batch_delete_categories(self, ids: List[int]) -> None:
        """
        批量删除服务类别
        """
        if not ids:
            return

        try:
            # 检查是否包含有子类别的分类
            for id in ids:
                children = self.get_child_categories(id)
                if children:
                    raise ServiceException("选中的类别中包含有子类别，不能直接删除")

            # 执行批量软删除
            now = datetime.now()
            categories = self.db.query(ServiceCategoryModel)\
                .filter(ServiceCategoryModel.id.in_(ids))\
                .all()
            for category in categories:
                category.is_deleted = 1
                category.update_time = now

            self.db.commit()
            logger.info(f"批量删除服务类别成功: count={len(ids)}")
        except Exception as e:
            self.db.rollback()
            raise ServiceException("批量删除服务类别失败")

    # ===================== 查询 =====================
    def get_child_categories(self, parent_id: int) -> List[ServiceCategory]:
        """
        获取子类别列表s
        """
        categories = self.db.query(ServiceCategoryModel)\
            .filter(
                ServiceCategoryModel.parent_id == parent_id,
                ServiceCategoryModel.is_deleted == 0
            )\
            .order_by(asc(ServiceCategoryModel.sort_num))\
            .all()
        return [ServiceCategory.model_validate(c.__dict__) for c in categories]

    def get_categories_by_page(
        self,
        category_name: Optional[str],
        status: Optional[str],
        page_num: int,
        page_size: int
    ):
        """
        分页查询服务类别
        """
        query = self.db.query(ServiceCategoryModel).filter(ServiceCategoryModel.is_deleted == 0)

        if category_name and category_name.strip():
            query = query.filter(ServiceCategoryModel.category_name.like(f"%{category_name}%"))
        if status and status.strip():
            query = query.filter(ServiceCategoryModel.status == int(status))

        # 按排序号升序、创建时间降序
        query = query.order_by(
            asc(ServiceCategoryModel.sort_num),
            desc(ServiceCategoryModel.create_time)
        )

        total = query.count()
        offset = (page_num - 1) * page_size
        records = query.offset(offset).limit(page_size).all()

        return {
            "records": [ServiceCategory.model_validate(r.__dict__) for r in records],
            "total": total,
            "page_num": page_num,
            "page_size": page_size
        }

    def search_categories(self, keyword: str) -> List[ServiceCategory]:
        """
        搜索服务类别
        """
        if not keyword or not keyword.strip():
            return []

        # 构建查询条件
        query = self.db.query(ServiceCategoryModel)\
            .filter(
                and_(
                    or_(
                        ServiceCategoryModel.category_name.like(f"%{keyword}%"),
                        ServiceCategoryModel.description.like(f"%{keyword}%")
                    ),
                    ServiceCategoryModel.status == 1,
                    ServiceCategoryModel.is_deleted == 0
                )
            )\
            .order_by(asc(ServiceCategoryModel.sort_num))\
            .limit(10)

        # 执行查询
        categories = query.all()
        return [ServiceCategory.model_validate(c.__dict__) for c in categories]

    # ===================== 私有方法：构建树形结构 =====================
    def _build_category_tree(self, categories: List[ServiceCategory]) -> List[ServiceCategory]:
        """
        构建类别树
        """
        # 按父ID分组所有类别
        children_map: Dict[int, List[ServiceCategory]] = {}
        for cat in categories:
            if cat.parent_id:
                if cat.parent_id not in children_map:
                    children_map[cat.parent_id] = []
                children_map[cat.parent_id].append(cat)
        
        # 递归设置子类别
        trees = []
        for cat in categories:
            if not cat.parent_id:
                self._fill_children(cat, children_map)
                trees.append(cat)
        return trees

    def _fill_children(self, category: ServiceCategory, children_map: Dict[int, List[ServiceCategory]]) -> ServiceCategory:
        """
        递归填充子类别
        """
        children = children_map.get(category.id)
        
        if children:
            # 递归处理每个子类别
            processed_children = [self._fill_children(child, children_map) for child in children]
            category.children = processed_children
            category.has_children = 1
        else:
            category.children = None
            category.has_children = 0
        
        return category