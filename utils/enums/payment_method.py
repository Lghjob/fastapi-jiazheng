from enum import Enum
from typing import Optional

class PaymentMethod(Enum):
    """
    支付方式枚举
    """
    WECHAT = ("WECHAT", "微信支付")
    ALIPAY = ("ALIPAY", "支付宝")
    BALANCE = ("BALANCE", "余额支付")

    # 初始化枚举值：code + 描述
    def __init__(self, code: str, desc: str):
        self.code = code
        self.desc = desc

    def get_code(self) -> str:
        return self.code

    def get_desc(self) -> str:
        return self.desc

    # 根据code获取枚举
    @classmethod
    def get_by_code(cls, code: str) -> Optional["PaymentMethod"]:
        for item in cls:
            if item.get_code() == code:
                return item
        return None