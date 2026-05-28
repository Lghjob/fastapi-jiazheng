import json
import logging
from typing import List, Type, TypeVar, Any
# 只有当你手动处理 JSON 字符串（比如从别的系统接数据、读文件、读 Redis）时，才使用你的 JsonUtils
LOGGER = logging.getLogger("JsonUtils")

T = TypeVar("T")

class JsonUtils:
    """
    JSON 工具类
    功能：对象/JSON互转、数组解析、复杂类型解析
    """

    @staticmethod
    def to_json(obj: Any) -> str:
        """
        将对象转换为JSON字符串
        """
        try:
            # 兼容 Pydantic 模型/普通字典/列表
            if hasattr(obj, "model_dump"):
                obj = obj.model_dump()
            return json.dumps(obj, ensure_ascii=False, default=str)
        except Exception as e:
            LOGGER.error("转换JSON失败", exc_info=e)
            raise RuntimeError("转换JSON失败") from e

    @staticmethod
    def parse_object(json_str: str, clazz: Type[T]) -> T:
        """
        将JSON字符串转换为指定对象
        """
        try:
            data = json.loads(json_str)
            if hasattr(clazz, "model_validate"):
                # type: ignore[attr-defined] → 强制忽略Pylance检查，彻底消除红波浪
                return clazz.model_validate(data)  # type: ignore[attr-defined]
            return data
        except Exception as e:
            LOGGER.error("解析JSON失败", exc_info=e)
            raise RuntimeError("解析JSON失败") from e

    @staticmethod
    def parse_array(json_str: str, clazz: Type[T]) -> List[T]:
        """
        将JSON字符串转换为对象列表
        """
        try:
            data_list = json.loads(json_str)
            result = []
            for item in data_list:
                if hasattr(clazz, "model_validate"):
                    # type: ignore[attr-defined] → 强制忽略检查
                    result.append(clazz.model_validate(item))  # type: ignore[attr-defined]
                else:
                    result.append(item)
            return result
        except Exception as e:
            LOGGER.error("解析JSON数组失败", exc_info=e)
            raise RuntimeError("解析JSON数组失败") from e

    @staticmethod
    def parse_complex(json_str: str) -> Any:
        """
        解析复杂JSON类型
        """
        try:
            return json.loads(json_str)
        except Exception as e:
            LOGGER.error("解析复杂JSON失败", exc_info=e)
            raise RuntimeError("解析复杂JSON失败") from e