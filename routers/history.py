from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from config.db_conf import get_db
from crud import history
from crud.history import delete_all_history, delete_history
from models.users import User
from schemas.history import HistoryAddRequest, HistoryNewsItemResponse, HistoryListResponse
from utils.auth import get_current_user
from utils.response import success_response


router = APIRouter(prefix="/history", tags=["history"])

#添加浏览历史记录
@router.post("/add")
async def add_history(
        data: HistoryAddRequest,
        user: User = Depends(get_current_user),
         db: AsyncSession = Depends(get_db)
    ):
    result = await history.add_history(db, user.id, data.news_id)

    return success_response(message="添加浏览历史记录成功", data=result)


# 获取浏览记录历史列表
@router.get("/list")

async def get_history_list(
        page: int = Query(1, ge=1),
        page_size: int = Query(10, ge=1, le=100, alias="pageSize"),
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
    ):
    rows, total = await history.get_history_list(db, user.id, page, page_size)
    history_list = [HistoryNewsItemResponse.model_validate({
        **news.__dict__,
        "view_time": view_time,
        "history_id": history_id
    }) for news, view_time, history_id in rows]

    has_more = total > page * page_size

    data = HistoryListResponse(list=history_list, total=total, hasMore=has_more)
    return success_response(message="获取历史记录列表成功",data=data)


#删除历史记录
@router.delete("/delete/{news_id}")
async def remove_history(
        news_id: int,
        user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
      ):
    result = await delete_history(db, user.id, news_id)

    if not result:
        raise HTTPException(status_code=404, detail="删除浏览记录失败")

    return success_response(message="删除浏览记录成功", data=result)


#清空历史记录
@router.delete("/clear")
async def clear_history(
        user: User = Depends(get_current_user),   #认证用户token
        db: AsyncSession = Depends(get_db)
      ):
    result = await delete_all_history(db, user.id)
    return success_response(message=f"清空了{result}条记录")
