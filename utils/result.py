# 导入Pydantic的BaseModel，用于数据校验和序列化
from pydantic import BaseModel
# 导入泛型相关工具，用于支持任意数据类型的响应
from typing import Generic, TypeVar, Optional, Any
# 直接导入项目统一的响应状态码枚举，避免重复定义
from utils.result_code import ResultCode

# 定义泛型类型T，表示响应数据可以是任意类型
T = TypeVar("T")

# ===================== 下划线转驼峰核心工具（适配ORM模型）=====================
def snake_to_camel(s: str) -> str:
    """
    单个字符串工具：下划线命名 转 驼峰命名（小驼峰）
    例如：user_name → userName，create_time → createTime
    如果字符串本身没有下划线（已是驼峰），则直接返回不修改
    """
    # 无下划线直接返回
    if '_' not in s:
        return s
    # 按下划线分割字符串
    components = s.split('_')
    # 第一个单词小写，后续单词首字母大写，拼接成驼峰
    return components[0] + ''.join(x.title() for x in components[1:])

def orm_to_dict(obj: Any) -> Any:
    """
    ORM对象转换工具：将SQLAlchemy ORM模型/普通自定义对象 转换为 原生Python字典
    用于后续处理字段名，适配接口返回格式
    """
    # 处理SQLAlchemy ORM模型（过滤掉ORM内部私有属性）
    if hasattr(obj, '__dict__') and hasattr(obj, '_sa_instance_state'):
        return {
            k: v for k, v in obj.__dict__.items()
            if not k.startswith('_sa_')  # 排除SQLAlchemy内部状态属性
        }
    # 处理普通自定义对象（非字典、非ORM的普通类实例）
    elif hasattr(obj, '__dict__') and not isinstance(obj, dict):
        return obj.__dict__
    # 原生字典/其他基础类型，直接返回
    return obj

def convert_dict_keys_to_camel(data: Any) -> Any:
    """
    递归转换工具：
    1. 先将ORM/自定义对象转为字典
    2. 递归将字典所有key（下划线）转为驼峰命名
    3. 支持嵌套字典、列表等复杂数据结构
    作用：后端数据库字段下划线命名 → 前端接口字段驼峰命名
    """
    # 第一步：统一将ORM/对象转换为原生字典
    data = orm_to_dict(data)

    # 第二步：处理字典，递归转换key为驼峰
    if isinstance(data, dict):
        return {
            snake_to_camel(k): convert_dict_keys_to_camel(v)
            for k, v in data.items()
        }
    # 第三步：处理列表，遍历每个元素递归转换
    elif isinstance(data, list):
        return [convert_dict_keys_to_camel(item) for item in data]
    # 字符串、数字、时间等基础类型，直接返回
    else:
        return data
# =========================================================================

# ==============================
# 项目统一响应结果模型
# 所有接口统一返回该格式：code(状态码) + msg(提示信息) + data(业务数据)
# 基于Pydantic，自动序列化JSON，支持泛型数据
# ==============================
class Result(BaseModel, Generic[T]):
    # 响应状态码（字符串类型，来自ResultCode枚举）
    code: str
    # 响应提示信息（成功/失败描述）
    msg: str
    # 响应业务数据（泛型，支持任意类型，默认为None）
    data: Optional[T] = None

    # ==================== 成功响应静态方法 ====================
    @staticmethod
    def success():
        """无参数的成功响应：仅返回成功状态码和成功信息"""
        return Result(code=ResultCode.SUCCESS.code, msg=ResultCode.SUCCESS.msg)

    @staticmethod
    def success_data(data: T):
        """
        最常用的成功响应：返回成功状态+业务数据
        数据会自动将下划线字段转为驼峰命名
        """
        camel_data = convert_dict_keys_to_camel(data)
        return Result(code=ResultCode.SUCCESS.code, msg=ResultCode.SUCCESS.msg, data=camel_data)

    @staticmethod
    def success_msg(msg: str, data: T = None):
        """自定义提示信息的成功响应，可携带业务数据"""
        camel_data = convert_dict_keys_to_camel(data)
        return Result(code=ResultCode.SUCCESS.code, msg=msg, data=camel_data)

    # ==================== 失败响应静态方法 ====================
    @staticmethod
    def error():
        """默认失败响应：返回通用失败状态码和信息"""
        return Result(code=ResultCode.ERROR.code, msg=ResultCode.ERROR.msg)

    @staticmethod
    def error_msg(msg: str):
        """自定义提示信息的失败响应"""
        return Result(code=ResultCode.ERROR.code, msg=msg)

    @staticmethod
    def error_code(code: str, msg: str):
        """
        自定义状态码+消息的失败响应
        主要用于：全局异常处理、自定义业务异常返回
        """
        return Result(code=code, msg=msg)