from datetime import datetime
from pydantic import Field,field_validator
from typing import Optional
from schemas.base import BaseSchema 
# 轮播图
class Banner(BaseSchema):
    """
    轮播图
    """
    # 主键ID
    id: Optional[int] = None

    # 轮播图标题 非空 + 最大长度100
    title: str = Field(
        ...,
        description="轮播图标题",
        min_length=1,
        max_length=100,
        json_schema_extra={"errorMessage": "轮播图标题不能为空/长度不能超过100个字符"}
    )

    # 图片URL 非空
    image_url: str = Field(
        ...,
        alias="imageUrl",
        description="图片URL",
        min_length=1,
        json_schema_extra={"errorMessage": "图片URL不能为空"}
    )

    # 描述 最大长度255
    description: Optional[str] = Field(
        None,
        description="图片描述",
        max_length=255
    )

    # 标签 最大长度50
    tag: Optional[str] = Field(
        None,
        description="标签",
        max_length=50
    )

    # 状态(0:禁用,1:启用)
    status: Optional[int] = Field(None, description="状态(0:禁用,1:启用)")

    # 创建时间
    create_time: Optional[datetime] = None

    # 更新时间
    update_time: Optional[datetime] = None
       
    @field_validator('id', mode='before')
    def empty_id_to_none(cls, value):
        # 如果前端传空字符串，自动变成 None
        if value == "":
            return None
        return value