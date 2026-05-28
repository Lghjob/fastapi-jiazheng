from datetime import datetime
from pydantic import Field,field_validator
from typing import Optional, List
from schemas.base import BaseSchema

class Menu(BaseSchema):
    """
    菜单类 
    """
    # 菜单id
    id: Optional[int] = None

    # 菜单名
    name: Optional[str] = None

    # 菜单路径
    path: Optional[str] = None

    # 组件路径
    component: Optional[str] = None

    # 菜单图标
    icon: Optional[str] = None

    # 描述
    description: Optional[str] = None

    # 父级菜单id
    pid: Optional[int] = None

    # 排序（加 alias 转驼峰）
    sort_num: Optional[int] = Field(None, alias="sortNum")

    # 是否隐藏
    hidden: Optional[bool] = None

    # 创建时间（加 alias 转驼峰）
    created_time: Optional[datetime] = Field(None, alias="createdTime")

    # 更新时间（加 alias 转驼峰）
    updated_time: Optional[datetime] = Field(None, alias="updatedTime")

    # 子菜单（自引用）
    children: Optional[List["Menu"]] = None

    # 是否存在子节点
    has_children: Optional[int] = 0

    @field_validator('id', 'pid', mode='before')
    @classmethod
    def empty_str_to_none(cls, v):
        if v == "":
            return None
        return v

Menu.model_rebuild()