from sqlalchemy import Column, Integer, String
from config.database import BaseModel,TimedstampMixin 

class MenuModel(BaseModel,TimedstampMixin):
    __tablename__ = "sys_menu"

    id = Column(Integer, primary_key=True, autoincrement=True)
    pid = Column(Integer, nullable=True, comment="父级菜单ID")
    name = Column(String(100), nullable=True, comment="菜单名称")
    path = Column(String(255), nullable=True, comment="路由路径")
    component = Column(String(255), nullable=True, comment="组件路径")
    description = Column(String(255))
    icon = Column(String(100), nullable=True, comment="菜单图标")
    sort_num = Column(Integer, default=0, comment="排序号")
    hidden = Column(Integer, default=0, comment="是否隐藏 0-显示 1-隐藏")