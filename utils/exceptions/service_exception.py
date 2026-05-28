"""
自定义业务异常
继承 Exception
"""
class ServiceException(Exception):
    # 类属性声明（标准Python语法）
    code: str
    msg: str

    def __init__(self, msg: str, code: str = "-1"):
        super().__init__(msg)
        # 1. 只传 msg → code = "-1"
        # 2. 传 code + msg → 使用自定义code
        if code is None:
            self.code = "-1"
            self.msg = msg
        else:
            self.code = code
            self.msg = msg

    def getCode(self) -> str:
        return self.code

    def getMsg(self) -> str:
        return self.msg

    def getMessage(self) -> str:
        return self.msg