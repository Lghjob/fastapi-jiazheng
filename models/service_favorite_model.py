from sqlalchemy import Column, Integer, DateTime, BigInteger,func
from datetime import datetime
from config.database import BaseModel 

class ServiceFavoriteModel(BaseModel):
    __tablename__ = "user_favorite"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="收藏ID")
    user_id = Column(BigInteger, nullable=False, comment="用户ID")
    service_id = Column(BigInteger, nullable=False, comment="服务项目ID")
    
    # 时间一致
    create_time = Column(DateTime, default=func.now(), comment="创建时间")