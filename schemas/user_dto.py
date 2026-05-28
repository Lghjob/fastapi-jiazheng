from pydantic import BaseModel
from schemas.base import BaseSchema
from typing import Optional

class UserLoginDTO(BaseSchema):
    username: str
    password: str

class UserUpdate(BaseSchema):
    id: int
    username: Optional[str] | None = None
    email: Optional[str] | None = None
    phone: Optional[str] | None = None
    name: Optional[str] | None = None
    id_card: Optional[str] | None = None
    address: Optional[str] | None = None

    gender: Optional[int] | None = None   # 改为 int
    age: Optional[int] | None = None      # 改为 int
    status: Optional[int] | None = None   # 改为 int

    role_code: Optional[str] | None = None
    avatar: Optional[str] | None = None


from pydantic import Field
from schemas.base import BaseSchema

class UserPasswordUpdateDTO(BaseSchema):
    """
    密码修改DTO
    """
    # 原密码
    old_password: str = Field(
        ..., 
        description="原密码",
        min_length=1,
        alias="oldPassword"  # 加驼峰别名
    )

    # 新密码
    new_password: str = Field(
        ..., 
        description="新密码",
        min_length=6, 
        max_length=20,
        alias="newPassword"  # 加驼峰别名
    )

    # 确认密码
    confirm_password: str = Field(
        ..., 
        description="确认密码",
        min_length=1,
        alias="confirmPassword"  # 加驼峰别名
    )