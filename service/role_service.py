import logging
from typing import List, Optional, Set
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc

# 导入你项目已有的文件
from schemas.role import Role
from schemas.role_menu import RoleMenu
from schemas.menu import Menu
from schemas.user import User
from utils.exceptions.service_exception import ServiceException

# 导入 SQLAlchemy Model
from models.role_model import RoleModel
from models.role_menu_model import RoleMenuModel
from models.menu_model import MenuModel
from models.user_model import UserModel

# 日志配置
logger = logging.getLogger(__name__)

class RoleService:
    # 系统保留角色编码常量
    PROTECTED_ROLE_CODES = {"USER", "ADMIN"}

    def __init__(self, db: Session):
        self.db = db

    # ===================== 角色CRUD =====================
    def create_role(self, role: Role) -> None:
        """
        创建角色
        """
        try:
            # 检查角色编码是否已存在
            if self._is_code_exists(role.code):
                raise ServiceException("角色编码已存在")

            now = datetime.now()
            
            # 排除非数据库字段和不需要手动赋值的字段
            role_data = role.model_dump(
                exclude={"menu_list", "created_time", "updated_time", "id"}
            )
            
            # 手动处理 is_deleted 给默认值
            if role_data.get("is_deleted") in [None, ""]:
                role_data["is_deleted"] = 0

            db_role = RoleModel(
                **role_data,
                created_time=now,
                updated_time=now
            )
            self.db.add(db_role)
            self.db.commit()
            logger.info(f"角色创建成功: {role.name}")
            
        except ServiceException as e:
            self.db.rollback()
            raise e
        except Exception as e:
            self.db.rollback()
            logger.error(f"角色创建失败: {str(e)}")
            raise ServiceException("角色创建失败")
        

    def update_role(self, role: Role) -> None:
        """
        更新角色
        """
        try:
            # 检查角色是否存在
            existing_role = self.db.get(RoleModel, role.id)
            if not existing_role:
                raise ServiceException("角色不存在")

            # 检查是否是系统保留角色
            if existing_role.code in self.PROTECTED_ROLE_CODES:
                # 不允许修改角色编码
                if existing_role.code != role.code:
                    raise ServiceException("系统保留角色不允许修改角色编码")
            elif existing_role.code != role.code and self._is_code_exists(role.code):
                # 如果不是系统角色且修改了编码，检查新编码是否已存在
                raise ServiceException("角色编码已存在")

            # 更新数据
            for key, value in role.model_dump(exclude_unset=True).items():
                setattr(existing_role, key, value)
            existing_role.updated_time = datetime.now()

            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise ServiceException("角色更新失败")

    def delete_role(self, id: int) -> None:
        """
        删除角色（软删除）
        """
        try:
            # 检查角色是否存在且未删除
            role = self.db.query(RoleModel)\
                .filter(
                    RoleModel.id == id,
                    RoleModel.is_deleted == 0
                )\
                .first()
            if not role:
                raise ServiceException("角色不存在")

            # 检查是否是系统保留角色
            if role.code in self.PROTECTED_ROLE_CODES:
                raise ServiceException("系统保留角色不允许删除")

            # 检查是否有用户关联此角色
            user_count = self.db.query(UserModel)\
                .filter(UserModel.role_code == role.code)\
                .count()
            if user_count > 0:
                raise ServiceException("该角色下存在用户,不能删除")

            # 删除角色菜单关联
            self.db.query(RoleMenuModel)\
                .filter(RoleMenuModel.role_id == id)\
                .delete(synchronize_session=False)

            # 执行软删除
            role.is_deleted = 1
            role.updated_time = datetime.now()

            self.db.commit()
            logger.info(f"角色软删除成功: {id}")
        except ServiceException as e:
            self.db.rollback()
            raise e
        except Exception as e:
            self.db.rollback()
            logger.error(f"角色删除失败: {str(e)}")
            raise ServiceException("角色删除失败")

    def batch_delete_roles(self, ids: List[int]) -> None:
        """
        批量删除角色（软删除）
        """
        if not ids:
            return

        try:
            # 检查角色是否存在
            roles = self.db.query(RoleModel)\
                .filter(
                    RoleModel.id.in_(ids),
                    RoleModel.is_deleted == 0
                )\
                .all()
            if len(roles) != len(ids):
                raise ServiceException("部分角色不存在")

            # 检查是否包含系统保留角色
            has_protected = any(r.code in self.PROTECTED_ROLE_CODES for r in roles)
            if has_protected:
                raise ServiceException("选中的角色包含系统保留角色，不能删除")

            # 检查是否有用户关联这些角色
            role_codes = [r.code for r in roles]
            user_count = self.db.query(UserModel)\
                .filter(UserModel.role_code.in_(role_codes))\
                .count()
            if user_count > 0:
                raise ServiceException("选中的角色中存在关联用户,不能删除")

            # 批量删除角色菜单关联
            self.db.query(RoleMenuModel)\
                .filter(RoleMenuModel.role_id.in_(ids))\
                .delete(synchronize_session=False)

            # 执行批量软删除
            now = datetime.now()
            for role in roles:
                role.is_deleted = 1
                role.updated_time = now

            self.db.commit()
            logger.info(f"批量软删除角色成功: count={len(ids)}")
        except Exception as e:
            self.db.rollback()
            raise e

    # ===================== 角色查询 =====================
    def get_role_by_id(self, id: int) -> Role:
        """
        根据ID查询角色
        """
        role = self.db.get(RoleModel, id)
        if not role:
            raise ServiceException("角色不存在")
        return Role.model_validate(role)

    def get_role_by_code(self, code: str) -> Optional[Role]:
        """
        根据编码查询角色
        """
        role = self.db.query(RoleModel)\
            .filter(RoleModel.code == code)\
            .first()
        return Role.model_validate(role) if role else None

    def get_all_roles(self) -> List[Role]:
        """
        获取所有角色
        """
        roles = self.db.query(RoleModel)\
            .filter(RoleModel.is_deleted == 0)\
            .order_by(asc(RoleModel.code))\
            .all()
        return [Role.model_validate(r) for r in roles]
        
    def get_roles_by_page(
        self,
        code: Optional[str],
        name: Optional[str],
        currentPage: int = 1,
        pageSize: int = 10
    ):
        """
        分页查询角色
        """
        query = self.db.query(RoleModel).filter(RoleModel.is_deleted == 0)

        if code and code.strip():
            query = query.filter(RoleModel.code.like(f"%{code}%"))
        if name and name.strip():
            query = query.filter(RoleModel.name.like(f"%{name}%"))

        query = query.order_by(asc(RoleModel.code))

        total = query.count()
        offset = (currentPage - 1) * pageSize
        records = query.offset(offset).limit(pageSize).all()

        return {
                "records": [Role.model_validate(r) for r in records],
                "total": total,
                "current": currentPage,
                "size": pageSize
            }
    # ===================== 角色菜单管理 =====================
    def get_role_menus(self, roleId: int) -> List[Menu]:
        """
        获取角色菜单
        """
        # 获取角色菜单关联
        role_menus = self.db.query(RoleMenuModel)\
            .filter(RoleMenuModel.role_id == roleId)\
            .all()

        # 获取菜单ID列表
        menu_ids = [rm.menu_id for rm in role_menus if rm.menu_id]
        if not menu_ids:
            return []

        # 查询菜单信息
        menus = self.db.query(MenuModel)\
            .filter(MenuModel.id.in_(menu_ids))\
            .order_by(asc(MenuModel.sort_num))\
            .all()
        return [Menu.model_validate(m) for m in menus]

    def assign_menus_to_role(self, roleId: int, menuIds: List[int]) -> None:
        """
        为角色分配菜单（自动添加必要的父菜单）s
        """
        try:
            # 检查角色是否存在
            role = self.db.get(RoleModel, roleId)
            if not role:
                raise ServiceException("角色不存在")

            # 如果menuIds为空，直接清空角色菜单关联并返回
            if not menuIds:
                self.db.query(RoleMenuModel)\
                    .filter(RoleMenuModel.role_id == roleId)\
                    .delete(synchronize_session=False)
                self.db.commit()
                return

            # 获取所有选中菜单
            selected_menus = self.db.query(MenuModel)\
                .filter(MenuModel.id.in_(menuIds))\
                .all()
            if len(selected_menus) != len(menuIds):
                raise ServiceException("存在无效的菜单ID")

            # 收集所有需要添加的菜单ID（包括必要的父菜单）
            all_menu_ids: Set[int] = set(menuIds)

            # 检查每个选中菜单的父菜单
            for menu in selected_menus:
                parent_id = menu.pid
                while parent_id and parent_id != 0:
                    # 检查父菜单是否已分配或在待分配列表中
                    if parent_id not in all_menu_ids:
                        # 查询父菜单
                        parent_menu = self.db.get(MenuModel, parent_id)
                        if not parent_menu:
                            break
                        all_menu_ids.add(parent_id)
                        parent_id = parent_menu.pid
                    else:
                        break

            # 删除原有的角色菜单关联
            self.db.query(RoleMenuModel)\
                .filter(RoleMenuModel.role_id == roleId)\
                .delete(synchronize_session=False)

            # 批量插入新的角色菜单关联
            now = datetime.now()
            for menu_id in all_menu_ids:
                role_menu = RoleMenuModel(
                    role_id=roleId,
                    menu_id=menu_id,
                    created_time=now
                )
                self.db.add(role_menu)

            # 更新角色的更新时间
            role.updated_time = now

            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise e

    def get_role_menu_ids(self, roleId: int) -> List[int]:
        """
        获取角色菜单ID列表
        """
        role_menus = self.db.query(RoleMenuModel)\
            .filter(RoleMenuModel.role_id == roleId)\
            .all()
        return [rm.menu_id for rm in role_menus if rm.menu_id]

    # ===================== 私有方法 =====================
    def _is_code_exists(self, code: str) -> bool:
        """
        检查角色编码是否存在
        """
        count = self.db.query(RoleModel)\
            .filter(RoleModel.code == code)\
            .count()
        return count > 0