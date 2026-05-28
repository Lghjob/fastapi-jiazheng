from datetime import datetime
from pydantic import BaseModel, Field,field_validator
from typing import Optional, List
from schemas.base import BaseSchema
# 服务类别
class ServiceCategory( BaseSchema):
    """
    服务类别
    作用：存储服务分类信息，支持树形父子分类结构
    """
    # 类别ID
    id: Optional[int] = None

    # 类别名称 非空 + 最大长度50
    category_name: str = Field(
        ...,
        description="类别名称",
        min_length=1,
        max_length=50
    )

    # 父类别ID（用于树形结构）
    parent_id: Optional[int] = None

    # 描述 最大长度500
    description: Optional[str] = Field(
        None,
        description="描述",
        max_length=500
    )

    # 图标URL
    icon: Optional[str] = None

    # 排序号
    sort_num: Optional[int] = None

    # 状态(0:禁用,1:正常)
    status: Optional[int] = None

    # 创建时间
    create_time: Optional[datetime] = None

    # 更新时间
    update_time: Optional[datetime] = None

    # 是否删除(0:未删除,1:已删除)
    is_deleted: Optional[int] = None
    @field_validator('id', mode='before')
    def empty_id_to_none(cls, value):
        # 如果前端传空字符串，自动变成 None
        if value == "":
            return None
        return value
    # ===================== 树形结构字段（非数据库字段） =====================
    # 子类别列表（自引用）
    children: Optional[List["ServiceCategory"]] = None

    # 是否有子类别
    has_children: Optional[int] = None
    # ========================================================================

    model_config = {"arbitrary_types_allowed": True}