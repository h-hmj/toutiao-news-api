from fastapi import HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter
from fastapi import Depends
from config.db_conf import get_db
from crud import favorite
from crud.favorite import is_news_favorite, add_news_favorite, remove_news_favorite
from utils.response import success_response
from schemas.favorite import FavoriteCheckResponse, FavoriteAddRequest, FavoriteListResponse
from models.users import User
from utils.auth import get_current_user

router = APIRouter(prefix="/favorite", tags=["favorite"])

# 检查收藏
@router.get("/check")
async def check_favorite(
        news_id: int = Query(..., alias="newsId"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
      ):
    #调用 crud 层的数据库函数,查询「当前登录用户是否已经收藏了这条新闻」,并把查询结果(True/False)存入 is_favorited 变量。
    is_favorited = await is_news_favorite(db, user.id, news_id)

    #返回的是带字段名的对象 {"isFavorite": true}。
    return success_response(message="检查收藏状态成功",data=FavoriteCheckResponse(isFavorite=is_favorited))

# 添加收藏
@router.post("/add")
async def add_favorite(
        data: FavoriteAddRequest,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
      ):
    result = await add_news_favorite(db, user.id, data.news_id)
    return success_response(message="添加收藏成功", data=result)


#获取收藏列表
@router.get("/list")
async def get_favorite_list(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
      ):
    rows, total = await favorite.get_favorite_list(db, user.id, page, page_size)
    favorite_list = [{
        **news.__dict__,
        "favorite_time": favorite_time,
        "favorite_id": favorite_id
    } for news, favorite_time, favorite_id in rows]

    has_more = total > page * page_size
    # 返回的是带字段名的对象 {"list": [], "total": 100, "hasMore": true}
    data = FavoriteListResponse(list=favorite_list, total=total, hasMore=has_more)
    return success_response(message="获取收藏列表成功", data=data)


#取消收藏
@router.delete("/remove")
async def remove_favorite(
        news_id: int = Query(..., alias="newsId"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
      ):
    result = await remove_news_favorite(db, user.id, news_id)

    if not result:
        raise HTTPException(status_code=404, detail="取消收藏失败")

    return success_response(message="取消收藏成功", data=result)


#清空列表
@router.delete("/clear")
async def clear_favorite(
        user: User = Depends(get_current_user),   #认证用户token
        db: AsyncSession = Depends(get_db)
      ):
    result = await favorite.remove_all_favorites(db, user.id)
    return success_response(message=f"清空了{result}条记录")
