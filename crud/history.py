from models.history import History
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from sqlalchemy.dialects.mysql import insert as mysql_insert
from datetime import datetime

from models.news import News


#添加浏览历史记录
async def add_history(db: AsyncSession,
                      user_id: int,
                      news_id: int,
                      ):
    """
    添加历史记录，如果已存在则更新浏览时间，如果不存在则插入新记录。
    使用 MySQL 原生的 INSERT ... ON DUPLICATE KEY UPDATE 单语句完成 upsert，
    配合表上的唯一约束 user_news_history_unique，并发下也不会插入重复记录
    （旧写法"先查再插"存在竞态窗口）。
    """
    stmt = mysql_insert(History).values(
        user_id=user_id,
        news_id=news_id,
        view_time=datetime.now(),
    )
    stmt = stmt.on_duplicate_key_update(view_time=stmt.inserted.view_time)
    await db.execute(stmt)

    # UPDATE 语句不返回数据行，回读一次拿到最新记录返回
    query = select(History).where(History.user_id == user_id, History.news_id == news_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


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
    # 若返回true则代表删除成功，若为false则代表删除失败
    return result.rowcount > 0


#清空历史记录
async def delete_all_history(
        db: AsyncSession,
        user_id: int
    ):
    query = delete(History).where(History.user_id == user_id)
    result = await db.execute(query)
    # 返回删除的行数（而不是 bool，供路由拼接"清空了N条记录"消息）
    return result.rowcount

