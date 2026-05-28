from sqlalchemy import Column, Integer, DateTime,func
from datetime import datetime
from config.database import BaseModel 

class RoleMenuModel(BaseModel):
    __tablename__ = "sys_role_menu"

    role_id = Column(Integer, nullable=False, comment="角色ID",primary_key=True)
    menu_id = Column(Integer, nullable=False, comment="菜单ID",primary_key=True)
    created_time = Column(DateTime, default=func.now())