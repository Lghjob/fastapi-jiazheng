# 自定义JSON转换工具
# 作用：将数据库存储的JSON字符串，自动转为数组返回给前端
import json
from typing import Any

def string_to_json_array(value: str | None) -> Any:
    """
    转换逻辑：
    1. 空值 → 返回None
    2. JSON格式字符串 → 转为数组/对象
    3. 解析失败 → 返回原始字符串
    """
    if not value or not value.strip():
        return None
    
    try:
        # 尝试将字符串转为JSON对象/数组
        return json.loads(value)
    except (json.JSONDecodeError, Exception):
        # 解析失败，返回原始字符串
        return value