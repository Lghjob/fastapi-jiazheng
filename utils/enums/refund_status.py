from enum import Enum
from typing import Optional

class RefundStatus(Enum):
    """
    退款状态枚举
    """
    PENDING_AUDIT = (1, "待审核")
    AUDIT_PASSED = (2, "审核通过")
    AUDIT_REJECTED = (3, "审核拒绝")
    REFUNDING = (4, "退款中")
    REFUNDED = (5, "已退款")
    REFUND_FAILED = (6, "退款失败")

    # 初始化枚举值：code + 描述（绝对不用 value！）
    def __init__(self, code: int, desc: str):
        self.code = code   # 禁用 value
        self.desc = desc

    def get_value(self) -> int:
        return self.code   # 这里同步改

    def get_desc(self) -> str:
        return self.desc

    @classmethod
    def get_by_value(cls, value: int) -> Optional["RefundStatus"]:
        for item in cls:
            if item.get_value() == value:
                return item
        return None