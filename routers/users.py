from fastapi import APIRouter
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from config.db_conf import get_db
from schemas.users import UserRequest, UserAuthResponse, UserInfoResponse, UserUpdateRequest, UserChangePasswordRequest
from crud import users
from utils.response import success_response
from utils.auth import get_current_user
from models.users import User
#创建 APIRouter 实例
router = APIRouter(prefix="/user", tags=["users"])
#接口实现流程
#1.模块化路由——>API接口规范文档
#2.定义模型类——>数据库表

#注册接口
@router.post("/register")
async def register(user_data: UserRequest ,db: AsyncSession = Depends(get_db)):    #添加用户信息，数据库信息
    #注册逻辑：验证用户是否存在 ——>创建用户 ——>生成token ——>响应结果
    #验证用户是否存在
    existing_user = await users.get_user_by_username(db, user_data.username)
    if existing_user:
        # 统一走全局异常处理器：HTTP 状态码与 body code 保持一致（400），
        # 而不是"HTTP 200 里藏 code 400"
        raise HTTPException(status_code=400, detail="用户已存在，请修改用户名后重试")

    #用户不存在则创建用户
    user = await users.create_user(db, user_data)

    #生成token
    token = await users.create_token(db, user.id)

    #
    # return {
    #     "code": 200,
    #     "message": "登录成功",
    #     "data": {
    #         "token": token,
    #         "userInfo": {
    #             "id": user.id,
    #             "username": user.username,
    #             "bio": user.bio,
    #             "avatar": user.avatar
    #         }
    #     }
    # }
    #
    response_data = UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user))
    return success_response(message="注册成功",data=response_data)

#登录接口
@router.post("/login")
async def login(user_data: UserRequest, db: AsyncSession = Depends(get_db)):
    #登录逻辑：验证用户是否存在——>验证密码——>生成token——>响应结果
    #验证用户是否存在
    user = await users.authenticate_user(db, user_data.username, user_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    #生成token
    token = await users.create_token(db, user.id)

    response_data = UserAuthResponse(token=token, user_info=UserInfoResponse.model_validate(user))

    return success_response(message="登录成功", data=response_data)


#获取用户信息的接口：查Token查用户——>封装crud——>功能整合成一个工具函数——>路由导入使用
@router.get("/info")

async def get_user_info(user: User = Depends(get_current_user)):
    return success_response(message="获取用户信息成功", data=UserInfoResponse.model_validate(user))


#修改用户信息:验证token——>更新(用户输入数据 put提交——>请求体参数——>定义Pydantic模型类)——>响应结果
#参数：用户输入的 + 验证Token的 +db(调用更新的方法)
@router.put("/update")

async def update_user_info(user_data: UserUpdateRequest, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    user = await users.update_user(db, user.username, user_data)
    return success_response(message="修改用户信息成功", data=UserInfoResponse.model_validate(user))

#修改用户密码
@router.put("/password")
async def update_password(
        password_data: UserChangePasswordRequest,
        db: AsyncSession = Depends(get_db),
        user: User = Depends(get_current_user)
    ):
    res_change_pwd = await users.change_password(db, user, password_data.old_password, password_data.new_password)
    if not res_change_pwd:
        raise HTTPException(status_code=400, detail="修改密码失败，请重试")
    return success_response(message="修改用户密码成功")




