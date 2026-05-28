from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Any
from schemas.base import BaseSchema
# 服务收藏
class ServiceFavorite(BaseSchema):
    """
    服务收藏
    作用：记录用户收藏的服务项目
    """
    # 收藏ID
    id: Optional[int] = None

    # 用户ID 非空
    user_id: int = Field(...,
        description="用户ID",
        alias="userId"
        )
    # 服务ID 非空
    service_id: int = Field(
        ...,
        description="服务ID",
        alias="serviceId"
        )

    # 创建时间
    create_time: Optional[datetime] = None

    # ===================== 关联信息（非数据库字段）占位 =====================
    # 迁移完 User 和 ServiceItem  后，把下面的 Any 替换成对应类名
    user: Optional[Any] = None  # 对应  User
    service_item: Optional[Any] = None  # 对应 ServiceItem
    # ========================================================================