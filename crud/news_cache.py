import asyncio

from cache.news_cache import get_cached_categories, set_cache_categories, get_cache_news_list, set_cache_news_list, \
    cache_news_detail, get_cached_news_detail, cache_related_news, get_cached_related_news, invalidate_news_detail
from config.cache_conf import acquire_lock, release_lock
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from models.news import Category,News
from schemas.base import NewsItemBase

# 空值缓存标记：不存在的新闻也短暂缓存该标记，防止恶意请求反复穿透到数据库（缓存穿透）
NULL_MARKER = {"_null": True}


# 获取新闻分类
async def get_categories(db: AsyncSession, skip: int=0, limit: int =100):
    #尝试从缓存中获取数据
    cached_categories = await get_cached_categories()
    if cached_categories:
        return cached_categories
    # 查询数据库
    stmt = select(Category).offset(skip).limit(limit)
    # 异步执行查询，拿到结果集
    result = await db.execute(stmt)
    categories = result.scalars().all()  # ORM

    # 写入缓存
    if categories:
        categories = jsonable_encoder(categories)
        await set_cache_categories(categories)

    # 返回数据
    return categories


# 获取新闻列表
async def get_news_list(
        db: AsyncSession,
        category_id: int,
        skip: int = 0,
        limit: int = 10
):
    # 先尝试从缓存获取新闻列表
    # 跳过的数量skip = (页码 - 1) * 每页数量 -> 页码 = 跳过的数量 // 每页数量 + 1
    # await get_cache_news_list(分类id, 页码, 每页数量)

    page = skip // limit + 1
    cached_list = await get_cache_news_list(category_id, page, limit)  # 缓存数据 json
    if cached_list:
        # return cached_list  # 要的是 ORM
        return [News(**item) for item in cached_list]

    # 查询的是指定分类下的所有新闻
    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    news_list = result.scalars().all()

    # 写入缓存
    if news_list:
        # 先把 ORM 数据 转换 字典才能写入缓存
        # ORM 转成 Pydantic，再转为 字典
        # by_alias=False 不适用别名，保存 Python 风格，因为 Redis 数据是给后端用的
        news_data = [
            NewsItemBase.model_validate(item).model_dump(mode="json", by_alias=False)
            for item in news_list
        ]
        await set_cache_news_list(category_id, page, limit, news_data)

    return news_list


#获取新闻总量
async def get_news_count(db: AsyncSession, category_id: int = 0):
    stmt = select(func.count(News.id)).where(News.category_id == category_id)
    result = await db.execute(stmt)
    return result.scalars().one()


# 获取新闻详情
async def get_news_detail(
        db: AsyncSession,
        new_id : int
):
    # 先尝试从缓存获取新闻详情
    cached_detail = await get_cached_news_detail(new_id)
    if cached_detail is not None:
        # 命中空值标记：该新闻不存在，直接返回 None，不再穿透数据库
        if cached_detail.get("_null"):
            return None
        return News(**cached_detail)

    # 缓存未命中：用互斥锁保证同一时刻只有一个请求回源重建缓存（防缓存击穿）
    lock_key = f"lock:news:detail:{new_id}"
    if not await acquire_lock(lock_key):
        # 没抢到锁：说明有请求正在重建，短暂等待后再读一次缓存
        await asyncio.sleep(0.1)
        cached_detail = await get_cached_news_detail(new_id)
        if cached_detail is not None:
            return None if cached_detail.get("_null") else News(**cached_detail)
        # 等待后仍未命中，降级直接查库，保证可用性

    try:
        # 查询数据库
        stmt = select(News).where(News.id == new_id)
        result = await db.execute(stmt)
        news = result.scalar_one_or_none()

        if news:
            news_data = jsonable_encoder(news)
            await cache_news_detail(new_id, news_data)
        else:
            # 查不到也写入短 TTL 空值标记，防缓存穿透
            await cache_news_detail(new_id, NULL_MARKER, expire=60)

        return news
    finally:
        await release_lock(lock_key)


# 查询新闻当前浏览量（浏览量自增后回读，保证接口返回最新值而非旧值）
async def get_news_views(db: AsyncSession, news_id: int):
    stmt = select(News.views).where(News.id == news_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


#浏览量+1
async def increase_news_views(db: AsyncSession, news_id: int):
    stmt = update(News).where(News.id == news_id).values(views=News.views + 1)
    result = await db.execute(stmt)
    #检查数据库是否命中了数据——>命中了返回True
    if result.rowcount > 0:
        # 数据已变更，主动失效详情缓存，避免后续请求读到旧浏览量（Cache-Aside 失效策略）
        await invalidate_news_detail(news_id)
        return True
    return False


#获取相关新闻（同分类、排除自身）
async def get_related_news(db: AsyncSession,category_id: int, news_id: int,  limit: int = 5):
    #先从缓存读取内容（用相关新闻自己的缓存函数，key 才和写入端一致）
    cached_related = await get_cached_related_news(news_id, category_id)
    if cached_related:
        return cached_related
    #order_by()按照浏览量由高到低排列,同时发布时间最新的排列
    stmt = select(News).where(
        News.category_id == category_id,
                   News.id != news_id
                              ).order_by(
                    News.views.desc(),
            News.publish_time.desc()
                ).limit(limit)
    result = await db.execute(stmt)
    related_news = result.scalars().all()

    related_list = [
        {
            "id": item.id,
            "title": item.title,
            "content": item.content,
            "image": item.image,
            "author": item.author,
            "publishTime": item.publish_time,
            "categoryId": item.category_id,
            "views": item.views
        }
        for item in related_news
    ]

    # 写入缓存，空值则不写，不空则写入缓存
    if related_list:
        # jsonable_encoder 把 datetime 转成可序列化的字符串
        await cache_related_news(news_id, category_id, jsonable_encoder(related_list))

    return related_list

