from sqlalchemy import Column, Integer, String, DateTime,func
from datetime import datetime
from config.database import BaseModel 

class RoleModel(BaseModel):
    __tablename__ = "sys_role"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(50), nullable=True, comment="角色编码")
    name = Column(String(100), nullable=True, comment="角色名称")
    description = Column(String(500), nullable=True, comment="角色描述")
    created_time = Column(DateTime, default=func.now())
    updated_time = Column(DateTime, default=func.now(), onupdate=func.now())
    is_deleted = Column(Integer, default=0, comment="是否删除 0否 1是")