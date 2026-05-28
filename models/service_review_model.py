from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, Text, BigInteger,func
from datetime import datetime
from config.database import BaseModel

class ServiceReviewModel(BaseModel):
    __tablename__ = "service_review"

    id = Column(BigInteger, primary_key=True, autoincrement=True, comment="评价ID")
    order_id = Column(BigInteger, nullable=True, comment="订单ID")
    user_id = Column(BigInteger, nullable=True, comment="用户ID")
    staff_id = Column(BigInteger, nullable=True, comment="服务人员ID")

    # 2. 三项评分（1-5分）
    skill_rating = Column(Integer, nullable=True, comment="技能满意度评分(1-5)")
    attitude_rating = Column(Integer, nullable=True, comment="服务态度评分(1-5)")
    experience_rating = Column(Integer, nullable=True, comment="综合体验评分(1-5)")

    # 3. 总体评分 BigDecimal → DECIMAL(10,1)
    overall_rating = Column(DECIMAL(10,1), nullable=True, comment="总体评分")

    # 评价内容
    content = Column(Text, nullable=True, comment="评价内容")

    # 4. 创建时间 + 更新时间
    create_time = Column(DateTime, default=func.now(), comment="创建时间")
    update_time = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")