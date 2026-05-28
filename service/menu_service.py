import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

# 导入你项目已有的文件
from schemas.menu import Menu
from schemas.role import Role
from schemas.role_menu import RoleMenu
from utils.exceptions.service_exception import ServiceException

# 导入 SQLAlchemy Model
from models.menu_model import MenuModel
from models.role_model import RoleModel
from models.role_menu_model import RoleMenuModel

# 日志配置
logger = logging.getLogger(__name__)

class MenuService:
    def __init__(self, db: Session):
        self.db = db

    # ===================== 核心功能：为角色分配菜单 =====================
    def assign_menus_to_role(self, role_id: int, menu_ids: List[int]) -> None:
        """
        为角色分配菜单
        """
        try:
            # 1. 检查角色是否存在
            role = self.db.get(RoleModel, role_id)
            if not role:
                raise ServiceException("角色不存在")

            # 2. 删除原有的角色菜单关联
            self.db.query(RoleMenuModel)\
                .filter(RoleMenuModel.role_id == role_id)\
                .delete(synchronize_session=False)

            # 3. 批量插入新的角色菜单关联
            for menu_id in menu_ids:
                role_menu = RoleMenuModel(
                    role_id=role_id,
                    menu_id=menu_id,
                    created_time=datetime.now()
                )
                self.db.add(role_menu)

            self.db.commit()
            logger.info(f"为角色 {role_id} 分配菜单成功: {menu_ids}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"为角色分配菜单失败: {str(e)}")
            raise e

    # ===================== 菜单CRUD =====================
    def save_menu(self, menu: Menu) -> None:
        """
        保存或更新菜单
        """
        now = datetime.now()
        if menu.id:
            # 更新
            existing_menu = self.db.get(MenuModel, menu.id)
            if not existing_menu:
                raise ServiceException("菜单不存在")
            
            for key, value in menu.model_dump(exclude_unset=True).items():
                setattr(existing_menu, key, value)
            existing_menu.updated_time = now
        else:

            db_menu = MenuModel(**menu.model_dump(exclude={'children', 'has_children'}))
            db_menu.created_time = now
            db_menu.updated_time = now
            self.db.add(db_menu)

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise ServiceException("更新失败" if menu.id else "新增失败")

    def update_menu(self, menu: Menu) -> None:
        """
        更新菜单
        """
        existing_menu = self.db.get(MenuModel, menu.id)
        if not existing_menu:
            raise ServiceException("菜单不存在")

        for key, value in menu.model_dump(exclude_unset=True).items():
            setattr(existing_menu, key, value)
        existing_menu.updated_time = datetime.now()

        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise ServiceException("更新失败")

    def delete_by_id(self, id: int) -> None:
        """
        删除菜单
        """
        # 检查是否存在子菜单
        child_count = self.db.query(MenuModel)\
            .filter(MenuModel.pid == id)\
            .count()
        if child_count > 0:
            raise ServiceException("存在子菜单,不能删除")

        menu = self.db.get(MenuModel, id)
        if not menu:
            raise ServiceException("删除失败")

        try:
            self.db.delete(menu)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise ServiceException("删除失败")

    def delete_batch(self, ids: List[int]) -> None:
        """
        批量删除菜单
        """
        try:
            # 检查是否存在子菜单
            child_count = self.db.query(MenuModel)\
                .filter(MenuModel.pid.in_(ids))\
                .count()
            if child_count > 0:
                raise ServiceException("选中的菜单中存在子菜单,不能删除")

            # 批量删除
            self.db.query(MenuModel)\
                .filter(MenuModel.id.in_(ids))\
                .delete(synchronize_session=False)

            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise ServiceException("删除失败")

    # ===================== 菜单查询 =====================
    def get_by_id(self, id: int) -> Menu:
        """
        根据ID查询菜单
        """
        menu = self.db.get(MenuModel, id)
        if not menu:
            raise ServiceException("菜单不存在")
        return Menu.model_validate(menu)

    def get_all_menu_tree(self) -> List[Menu]:
        """
        获取所有菜单树
        """
        all_menus = self.db.query(MenuModel)\
            .order_by(asc(MenuModel.sort_num))\
            .all()
        menu_list = [Menu.model_validate(m) for m in all_menus]
        return self._build_menu_tree(menu_list)

    def get_parent_menu_page(self, current_page: int, size: int):
        """
        分页查询父级菜单
        """
        query = self.db.query(MenuModel)\
            .filter(MenuModel.pid.is_(None))\
            .order_by(asc(MenuModel.sort_num))

        total = query.count()
        offset = (current_page - 1) * size
        records = query.offset(offset).limit(size).all()

        return {
            "records": [Menu.model_validate(r) for r in records],
            "total": total,
            "page_num": current_page,
            "page_size": size
        }

    def get_children_menus(self, parent_id: int) -> List[Menu]:
        """
        查询子菜单
        """
        menus = self.db.query(MenuModel)\
            .filter(MenuModel.pid == parent_id)\
            .order_by(asc(MenuModel.sort_num))\
            .all()
        return [Menu.model_validate(m) for m in menus]

    def get_menus_by_role_code(self, role_code: str) -> List[Menu]:
        """
        根据角色编码获取菜单
        """
        if not role_code or not role_code.strip():
            logger.warning("Role code is null or empty")
            return []

        try:
            # 1. 获取角色
            role = self.db.query(RoleModel)\
                .filter(RoleModel.code == role_code)\
                .first()
            if not role:
                logger.warning(f"Role not found for code: {role_code}")
                return []

            # 2. 获取角色菜单关联
            role_menus = self.db.query(RoleMenuModel)\
                .filter(RoleMenuModel.role_id == role.id)\
                .all()
            if not role_menus:
                logger.info(f"No menus found for role: {role_code}")
                return []

            # 3. 获取菜单ID列表
            menu_ids = list({rm.menu_id for rm in role_menus if rm.menu_id is not None})
            if not menu_ids:
                logger.warning(f"No valid menu IDs found for role: {role_code}")
                return []

            # 4. 批量查询菜单
            all_menu_ids = set(menu_ids)

            # 自动把父菜单全部加进来
            changed = True
            while changed:
                changed = False
                parents = self.db.query(MenuModel.pid)\
                    .filter(MenuModel.id.in_(all_menu_ids), MenuModel.pid.isnot(None))\
                    .all()
                parent_ids = {p[0] for p in parents if p[0]}
                new_ids = parent_ids - all_menu_ids
                if new_ids:
                    all_menu_ids.update(new_ids)
                    changed = True

            menus = self.db.query(MenuModel)\
                .filter(MenuModel.id.in_(all_menu_ids))\
                .order_by(asc(MenuModel.sort_num))\
                .all()
            # 5. 构建树形结构
            menu_list = [Menu.model_validate(m) for m in menus]
            return self._build_menu_tree(menu_list)

        except Exception as e:
            logger.error(f"Error in getMenusByRoleCode for role {role_code}: {str(e)}")
            return []

    # ===================== 私有方法：构建菜单树 =====================
    def _build_menu_tree(self, menus: List[Menu]) -> List[Menu]:
        """
        构建菜单树
        """
        trees = []
        for menu in menus:
            if menu.pid == 0 or menu.pid is None:
                menu.children = self._get_children(menu, menus)
                trees.append(menu)
        return trees

    def _get_children(self, parent: Menu, all_menus: List[Menu]) -> List[Menu]:
        """
        递归获取子菜单
        """
        children = []
        for menu in all_menus:
            if parent.id == menu.pid:
                menu.children = self._get_children(menu, all_menus)
                children.append(menu)
        return children