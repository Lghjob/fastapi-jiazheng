from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from datetime import datetime
from config.database import BaseModel,TimestampMixin

class BannerModel(BaseModel,TimestampMixin):
    __tablename__ = "banner"

    # 主键ID bigint
    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="主键ID")
    # 轮播图标题 varchar(100)
    title = Column(String(100), nullable=True, comment="轮播图标题")
    # 图片URL varchar(255)
    image_url = Column(String(255), nullable=True, comment="图片URL")
    # 图片描述 varchar(255) 
    description = Column(String(255), nullable=True, comment="图片描述")
    # 标签 varchar(50)
    tag = Column(String(50), nullable=True, comment="标签（如：新人专享、热门活动、限时特惠等）")
    # 状态 tinyint(1) 0禁用 1启用
    status = Column(Integer, default=1, comment="状态（0-禁用，1-启用）")