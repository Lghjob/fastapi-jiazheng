from sqlalchemy import Column, Integer, String, DateTime, BigInteger,func
from datetime import datetime
from config.database import BaseModel 

class ServiceCategoryModel(BaseModel):
    __tablename__ = "service_category"

    # 类别ID bigint
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="类别ID")
    
    # 类别名称 varchar(50)
    category_name = Column(String(50), nullable=True, comment="类别名称")
    
    # 父类别ID bigint
    parent_id = Column(BigInteger, nullable=True, comment="父类别ID")
    
    # 描述 varchar(500)
    description = Column(String(500), nullable=True, comment="描述")
    
    # 图标URL varchar(200)
    icon = Column(String(200), nullable=True, comment="图标URL")
    
    # 排序号 int
    sort_num = Column(Integer, default=1, comment="排序号")
    
    # 状态 tinyint
    status = Column(Integer, default=1, comment="状态(0:禁用,1:正常)")
    
    # 创建时间
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
    
    # 更新时间
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    
    # 是否删除
    is_deleted = Column(Integer, default=0, comment="是否删除(0:未删除,1:已删除)")