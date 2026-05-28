from datetime import datetime
from pydantic import BaseModel
from typing import Optional
from schemas.base import BaseSchema 

class RoleMenu(BaseSchema):
    """
    角色-菜单关联中间表
    """
    # 角色ID
    role_id: Optional[int] = None

    # 菜单ID
    menu_id: Optional[int] = None

    # 创建时间
    created_time: Optional[datetime] = None