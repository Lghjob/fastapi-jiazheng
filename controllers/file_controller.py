from fastapi import APIRouter, UploadFile, File, Depends
from typing import List
from utils.result import Result
# 从你的项目导入依赖
from config.database import  get_db
from utils.enums.file_type import FileType
from service.file_service import FileService

# 路由配置
router = APIRouter(prefix="/file", tags=["文件上传接口类"])

# ===================== 单文件上传 =====================
@router.post("/upload/img", summary="文件上传")
async def upload_img(
    file: UploadFile = File(...),
    db = Depends(get_db)
):
    service = FileService()
    return service.upload(file, FileType.IMG)

# ===================== 多文件上传 =====================
@router.post("/uploadMultiple", summary="多文件上传，失败时删除已上传文件")
async def upload_multiple(
    files: List[UploadFile] = File(...),
    db = Depends(get_db)
):
    service = FileService(db)
    result = service.upload_multiple(files)
    if result:
        return Result.success_data(result)
    return Result.error_code("-1", "文件上传失败！")