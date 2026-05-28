from enum import Enum

class AccountStatus(Enum):
    """
    账号状态枚举
    ENABLE = 1 启用
    DISABLE = 0 禁用
    """
    ENABLE = 1    # 启用
    DISABLE = 0   # 禁用

    def get_value(self):
        return self.value