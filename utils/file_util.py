import os
import time
import logging
from pathlib import Path
from fastapi import UploadFile

LOGGER = logging.getLogger("FileUtil")

# ===================== 统一使用项目根目录 =====================
# 获取当前文件（file_util.py）所在的目录 → 自动定位项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent  # 定位到 fastapi 上级目录
FILE_BASE_PATH = BASE_DIR / "files"  # 统一指向根目录的 files

# 自动创建目录
os.makedirs(FILE_BASE_PATH, exist_ok=True)


class FileUtil:
    """
    文件工具类
    """

    @staticmethod
    def save_file(file: UploadFile, folder_name: str | None, base_dir: str) -> str | None:
        """
        公共文件保存方法
        :param file: FastAPI 上传文件
        :param folder_name: 子文件夹名称
        :param base_dir: 基础目录（img/videos等）
        :return: 前端可访问的相对路径
        """
        try:
            original_filename = file.filename
            if not original_filename:
                original_filename = "unknown_file"

            # 毫秒时间戳
            timestamp = str(int(time.time() * 1000))
            extension = os.path.splitext(original_filename)[-1] if "." in original_filename else ""

            # 新文件名
            new_filename = f"{timestamp}{extension}"

            # 拼接路径
            target_dir = FILE_BASE_PATH / base_dir
            if folder_name:
                target_dir = target_dir / folder_name

            target_dir.mkdir(parents=True, exist_ok=True)
            save_path = target_dir / new_filename

            # 写入文件
            with open(save_path, "wb") as f:
                f.write(file.file.read())

            LOGGER.info(f"文件已保存: {save_path.absolute()}")

            # 返回前端访问路径
            relative_path = f"/{base_dir}/"
            if folder_name:
                relative_path += f"{folder_name}/"
            relative_path += new_filename

            return relative_path

        except Exception as e:
            LOGGER.error(f"文件保存失败", exc_info=e)
            return None

    @staticmethod
    def save_image(file: UploadFile, folder_name: str | None) -> str | None:
        return FileUtil.save_file(file, folder_name, "img")

    @staticmethod
    def save_video(file: UploadFile, folder_name: str | None) -> str | None:
        return FileUtil.save_file(file, folder_name, "videos")

    @staticmethod
    def delete_file(filename: str) -> bool:
        try:
            file_path = FILE_BASE_PATH / filename.lstrip("/")
            if file_path.exists():
                os.remove(file_path)
                LOGGER.info(f"文件已删除: {file_path}")
                return True
            else:
                LOGGER.warning(f"文件不存在: {file_path}")
                return False
        except Exception as e:
            LOGGER.error(f"删除文件失败: {filename}", exc_info=e)
            return False

    @staticmethod
    def write_to_file(file_name: str, content: str):
        try:
            file_path = Path(file_name)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(file_name, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            LOGGER.error(f"写入文件失败", exc_info=e)
            raise e