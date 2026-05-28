import logging
from datetime import datetime, timedelta
from typing import Optional, Any
from jose import jwt
from fastapi import Request

# 获取日志记录器
logger = logging.getLogger(__name__)

class JwtTokenUtils:
    # 类静态变量：保存用户服务实例，全局共用一份
    static_user_service: Optional[Any] = None

    @classmethod
    def init_user_service(cls, user_service: Any):
        """
        类方法：项目启动时初始化用户服务
        只需要调用一次，全局生效
        """
        cls.static_user_service = user_service

    # ===================== 生成Token =====================
    @staticmethod
    def gen_token(user_id: str, sign: str) -> str:
        """
        静态方法：生成JWT登录令牌
        :param user_id: 用户ID
        :param sign: 加密密钥
        :return: 生成的token字符串
        """
        expire_time = datetime.utcnow() + timedelta(days=7)
        
        # JWT载荷：存放用户ID和过期时间
        payload = {
            "aud": user_id,    # aud 存放用户ID
            "exp": expire_time # exp 固定表示过期时间
        }
        
        # 加密生成token，使用HS256算法
        return jwt.encode(payload, sign, algorithm="HS256")

    # ===================== 获取当前登录用户 =====================
    @staticmethod
    def get_current_user(request: Request) -> Optional[Any]:
        """
        静态方法：从请求中解析token，获取当前登录用户信息
        :param request: FastAPI请求对象
        :return: 用户对象 或 None
        """
        token: Optional[str] = None
        try:
            # 1. 优先从请求头 Header 获取 token
            token = request.headers.get("token")
            # 2. 头部没有，再从 URL 参数中获取 token
            if not token:
                token = request.query_params.get("token")
            
            # 3. 两处都没拿到token，直接返回空
            if not token:
                logger.error(f"获取当前登录的token失败，token={token}")
                return None

            # 4. 不校验签名，直接解析token内容（仅提取数据）
            payload = jwt.get_unverified_claims(token)
            # 从载荷中取出用户ID
            user_id = payload.get("aud")
            
            # 5. 没有用户ID 或 用户服务未初始化，返回空
            if not user_id or not JwtTokenUtils.static_user_service:
                return None
            
            # 6. 根据用户ID查询并返回用户信息
            return JwtTokenUtils.static_user_service.get_user_by_id(int(user_id))

        except Exception as e:
            # 统一捕获所有异常，打印错误日志，返回空
            logger.error(f"获取当前用户信息失败，token={token}", exc_info=e)
            return None