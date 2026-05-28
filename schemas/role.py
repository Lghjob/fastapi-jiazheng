from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from schemas.menu import Menu
from schemas.base import BaseSchema 

class Role(BaseSchema):
    id: Optional[Any] = None
    code: Optional[str] = Field(None, description="角色编码", max_length=50)
    name: Optional[str] = Field(None, description="角色名称", max_length=50)
    is_deleted: Optional[Any] = None
    description: Optional[str] = None
    created_time: Optional[Any] = None
    updated_time: Optional[Any] = None
    menu_list: Optional[Any] = None

    model_config = {"from_attributes": True}

    # ==========================================
   #所有字段统一处理空字符串
    # ==========================================
    @field_validator('*', mode='before')
    @classmethod
    def handle_all_empty_strings(cls, v, info):
        """
        无论前端传什么空字符串，全部处理成正确的格式
        """
        # 1. 如果是空字符串
        if v == "":
            # 对于 menu_list，返回 None
            if info.field_name == "menu_list":
                return None
            # 对于时间字段，返回 None
            if info.field_name in ["created_time", "updated_time"]:
                return None
            # 对于数字字段，返回 None
            if info.field_name in ["id", "is_deleted"]:
                return None
            # 对于字符串字段，返回空字符串
            return v
        
        # 2. 如果是字符串类型的数字，尝试转成 int
        if info.field_name in ["id", "is_deleted"] and isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        
        return v