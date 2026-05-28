from pydantic import BaseModel, ConfigDict, field_validator
from typing import Any, Optional
from datetime import datetime, date
import re
import json

class BaseSchema(BaseModel):
    """
    全局 Schema 基类
    所有的 Schema/DTO 都继承这个类
    """
    # ==================== 【合并后的】全局统一配置 ====================
    model_config = ConfigDict(
        # 1. 自动转驼峰
        alias_generator=lambda s: ''.join(
            word.capitalize() if i else word 
            for i, word in enumerate(s.split('_'))
        ),
        
        # 2. 基础配置
        populate_by_name=True,      # 允许通过原名(下划线)或别名(驼峰)赋值
        from_attributes=True,       # 兼容 ORM 模型
        extra='ignore',             # 忽略未知字段
        
        # 3. 时间序列化格式
        json_encoders={
            datetime: lambda dt: dt.strftime("%Y-%m-%d %H:%M:%S"),
            date: lambda d: d.strftime("%Y-%m-%d"),
        }
    )

    # ==================== 全局时间反序列化====================
    @field_validator('*', mode='before')
    @classmethod
    def parse_datetime(cls, v: Any) -> Any:
        if isinstance(v, str):
            patterns = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M",
                "%Y/%m/%d %H:%M:%S",
                "%Y/%m/%d %H:%M",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S.%f%z",
                "%Y-%m-%d",
            ]
            for pattern in patterns:
                try:
                    return datetime.strptime(v.strip(), pattern)
                except ValueError:
                    continue
            try:
                return datetime.fromisoformat(v.strip())
            except ValueError:
                pass
        return v

    # ==================== JSON字符串解析工具 ====================
    @staticmethod
    def string_to_json_array(value: Optional[str]) -> Any:
        if value is None or value.strip() == "":
            return None
        try:
            return json.loads(value)
        except:
            return value
