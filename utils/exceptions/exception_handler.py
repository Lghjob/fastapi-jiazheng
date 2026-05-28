"""
全局异常处理器
"""
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

# 导入项目内部模块
from utils.result import Result
from utils.result_code import ResultCode
from utils.exceptions.service_exception import ServiceException

# 日志配置
logger = logging.getLogger(__name__)

# ======================
# 1. 处理自定义业务异常 ServiceException
# ======================
def service_exception_handler(request: Request, exc: ServiceException):
    logger.error(f"业务异常: {exc.getMessage()}", exc_info=True)
    return JSONResponse(
        status_code=200,
        content=Result.error_code(code=exc.getCode(), msg=exc.getMessage()).model_dump()
    )

# ======================
# 2. 处理参数校验异常 RequestValidationError
# ======================
def validation_exception_handler(request: Request, exc: RequestValidationError):
    # 取第一个错误的提示信息返回给前端
    errors = exc.errors()
    msg = errors[0]["msg"] if errors else "参数校验失败"
    logger.error(f"参数校验异常: {msg}")
    
    return JSONResponse(
        status_code=200,
        content=Result.error_code(
            code=ResultCode.VALIDATE_FAILED.code,
            msg=msg
        ).model_dump()
    )

# ======================
# 3. 处理所有其他系统异常 Exception
# ======================
def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"系统异常: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=200,
        content=Result.error_code(
            code=ResultCode.SYSTEM_ERROR.code,
            msg="系统内部错误"
        ).model_dump()
    )