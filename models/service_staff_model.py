from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Text, JSON,func
from datetime import datetime
from config.database import BaseModel,TimestampMixin


class ServiceStaffModel(BaseModel,TimestampMixin):
    __tablename__ = "service_staff"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=True, comment="关联用户ID")
    service_type = Column(JSON, nullable=True, comment="服务类型")
    experience = Column(Integer, nullable=True, comment="工作年限")
    rating = Column(DECIMAL(2,1), nullable=True, comment="综合评分")
    description = Column(Text, nullable=True, comment="个人描述")
    certificates = Column(JSON, nullable=True, comment="证书信息")
    work_area = Column(String(200), nullable=True, comment="服务区域")
    total_orders = Column(Integer, default=0, comment="总订单数")
    completion_rate = Column(DECIMAL(5,2), default=0, comment="完成率")
    is_deleted = Column(Integer, default=0, comment="是否删除 0否 1是")