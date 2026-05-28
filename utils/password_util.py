from passlib.context import CryptContext
from passlib.exc import UnknownHashError

# 显式设置 rounds=10
pwd_context = CryptContext(schemes=["bcrypt"], bcrypt__rounds=10, deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证密码是否匹配，捕获密码格式异常，永不崩溃
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except UnknownHashError:
        # 密码格式错误 → 统一返回False，走业务层的"原密码错误"
        return False

def get_password_hash(password: str) -> str:
    """
    生成新的加密密码
    """
    return pwd_context.hash(password)
