from enum import Enum

class FileType(Enum):
    """
    文件类型枚举
    """
    # 文本文件
    TXT = "text"
    # PDF文件
    PDF = "pdf"
    # 图像文件
    IMG = "img"
    # 音频文件
    AUDIO = "audio"
    # 视频文件
    VIDEO = "video"
    # 通用文件
    COMMON = "common"

    def get_type_name(self):
        return self.value