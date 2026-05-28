from datetime import datetime
from pydantic import Field, field_validator
from typing import Optional, List, Any, Union
import json

from schemas.base import BaseSchema


class ServiceStaff(BaseSchema):
    """
    服务人员
    """
    # 服务人员ID
    id: Optional[int] | None = None

    # 关联用户ID (必填)
    user_id: int = Field(
        ...,
        description="关联用户ID",
        alias="userId"
    )

    # 服务类型 (JSON 字符串)
    service_type: Optional[List[str]] | None = Field(
        None,
        description="服务类型",
        alias="serviceType"
    )

    # 工作经验年限 (不能小于0)
    experience: Optional[int] | None = Field(
        None,
        description="工作经验年限",
        ge=0
    )

    # 综合评分 (0-5)
    rating: Optional[float] | None = Field(
        None,
        description="综合评分",
        ge=0.0,
        le=5.0
    )

    # 个人描述
    description: Optional[str] | None = None

    #  改成支持任意JSON格式：对象 / 数组 / 空
    certificates: Optional[Union[dict, list, Any]] | None = Field(
        None,
        description="证书信息(JSON格式)"
    )

    # 服务区域
    work_area: Optional[str] | None = Field(
        None,
        description="服务区域",
        alias="workArea"
    )

    # 总订单数
    total_orders: Optional[int] | None = Field(
        None,
        description="总订单数",
        alias="totalOrders"
    )

    # 完成率 (0-100)
    completion_rate: Optional[float] | None = Field(
        None,
        description="完成率",
        ge=0.0,
        le=100.0,
        alias="completionRate"
    )

    # 创建时间
    create_time: Optional[datetime] | None = Field(
        None,
        description="创建时间",
        alias="createTime"
    )

    # 更新时间
    update_time: Optional[datetime] | None = Field(
        None,
        description="更新时间",
        alias="updateTime"
    )

    # 是否删除(0:未删除,1:已删除)
    is_deleted: Optional[int] | None = Field(
        None,
        description="是否删除(0:未删除,1:已删除)",
        alias="isDeleted"
    )

    # ===================== 关联信息（非数据库字段） =====================
    user: Optional[Any] | None = None
    orders: Optional[List[Any]] | None = None
    reviews: Optional[List[Any]] | None = None
    categories: Optional[List[Any]] | None = None
    service_items: Optional[List[Any]] | None = Field(None, alias="serviceItems")
    # ========================================================================================

    # ===================== 自动解析 JSON =====================
    @field_validator('service_type', mode='before')
    @classmethod
    def parse_service_type(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return []
        return v
#支持 字符串/对象/数组
    @field_validator('certificates', mode='before')
    @classmethod
    def parse_certificates(cls, v):
        if v is None or v == "":
            return None

        # 字符串 → 自动转成 JSON
        if isinstance(v, str):
            try:
                return json.loads(v)
            except:
                return None

        # 已经是 对象 / 数组 → 直接返回
        return v

    model_config = {
        "from_attributes": True,
        "populate_by_name": True
    }
