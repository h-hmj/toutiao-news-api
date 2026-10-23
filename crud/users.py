import uuid

from fastapi import HTTPException
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from models.users import User, UserToken
from schemas.users import UserRequest, UserUpdateRequest
from utils import security
from datetime import datetime, timedelta




#按用户名去 user 表里查一个人，查到返回 User ORM 对象，查不到返回 None。
async def get_user_by_username(db: AsyncSession, username: str):
    query = select(User).where(User.username == username)
    result = await db.execute(query)
    return result.scalars().one_or_none()


#创建用户
async def create_user(db: AsyncSession, user_data:UserRequest):
    #先密码加密处理
    hashed_password = security.get_hash_password(user_data.password)
    user = User(username=user_data.username, password=hashed_password)
    db.add(user)
    # flush：把 SQL 发送到数据库执行（唯一约束冲突等错误会在这里立即抛出），
    # 但不提交事务——事务边界统一由 get_db 依赖在请求结束后 commit
    await db.flush()
    await db.refresh(user)    #从数据库读取最新的user
    return user


#生成Token
async def create_token(db: AsyncSession, user_id: int):
    #生成Token + 设置过期时间 ——>查询数据库当前用户是否有Token ——>有：更新，没有：添加
    token = str(uuid.uuid4())
    #设置过期时间，七天过期
    expires_at = datetime.now() + timedelta(days=7)
    #查询数据库是否有token
    query = select(UserToken).where(UserToken.user_id == user_id)
    result = await db.execute(query)
    user_token = result.scalars().one_or_none()
    if user_token:
        #更新token
        user_token.token = token
        user_token.expires_at = expires_at
    else:
        #添加token
        user_token = UserToken(user_id=user_id, token=token, expires_at=expires_at)
        db.add(user_token)
    await db.flush()
    await db.refresh(user_token)
    return token

#验证用户是否存在
async def authenticate_user(db: AsyncSession, username: str, password: str):
    user = await get_user_by_username(db, username)
    if not user:
        return None
    if not security.verify_password(password, user.password):
        return None
    return user


#根据token查询用户：验证Token——>查询用户
async def get_user_by_token(db: AsyncSession, token: str):
    #查token
    query = select(UserToken).where(UserToken.token == token)
    result = await db.execute(query)
    db_token = result.scalars().one_or_none()
    if not db_token:
        return None
    if datetime.now() > db_token.expires_at:
        # 过期令牌：顺手从库里删除，避免 user_token 表残留无效记录，再要求重新登录
        await db.delete(db_token)
        await db.flush()
        return None
    #根据token查用户
    query = select(User).where(User.id == db_token.user_id)
    result = await db.execute(query)
    return result.scalars().one_or_none()

#更新用户信息：根据用户名查询用户——>更新用户信息——>返回更新后的用户信息
async def update_user(db: AsyncSession, username: str, user_data: UserUpdateRequest):
#user_data.model_dump(exclude_unset=True) = 把更新对象转成字典，且只包含前端真正传过来的字段，UPDATE 语句不会返回任何数据行
    query = update(User).where(User.username == username).values(user_data.model_dump(exclude_unset=True))
    result = await db.execute(query)

    #检查更新
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="用户不存在")

    #获取更新后的用户
    updated_user = await get_user_by_username(db, username)
    return updated_user



#修改用户密码:验证旧密码——>新密码加密——>修改密码
async def change_password(db: AsyncSession, user:User, old_password: str, new_password: str):
    #验证密码是否一致
    if not security.verify_password(old_password, user.password):
        raise HTTPException(status_code=400, detail="旧密码错误")
    #新密码加密
    hashed_new_pwd = security.get_hash_password(new_password)
    user.password = hashed_new_pwd
    db.add(user)  #把改过密码的 user 交给会话，flush 发送 SQL、commit 由 get_db 统一完成
    await db.flush()
    await db.refresh(user)
    return {"message": "修改密码成功"}

