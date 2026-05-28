from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Any
from schemas.base import BaseSchema
# 服务浏览记录
class ServiceBrowseHistory(BaseSchema):
    """
    服务浏览记录
    """
    # 记录ID
    id: Optional[int] = None

    # 用户ID 非空
    user_id: int = Field(
        ...,
        description="用户ID"
    )

    # 服务项目ID 非空
    service_id: int = Field(
        ...,
        description="服务项目ID"
    )

    # 最后浏览时间
    last_browse_time: Optional[datetime] = None

    # ===================== 关联信息（非数据库字段）占位 =====================
    user: Optional[Any] = None 
    service_item: Optional[Any] = None  
    # ========================================================================