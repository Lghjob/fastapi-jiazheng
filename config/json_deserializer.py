# 自定义JSON转换工具
# 作用：将前端传入的数组自动转换为字符串
import json
from typing import Any

# 反序列化器
def json_array_to_string(value: Any) -> str | None:
    """
    转换逻辑：
    1. 数组 → 转为JSON字符串
    2. 字符串 → 直接返回
    3. 其他类型 → 返回None
    """
    # 如果是列表(数组)，转换为JSON字符串
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False)
    # 如果是字符串，直接返回
    if isinstance(value, str):
        return value
    # 其他情况返回None
    return None

#在迁移 schemas/ 文件夹时，记得把这个函数挂载到对应的字段验证器上即可。