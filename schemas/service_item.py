from datetime import datetime
from pydantic import BaseModel, Field,field_validator
from typing import Optional
from schemas.service_category import ServiceCategory
from schemas.base import BaseSchema
# 服务项目
class ServiceItem(BaseSchema):
    """
    服务项目
    作用：存储具体的服务项目信息（标题、价格、分类等）
    """
    # 服务ID
    id: Optional[int] = None

    # 类别ID 非空
    category_id: int = Field(
        ...,
        description="类别ID"
    )

    # 服务标题 非空 + 最大长度100
    title: str = Field(
        ...,
        description="服务标题",
        min_length=1,
        max_length=100
    )

    # 服务描述
    description: Optional[str] = None

    # 服务价格 非空 + 不能小于0
    price: float = Field(
        ...,
        description="服务价格",
        ge=0.0
    )

    # 状态(0:下架,1:上架)
    status: Optional[int] = None

    # 创建时间
    create_time: Optional[datetime] = None

    # 更新时间
    update_time: Optional[datetime] = None

    # 是否删除(0:未删除,1:已删除)
    is_deleted: Optional[int] = None

    # ===================== 关联信息（非数据库字段） =====================
    # 关联的类别信息（已迁移 ServiceCategory，直接导入）
    category: Optional[ServiceCategory] = None

    @field_validator('id', mode='before')
    def empty_id_to_none(cls, value):
        # 如果前端传空字符串，自动变成 None
        if value == "":
            return None
        return value
    # ========================================================================
model_config = {"from_attributes": True}

