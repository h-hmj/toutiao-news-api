from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from models.news import Category,News

async def get_categories(db: AsyncSession, skip: int=0, limit: int =100):
    stmt = select(Category).offset(skip).limit(limit)
    # 异步执行查询，拿到结果集
    result = await db.execute(stmt)
    return result.scalars().all()

#查询指定分类下的所有新闻
async def get_news_list(db: AsyncSession, category_id:int ,skip: int=0, limit: int =10):
    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all()

#获取新闻总量
async def get_news_count(db: AsyncSession, category_id: int = 0):
    stmt = select(func.count(News.id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalars().one()

#按id查询新闻详情
async def get_news_detail(db: AsyncSession, news_id: int):
    stmt = select(News).where(News.id == news_id)
    result = await db.execute(stmt)
    return result.scalars().one_or_none()

#浏览量+1
async def increase_news_views(db: AsyncSession, news_id: int):
    stmt = update(News).where(News.id == news_id).values(views=News.views + 1)
    result = await db.execute(stmt)
    #检查数据库是否命中了数据——>命中了返回True
    return result.rowcount > 0


#获取相关新闻（同分类、排除自身）
async def get_related_news(db: AsyncSession,category_id: int, news_id: int,  limit: int = 5):
    #order_by()按照浏览量由高到低排列,同时发布时间最新的排列
    stmt = select(News).where(
        News.category_id == category_id,
                   News.id != news_id
                              ).order_by(
                    News.views.desc(),
            News.publish_time.desc()
                ).limit(limit)
    result = await db.execute(stmt)
    # return result.scalars().all()
    #去掉创建时间等等，用列表推导式，推导出列表核心内容，然后在return
    return [{
        "id": news_detail.id,
        "title": news_detail.title,
        "content": news_detail.content,
        "image": news_detail.image,
        "author": news_detail.author,
        "publishTime": news_detail.publish_time,
        "categoryId": news_detail.category_id,
        "views": news_detail.views,
    } for news_detail in result.scalars().all()]

