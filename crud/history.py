from models.history import History
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from datetime import datetime

from models.news import News


#添加浏览历史记录
async def add_history(db: AsyncSession,
                      user_id: int,
                      news_id: int,
                      ):
    """
    添加历史记录，如果已存在则更新浏览时间，如果不存在则插入新记录
    """
    query = select(History).where(History.user_id == user_id, History.news_id == news_id)
    result = await db.execute(query)
    existing_history = result.scalar_one_or_none()
    #检查result是否存在
    if existing_history:
        #更新浏览时间
        existing_history.view_time = datetime.now()
        await db.commit()
        await db.refresh(existing_history)
        return existing_history

    else:
        #插入新记录
        history = History(user_id=user_id, news_id=news_id)
        db.add(history)
        await db.commit()
        await db.refresh(history)
        return history


#获取浏览记录历史列表
async def get_history_list(
        db: AsyncSession,
        user_id: int,
        page: int =1,
        page_size: int =10
):
    offset = (page - 1) * page_size
    count_query = select(func.count()).where(History.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one_or_none()

    query = (select(News, History.view_time.label("view_time"), History.id.label("history_id"))
             .join(History, News.id == History.news_id)
             .where(History.user_id == user_id)
             .order_by(History.view_time.desc())
             .offset(offset).limit(page_size)
             )
    result = await db.execute(query)
    rows = result.all()
    return rows, total


#删除历史记录
async def delete_history(
        db: AsyncSession,
        user_id: int,
        news_id: int
    ):
    query = delete(History).where(History.user_id == user_id, History.news_id == news_id)
    result = await db.execute(query)
    await db.commit()
    # 若返回true则代表删除成功，若为false则代表删除失败
    return result.rowcount > 0


#清空历史记录
async def delete_all_history(
        db: AsyncSession,
        user_id: int
    ):
    query = delete(History).where(History.user_id == user_id)
    result = await db.execute(query)
    await db.commit()
    # 若返回true则代表删除成功，若为false则代表删除失败
    return result.rowcount > 0

