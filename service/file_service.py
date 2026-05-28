import logging
import os
from typing import List, Optional
from fastapi import UploadFile

# 导入你项目已有的文件（直接用你写的，不用改）
from utils.result import Result
from utils.enums.file_type import FileType
from utils.file_util import FileUtil

# 日志配置
logger = logging.getLogger(__name__)

class FileService:
    def __init__(self):
        pass

    # 单文件上传
    def upload(self, file: UploadFile, file_type: FileType) -> Result:
        if not file.filename:
            logger.error("文件不存在")
            return Result.error_code("-1", "文件不存在！")

        logger.info(f"upload FILE: {file.filename}")
        # 调用你现有的 FileUtil.save_file
        path = FileUtil.save_file(file, None, file_type.get_type_name())

        if path:
            return Result.success_data(path)
        else:
            return Result.error_code("-1", "文件上传失败")

    # 文件删除
    def file_remove(self, filename: str) -> Result:
  
        file_path = f"\\img\\{filename}"
        res = FileUtil.delete_file(file_path)
        return Result.success() if res else Result.error_code("-1", "删除失败！")

    # 批量文件上传
    def upload_multiple(self, files: List[UploadFile]) -> Optional[List[str]]:
        if not files:
            logger.error("没有文件上传")
            return None

        success_paths = []
        failed_files = []

        for file in files:
            try:
                if not file.filename:
                    failed_files.append(f"{file.filename}: 文件不存在")
                    continue

                logger.info(f"upload FILE: {file.filename}")
                # 批量上传使用通用文件类型
                path = FileUtil.save_file(file, None, FileType.COMMON.get_type_name())

                if path:
                    success_paths.append(path)
                else:
                    failed_files.append(f"{file.filename}: 文件上传失败")
            except Exception as e:
                logger.error(f"文件上传时发生异常: {str(e)}")
                failed_files.append(f"{file.filename}: 文件上传时发生异常")

        # 有失败 → 回滚删除所有已上传文件
        if failed_files:
            for path in success_paths:
                try:
                    if os.path.exists(os.path.join(FileUtil.FILE_BASE_PATH, path.lstrip("/"))):
                        os.remove(os.path.join(FileUtil.FILE_BASE_PATH, path.lstrip("/")))
                        logger.info(f"Deleted successfully uploaded file: {path}")
                except Exception as e:
                    logger.warning(f"Failed to delete file: {path}")
            return None
        else:
            return success_paths