from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from config.database import BaseModel,TimestampMixin


class UserModel(BaseModel):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False, comment="用户名")
    password = Column(String(100), nullable=False, comment="密码(加密存储)")
    email = Column(String(100), nullable=False, comment="邮箱")
    phone = Column(String(20), nullable=True, comment="手机号")
    role_code = Column(String(20), nullable=True, comment="角色编码(USER/ADMIN)")
    name = Column(String(50), nullable=True, comment="姓名")
    id_card = Column(String(50), nullable=True, comment="身份证号")
    address = Column(String(200), nullable=True, comment="地址")
    avatar = Column(String(255), nullable=True, comment="头像URL")
    gender = Column(Integer, nullable=True, comment="性别(0:女,1:男)")
    age = Column(Integer, nullable=True, comment="年龄")
    status = Column(Integer, default=1, comment="状态(0:禁用,1:正常)")
    create_time = Column(DateTime, server_default=func.now(), comment="创建时间")
    update_time = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="更新时间")
    # 非数据库字段
    # 在 Pydantic Schema 里定义，这里不需要