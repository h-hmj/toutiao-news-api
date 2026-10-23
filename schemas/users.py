from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

"""
Pydantic 数据模型层(Schema 层),负责定义 API 的请求体校验格式和响应数据序列化格式,是连接"前端 JSON 数据"与"数据库 ORM 模型"之间的桥梁。
"""

# 定义前端注册时发过来的请求体格式
class UserRequest(BaseModel):
    username: str
    password: str


# 定义用户信息基础数据模型,单独放一个基类,目的是被继承复用,避免重复写。
class UserInfoBase(BaseModel):
    nickname: Optional[str] = Field(None, max_length=50, description="昵称")
    avatar: Optional[str] = Field(None, max_length=255, description="头像URL")
    gender: Optional[str] = Field(None, max_length=10, description="性别")
    bio: Optional[str] = Field(None, max_length=500, description="个人简介")

# 定义用户信息响应数据模型，继承自UserInfoBase，并添加id和username字段
class UserInfoResponse(UserInfoBase):
    id: int
    username: str
  # 模型类配置
    model_config = ConfigDict(
        from_attributes=True  # 允许从 ORM 对象属性中取值
    )


# 定义用户认证响应数据模型，包含token和用户信息
class UserAuthResponse(BaseModel):
    token: str
    #调用上面这个函数
    user_info: UserInfoResponse = Field(...,alias="userInfo")

    #模型类配置
    model_config = ConfigDict(
        populate_by_name=True,  #字段名兼容
        from_attributes=True    # 允许从ORM属性中获取字段值
        )

#更新用户信息的模型类
class UserUpdateRequest(BaseModel):
    nickname: str =None
    avatar: str =None
    gender: str =None
    bio: str =None
    phone: str =None

#修改用户密码的模型类
class UserChangePasswordRequest(BaseModel):
    old_password: str=Field(..., alias="oldPassword", description="旧密码")
    new_password: str=Field(..., min_length=6, alias="newPassword", description="新密码")

