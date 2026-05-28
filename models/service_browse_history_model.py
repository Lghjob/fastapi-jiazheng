from sqlalchemy import Column, Integer, DateTime, BigInteger,func
from datetime import datetime
from config.database import BaseModel 

class ServiceBrowseHistoryModel(BaseModel):
    __tablename__ = "browse_history"

    # 记录ID Long → BigInteger
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="记录ID")
    
    # 用户ID Long → BigInteger
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    
    # 服务项目ID Long → BigInteger
    service_id = Column(BigInteger, nullable=False, comment="服务项目ID")
    
    # 最后浏览时间（自动更新）
    last_browse_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment="最后浏览时间")