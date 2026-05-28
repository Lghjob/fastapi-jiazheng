from datetime import datetime
from pydantic import Field, EmailStr, field_validator
from typing import Optional, Any
from schemas.base import BaseSchema

class User(BaseSchema):
    """
    用户
    """
    # 用户ID
    id: Optional[int] = None

    # 用户名（列表查询用 Optional）
    username: Optional[str] = Field(None, min_length=3, max_length=50)

    # 密码（直接排除，不返回给前端）
    password: Optional[str] = Field(None, exclude=True, min_length=6, max_length=100)

    # 邮箱
    email: Optional[EmailStr] = None

    # 手机号
    phone: Optional[str] = Field(None, pattern=r"^$|^1[3-9]\d{9}$", description="手机号")

    # 角色编码（字段名下划线，alias 驼峰）
    role_code: Optional[str] = Field(None, alias="roleCode")
    
    # 姓名
    name: Optional[str] = Field(None, max_length=50)

    # 身份证号（字段名下划线，alias 驼峰）
    id_card: Optional[Any] = Field(None, alias="idCard")
    
    # 地址
    address: Optional[str] = Field(None, max_length=200)

    # 头像URL
    avatar: Optional[str] = None  # None 转空字符串

    # 性别
    gender: Optional[int] = None

    # 年龄
    age: Optional[int] = Field(None, ge=0, le=150)

    # 状态
    status: Optional[int] = None

    # 创建时间（字段名下划线，alias 驼峰）
    create_time: Optional[datetime] = Field(None, alias="createTime")

    # 更新时间（字段名下划线，alias 驼峰）
    update_time: Optional[datetime] = Field(None, alias="updateTime")

    # ===================== 非数据库字段 =====================
    # token信息
    token: Optional[str] = ""

    # 菜单信息
    menu_list: Optional[Any] = None

    # ==========================================
    # 全局兼容空字符串，不报错
    # ==========================================
    @field_validator('*', mode='before')
    def empty_to_none(cls, v, info):
        # 空字符串 → 转 None
        if v == "":
            return None
        return v

    # 身份证强制转字符串，避免类型错误
    @field_validator("id_card", mode="before")
    def force_str_id_card(cls, v):
        if v is None or v == "":
            return None
        return str(v)

    # 手机号兼容空字符串
    @field_validator("phone", mode="before")
    def empty_phone(cls, v):
        if v == "":
            return None
        return v