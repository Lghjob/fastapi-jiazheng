import logging
from typing import Optional
from sqlalchemy.orm import Session

# 导入你项目已有的文件
from schemas.user import User
from utils.exceptions.service_exception import ServiceException

# 导入 SQLAlchemy Model
from models.user_model import UserModel

# 日志配置
logger = logging.getLogger(__name__)

class UserDetailService:
    """
    用户认证服务
    """
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str) -> User:
        """
        根据用户名加载用户信息
        """
        # 根据用户名查询用户
        user = self.db.query(UserModel)\
            .filter(UserModel.username == username)\
            .first()

        if not user:
            logger.warning(f"用户不存在: {username}")
            raise ServiceException("用户不存在")

        user_Schema = User.model_validate(user)
        logger.info(f"加载用户信息成功: {username}")
        return user_Schema