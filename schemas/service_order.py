from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Any
from schemas.service_item import ServiceItem
from schemas.base import BaseSchema
# 服务订单
class ServiceOrder(BaseSchema):
    """
    服务订单
    作用：存储服务订单的完整信息（用户、服务、金额、状态、时间等）
    """
    # 订单ID
    id: Optional[int] = None

    # 用户ID 非空
    user_id: int = Field(
        ...,
        description="用户ID"
    )

    # 服务人员ID 非空
    staff_id: int = Field(
        ...,
        description="服务人员ID"
    )

    # 服务项目ID 非空
    service_id: int = Field(
        ...,
        description="服务项目ID"
    )

    # 订单状态(1:待支付,2:待接单,3:已接单,4:服务中,5:已完成,6:已取消,7:已关闭)
    order_status: Optional[int] = None

    # 服务开始时间
    service_time: Optional[datetime] = None

    # 服务时长(小时)
    duration: Optional[float] = None

    # 订单金额 非空 + 不能小于0
    total_amount: float = Field(
        ...,
        description="订单金额",
        ge=0.0
    )

    # 支付方式(WECHAT:微信,ALIPAY:支付宝,BALANCE:余额)
    payment_method: Optional[str] = None

    # 支付时间
    payment_time: Optional[datetime] = None

    # 实付金额
    paid_amount: Optional[float] = None

    # 退款金额
    refund_amount: Optional[float] = None

    # 退款状态(0:无退款,1:退款中,2:已退款,3:退款失败)
    refund_status: Optional[int] = None

    # 取消原因 最大长度500
    cancel_reason: Optional[str] = Field(
        None,
        description="取消原因",
        max_length=500
    )

    # 取消时间
    cancel_time: Optional[datetime] = None

    # 完成时间
    complete_time: Optional[datetime] = None

    # 备注 最大长度500
    remark: Optional[str] = Field(
        None,
        description="备注",
        max_length=500
    )

    # 创建时间
    create_time: Optional[datetime] = None

    # 更新时间
    update_time: Optional[datetime] = None

    # 是否删除(0:未删除,1:已删除)
    is_deleted: Optional[int] = None

    # ===================== 关联信息（非数据库字段） =====================
    # 等你迁移完 后，把下面的 Any 替换成具体类名
    user: Optional[Any] = None  
    staff: Optional[Any] = None 
    service_item: Optional[ServiceItem] = None  # 已迁移 ServiceItem，直接使用
    review: Optional[Any] = None  
    # ========================================================================