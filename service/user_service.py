import logging
import os
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func

# 密码加密
from passlib.context import CryptContext

# 项目内部导入
from schemas.user import User
from schemas.menu import Menu
from schemas.service_staff import ServiceStaff
from schemas.user_dto import UserPasswordUpdateDTO
from utils.exceptions.service_exception import ServiceException
from utils.enums.account_status import AccountStatus
from utils.jwt_token_utils import JwtTokenUtils
# from passlib.hash import bcrypt
# SQLAlchemy Model
from models.user_model import UserModel
from models.service_staff_model import ServiceStaffModel

# 其他服务
from service.menu_service import MenuService
from service.service_staff_service import ServiceStaffService

logger = logging.getLogger(__name__)


class UserService:
    STAFF_ROLE = "STAFF"
    DEFAULT_PWD = os.getenv("USER_DEFAULT_PASSWORD", "123456")

    def __init__(self, db: Session):
        self.db = db
        # 密码加密器
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.menu_service = MenuService(db)
        self.service_staff_service = ServiceStaffService(db)

    # ===================== 1. 获取用户详情 =====================
    def get_user_by_id(self, id: int) -> UserModel:
        user = self.db.query(UserModel).filter(UserModel.id == id).first()
        if not user:
            raise ServiceException("用户不存在")
        return user

    # ===================== 2. 根据用户名查询用户=====================
    def get_by_username(self, username: str) -> UserModel:
        user = self.db.query(UserModel).filter(UserModel.username == username).first()
        if not user:
            raise ServiceException("用户不存在")
        return user

    # ===================== 3. 分页查询用户列表 =====================
    def get_users_by_page(self, username: Optional[str], role_code: Optional[str],
                          current_page: int, size: int):
        query = self.db.query(UserModel)

        if username:
            query = query.filter(UserModel.username.like(f"%{username}%"))
        if role_code:
            query = query.filter(UserModel.role_code == role_code)

        # 分页（对应 MyBatis-Plus Page）
        total = query.count()
        offset = (current_page - 1) * size
        records = query.offset(offset).limit(size).all()

        #   转换为 Schema
        user_list = [User.model_validate(item, from_attributes=True) for item in records]

        return {
            "records": user_list,
            "total": total,
            "current": current_page,
            "size": size
        }

    # ===================== 4. 根据角色查找用户（分页） =====================
    def get_users_by_role(self, role_code: str, page_num: int, page_size: int):
        if not role_code:
            raise ServiceException("角色编码不能为空")

        query = self.db.query(UserModel)\
            .filter(UserModel.role_code == role_code)\
            .order_by(desc(UserModel.created_time))

        total = query.count()
        offset = (page_num - 1) * page_size
        records = query.offset(offset).limit(page_size).all()

        #   转换为 Schema
        user_list = [User.model_validate(item, from_attributes=True) for item in records]

        return {
            "records": user_list,
            "total": total,
            "current": page_num,
            "size": page_size
        }

    # ===================== 5. 删除用户  =====================
    def delete_user_by_id(self, id: int) -> None:
        # 检查用户
        user = self.get_user_by_id(id)

        # 检查是否是服务人员
        if self.STAFF_ROLE == user.role_code:
            raise ServiceException("该用户是服务人员，不能直接删除")

        # 执行删除
        try:
            self.db.delete(user)
            self.db.commit()
            logger.info(f"用户删除成功: {id}")
        except Exception as e:
            self.db.rollback()
            raise ServiceException("删除用户失败")

    # ===================== 6. 批量删除用户  =====================
    def batch_delete_users(self, ids: List[int]) -> None:
        if not ids:
            return

        # 校验服务人员
        for user_id in ids:
            user = self.db.query(UserModel).filter(UserModel.id == user_id).first()
            if user and self.STAFF_ROLE == user.role_code:
                raise ServiceException("选中的用户中存在服务人员，不能删除")
            
            staff = self.service_staff_service.get_service_staff_by_user_id(user_id)
            if staff:
                raise ServiceException("选中的用户中存在服务人员，不能删除")

        # 批量删除
        try:
            self.db.query(UserModel).filter(UserModel.id.in_(ids)).delete(synchronize_session=False)
            self.db.commit()
            logger.info(f"批量删除用户成功: count={len(ids)}")
        except Exception as e:
            self.db.rollback()
            raise ServiceException("批量删除用户失败")

    # ===================== 7. 用户登录 =====================
    def login(self, login_dto):
        # 查询用户
        db_user = self.get_by_username(login_dto.username)

        # 状态校验
        if db_user.status == 0:
            raise ServiceException("账号已禁用")

        # 密码校验
        try:
            pwd = login_dto.password[:72]
            hashed_pwd = str(db_user.password)

            # ok = bcrypt.verify(pwd, hashed_pwd)
            ok = self.pwd_context.verify(pwd, hashed_pwd)
        except Exception as e:
            logger.error("密码校验异常")
            raise ServiceException("系统异常")

        if not ok:
            raise ServiceException("用户名或密码错误")

        # 获取菜单（如果报错会是空数组）
        menus = self.menu_service.get_menus_by_role_code(db_user.role_code)

        # 生成 token
        token = JwtTokenUtils.gen_token(str(db_user.id), hashed_pwd)

        # =====================返回格式 =====================
        return {
            "id": db_user.id,
            "username": db_user.username,
            "email": db_user.email,
            "phone": db_user.phone,
            "roleCode": db_user.role_code,
            "name": db_user.name,
            "idCard": db_user.id_card,
            "address": db_user.address,
            "avatar": db_user.avatar,
            "gender": db_user.gender,
            "age": db_user.age,
            "status": db_user.status,
            "createTime": db_user.create_time.isoformat() if db_user.create_time else None,
            "updateTime": db_user.update_time.isoformat() if db_user.update_time else None,
            "token": token,
            "menuList": menus
        }

    # ===================== 8. 根据角色查询用户列表 =====================
    def get_user_by_role(self, role_code: str) -> List[User]:
        users = self.db.query(UserModel).filter(UserModel.role_code == role_code).all()
        if not users:
            raise ServiceException("未找到该角色的用户")
        
        #  转换为 Schema
        return [User.model_validate(item, from_attributes=True) for item in users]

    # ===================== 9. 创建用户 =====================
    def create_user(self, user: User) -> None:
        # 校验用户名重复
        exists = self.db.query(UserModel).filter(UserModel.username == user.username).first()
        if exists:
            raise ServiceException("用户名已存在")

        # 密码处理
        password = user.password if user.password else self.DEFAULT_PWD
        encrypt_pwd = self.pwd_context.hash(password)

        # 构建 
        db_user = UserModel(
            **user.model_dump(exclude={"password", "token", "menu_list", "create_time", "update_time"}), #这里除了 password，还要排除 token、menu_list 等非数据库字段！
            password=encrypt_pwd,
            create_time=datetime.now()
        )

        try:
            self.db.add(db_user)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise ServiceException("用户创建失败")

    # ===================== 10. 更新用户信息  =====================
    def update_user(self, user: User) -> None:
        exist_user = self.get_user_by_id(user.id or 0)
        
        # 服务人员不允许修改角色
        if self.STAFF_ROLE == exist_user.role_code and self.STAFF_ROLE != user.role_code:
            raise ServiceException("服务人员用户不能修改角色")

        # 更新字段
        for key, value in user.model_dump(exclude_unset=True).items():
            setattr(exist_user, key, value)

        try:
            self.db.commit()
            logger.info(f"用户信息更新成功: {user.id}")
        except Exception as e:
            self.db.rollback()
            raise ServiceException("更新用户失败")

    # ===================== 11. 批量删除 =====================
    def delete_batch(self, ids: List[int]) -> None:
        try:
            self.db.query(UserModel).filter(UserModel.id.in_(ids)).delete(synchronize_session=False)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise ServiceException("批量删除失败")

    # ===================== 12. 获取所有用户 =====================
    def get_user_list(self) -> List[User]:
        users = self.db.query(UserModel).all()
        if not users:
            raise ServiceException("未找到任何用户")
        
        #   转换为 Schema
        return [User.model_validate(item, from_attributes=True) for item in users]

    # ===================== 13. 修改密码  =====================
    def update_password(self, id: int, update_dto: UserPasswordUpdateDTO) -> None:
        user = self.get_user_by_id(id)

        # 旧密码校验
        if not self.pwd_context.verify(update_dto.old_password, user.password):
            raise ServiceException("原密码错误")

        # 更新新密码
        user.password = self.pwd_context.hash(update_dto.new_password)
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise ServiceException("密码修改失败")

    # ===================== 14. 忘记密码  =====================
    def forget_password(self, email: str, new_password: str) -> None:
        user = self.db.query(UserModel).filter(UserModel.email == email).first()
        if not user:
            raise ServiceException("邮箱不存在")

        user.password = self.pwd_context.hash(new_password)
        try:
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            raise ServiceException("密码重置失败")

    # ===================== 15. 重置密码  =====================
    def reset_password(self, id: int) -> str:
        user = self.get_user_by_id(id)

        # 重置为默认密码
        user.password = self.pwd_context.hash(self.DEFAULT_PWD)
        try:
            self.db.commit()
            logger.info(f"用户密码重置成功: {id}")
            return self.DEFAULT_PWD
        except Exception as e:
            self.db.rollback()
            raise ServiceException("密码重置失败")