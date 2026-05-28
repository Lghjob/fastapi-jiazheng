from pydantic import BaseModel as _BaseModel
from pydantic import ConfigDict

# 驼峰转换函数
def to_camel(s: str) -> str:
    parts = s.split('_')
    return parts[0] + ''.join(p.capitalize() for p in parts[1:])

# 全局生效的补丁（所有继承 BaseModel 的类自动支持驼峰）
class PatchedBaseModel(_BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

# 把系统的 BaseModel 替换成打了补丁的版本
import pydantic
pydantic.BaseModel = PatchedBaseModel
pydantic.main.BaseModel = PatchedBaseModel