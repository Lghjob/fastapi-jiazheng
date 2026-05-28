import asyncio
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
from starlette.middleware.base import BaseHTTPMiddleware

# ===================== 依赖导入 =====================
from service.user_service import UserService
from utils.result import Result
from config.database import get_db

LOGGER = logging.getLogger("JwtInterceptor")

# ===================== 官方标准白名单 =====================
WHITE_LIST = [
    # 用户登录注册
    "/api/user/login",
    "/api/user/forget",
    "/api/user/register",
    "/api/user/add",

    # 角色
    "/api/role/all",

    # 首页公开接口
    "/api/category/tree",              # 分类树
    "/api/service/list",              # 服务列表
    "/api/service/category/**",       # 按分类查服务（支持任意ID）
    "/api/staff/**",                  # 家政人员所有接口（列表、详情、评分）
    "/api/search/**",                 # 全局搜索所有接口
    "/api/review/staff/**", 
    "/api/recommend/**",
    "/api/service/**",
    
    # 图片 & 轮播图
    "/api/img/**",
    "/api/banner/active",
    "/api/file/upload/img",
    # 系统
    "/api/favicon.ico",
    "/docs",
    "/redoc",
    "/openapi.json"
]

class JwtInterceptorMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # -------------------- 1. 白名单放行 --------------------
        for white_path in WHITE_LIST:
            if white_path.endswith("/**") and path.startswith(white_path[:-3]):
                return await call_next(request)
            elif path == white_path:
                return await call_next(request)

        # -------------------- 2. 获取Token --------------------
        token = None

        # 1. 先尝试从 Authorization 头里取（支持 Swagger UI 的 Authorize 按钮）
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  

        # 2. 如果没有，再从 token 头里取
        if not token:
            token = request.headers.get("token")

        # 3. 如果还没有，从 URL 参数里取
        if not token:
            token = request.query_params.get("token")

        # -------------------- 3. Token缺失校验 --------------------
        if not token:
            return JSONResponse(status_code=401, content=Result.error_msg("Token缺失").model_dump())

        user = None
        db = None
        try:
            # -------------------- 4. 解码Token获取userId --------------------
            payload = jwt.get_unverified_claims(token)
            user_id_str = payload.get("aud")
            if isinstance(user_id_str, list):
                user_id_str = user_id_str[0]

            # ===================== 空值判断 =====================
            if not user_id_str or user_id_str.strip() == "":
                raise ValueError("userId不能为空")

            # 安全转 int
            user_id = int(user_id_str)

            # -------------------- 5. 数据库查询用户（核心业务逻辑，完整保留） --------------------
            db_gen = get_db()
            db = next(db_gen)
            user_service = UserService(db=db)
            user = await asyncio.to_thread(user_service.get_user_by_id, id=user_id)

        except Exception as e:
            err_msg = "token失效，请重新登录！"
            LOGGER.error(f"{err_msg} ,token={token}", exc_info=True)
            return JSONResponse(status_code=401, content=Result.error_msg(err_msg).model_dump())
        finally:
            # 关闭数据库连接，防止泄漏
            if db:
                try:
                    db.close()
                except:
                    pass

        # -------------------- 6. 用户不存在校验 --------------------
        if not user:
            return JSONResponse(status_code=401, content=Result.error_msg("用户不存在").model_dump())

        # -------------------- 7. Token签名验证（核心逻辑，完整保留） --------------------
        try:
            jwt.decode(
                token,
                key=str(user.password),
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
        except JWTError:
            err_msg = "token认证失败，请重新登录！"
            LOGGER.error(f"{err_msg} ,token={token}", exc_info=True)
            return JSONResponse(status_code=401, content=Result.error_msg(err_msg).model_dump())

        # -------------------- 8. 验证通过放行 --------------------
        LOGGER.info(f"验证成功，允许放行。{user}")
        return await call_next(request)