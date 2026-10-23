from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends, Header, HTTPException
from config.db_conf import get_db
from crud import users

"""
从请求头里解析 token，验证用户身份，把「当前登录用户」作为依赖提供给需要登录的接口。
"""

#整合 根据Token查询用户，返回用户
async def get_current_user(
        authorization: str = Header(None),   # 请求头参数，认证令牌
        db: AsyncSession = Depends(get_db)
    ):
    #校验请求头是否存在
    if not authorization:
        raise HTTPException(status_code=401, detail="未提供认证令牌")
    #兼容 "Bearer xxx" 和直接传 token 两种格式
    parts = authorization.split(" ")
    token = parts[1] if len(parts) > 1 else parts[0]
    #校验令牌是否存在
    if not token:
        raise HTTPException(status_code=401, detail="认证令牌格式错误")
    user = await users.get_user_by_token(db, token)
    #判断令牌是否有效或已经过期
    if not user:
        raise HTTPException(status_code=401, detail="令牌无效或已过期，请重新登录")
    return user