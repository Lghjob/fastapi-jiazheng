from enum import Enum
from typing import Optional

class OrderStatus(Enum):
    """
    订单状态枚举
    """
    WAITING_PAY = (1, "待支付")
    WAITING_ACCEPT = (2, "待接单")
    ACCEPTED = (3, "已接单")
    IN_SERVICE = (4, "服务中")
    COMPLETED = (5, "已完成")
    CANCELLED = (6, "已取消")
    CLOSED = (7, "已关闭")

    # 解析值和描述 → 把 value 改成 code，避开系统关键字！
    def __init__(self, code: int, desc: str):
        self.code = code   
        self.desc = desc

    def get_value(self) -> int:
        return self.code  

    def get_desc(self) -> str:
        return self.desc

    @classmethod
    def get_by_value(cls, value: int) -> Optional["OrderStatus"]:
        for item in cls:
            if item.get_value() == value:
                return item
        return None