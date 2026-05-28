from datetime import datetime
from typing import Optional

from schemas.service_item import ServiceItem
from schemas.base import BaseSchema
# 服务人员
class StaffServiceItem(BaseSchema):
    """
    服务人员-服务项目关联中间表
    作用：记录服务人员可以提供的服务项目
    """
    # 主键ID
    id: Optional[int] = None

    # 服务人员ID
    staff_id: Optional[int] = None

    # 服务项目ID
    service_id: Optional[int] = None

    # 状态
    status: Optional[int] = None

    # 创建时间
    create_time: Optional[datetime] = None

    # 更新时间
    update_time: Optional[datetime] = None

    # ===================== 关联信息（非数据库字段） =====================
    # 关联的服务项目信息
    service_item: Optional[ServiceItem] = None
    # ========================================================================
        