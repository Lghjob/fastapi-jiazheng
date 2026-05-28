# common/result_code.py
"""
通用响应状态码枚举模块
定义接口统一返回的状态码、状态信息
"""
from enum import Enum

class ResultCode(Enum):
    """
    接口统一响应状态码枚举类
    每个枚举项包含：状态码(code) + 提示信息(msg)
    用于前后端交互时统一返回状态标识和描述
    """
    # 操作成功
    SUCCESS = ("200", "操作成功")
    # 通用操作失败
    ERROR = ("-1", "操作失败")
    # 参数校验失败（前端传参错误/格式不合法）
    VALIDATE_FAILED = ("404", "参数检验失败")
    # 未登录 / Token 过期 / 身份认证失败
    UNAUTHORIZED = ("401", "暂未登录或token已经过期")
    # 权限不足，禁止访问
    FORBIDDEN = ("403", "没有相关权限")
    # 服务器内部异常
    SYSTEM_ERROR = ("500", "系统错误")

    @property
    def code(self):
        """
        只读属性：获取当前状态码的 code 字符串
        :return: 状态码字符串，如 "200"
        """
        return self.value[0]

    @property
    def msg(self):
        """
        只读属性：获取当前状态码的提示信息
        :return: 提示信息字符串，如 "操作成功"
        """
        return self.value[1]