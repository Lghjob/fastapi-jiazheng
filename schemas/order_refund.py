from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, Any
from schemas.service_order import ServiceOrder
from schemas.user import User
from schemas.base import BaseSchema 
class OrderRefund(BaseSchema):
    """
    订单退款 类
    """
    # 主键ID
    id: Optional[int] = None

    # 订单ID
    order_id: Optional[int] = None

    # 用户ID
    user_id: Optional[int] = None

    # 退款金额
    refund_amount: Optional[float] = None

    # 退款原因
    refund_reason: Optional[str] = None

    # 退款状态
    # 1:待审核, 2:审核通过, 3:审核拒绝, 4:退款中, 5:已退款, 6:退款失败
    refund_status: Optional[int] = None

    # 退款类型
    # 1:用户取消, 2:服务人员取消, 3:超时未接单, 4:服务纠纷
    refund_type: Optional[int] = None

    # 审核人ID
    audit_user_id: Optional[int] = None

    # 审核时间
    audit_time: Optional[datetime] = None

    # 审核备注
    audit_remark: Optional[str] = None

    # 退款时间
    refund_time: Optional[datetime] = None

    # 创建时间
    create_time: Optional[datetime] = None

    # 更新时间
    update_time: Optional[datetime] = None

    # 逻辑删除标记
    is_deleted: Optional[int] = None

    # ===================== 关联信息（非数据库字段）占位 =====================
    # 等你迁移完 ServiceOrder 和 User  后，把下面的 Any 替换成对应类名
    order: Optional[ServiceOrder] = None
    user: Optional[User] = None
    audit_user: Optional[User] = None  
    # ========================================================================