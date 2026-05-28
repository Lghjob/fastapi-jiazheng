from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Any
from schemas.service_order import ServiceOrder
from schemas.base import BaseSchema
# 服务评价
class ServiceReview(BaseSchema):
    """
    服务评价
    作用：存储用户对服务的评价（评分、内容、关联订单/用户/服务人员）
    """
    # 评价ID
    id: Optional[int] = None

    # 订单ID 非空
    order_id: int = Field(
        ...,
        description="订单ID"
    )

    # 用户ID 非空
    user_id: int = Field(
        ...,
        description="用户ID"
    )

    # 服务人员ID 非空
    staff_id: int = Field(
        ...,
        description="服务人员ID"
    )

    # 技能满意度评分(1-5) 非空 + 范围1-5
    skill_rating: int = Field(
        ...,
        description="技能满意度评分(1-5)",
        ge=1,
        le=5
    )

    # 服务态度评分(1-5) 非空 + 范围1-5
    attitude_rating: int = Field(
        ...,
        description="服务态度评分(1-5)",
        ge=1,
        le=5
    )

    # 综合体验评分(1-5) 非空 + 范围1-5
    experience_rating: int = Field(
        ...,
        description="综合体验评分(1-5)",
        ge=1,
        le=5
    )

    # 总体评分
    overall_rating: Optional[float] = None

    # 评价内容 最大长度1000
    content: Optional[str] = Field(
        None,
        description="评价内容",
        max_length=1000
    )

    # 创建时间
    create_time: Optional[datetime] = None

    # 更新时间
    update_time: Optional[datetime] = None

    # ===================== 关联信息（非数据库字段） =====================
    # 等你迁移完 后，把下面的 Any 替换成具体类名
    user: Optional[Any] = None  
    staff: Optional[Any] = None 
    order: Optional[ServiceOrder] = None  
    # ========================================================================
