from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Text, BigInteger,func
from datetime import datetime
from config.database import BaseModel

class ServiceItemModel(BaseModel):
    __tablename__ = "service_item"

    # 服务ID bigint
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="服务ID")
    
    # 类别ID bigint
    category_id = Column(BigInteger, nullable=True, comment="类别ID")
    
    # 服务标题 varchar(100)
    title = Column(String(100), nullable=True, comment="服务标题")
    
    # 服务描述 text
    description = Column(Text, nullable=True, comment="服务描述")
    
    # 价格 decimal(10,2) 金钱必须用这个
    price = Column(DECIMAL(10, 2), nullable=True, comment="服务价格")
    
    # 状态 tinyint
    status = Column(Integer, default=1, comment="状态(0:下架,1:上架)")
    
    # 逻辑删除
    is_deleted = Column(Integer, default=0, comment="是否删除(0:未删除,1:已删除)")

    create_time = Column(DateTime, default=datetime.now, comment="创建时间")
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")