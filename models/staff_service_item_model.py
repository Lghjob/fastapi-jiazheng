from sqlalchemy import Column, Integer, DateTime,func
from datetime import datetime
from config.database import BaseModel

class StaffServiceItemModel(BaseModel):
    __tablename__ = "staff_service_item"

    id = Column(Integer, primary_key=True, autoincrement=True)
    staff_id = Column(Integer, nullable=True, comment="服务人员ID")
    service_id = Column(Integer, nullable=True, comment="服务项目ID")
    status = Column(Integer, default=1, comment="状态 1启用 0禁用")
    create_time = Column(DateTime, default=func.now())
    update_time = Column(DateTime, default=func.now(), onupdate=func.now())