from fastapi import APIRouter, Depends, Query
from config.db_conf import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from crud import news_cache
from utils.response import success_response

#创建 APIRouter 实例
router = APIRouter(prefix="/news", tags=["news"])

#接口实现流程
#1.模块化路由——>API接口规范文档
#2.定义模型类——>数据库表
#3.在crud文件里面创建文件，封装操作数据库的方法
#4.在路由处理函数里面调用crud文件里面的方法，响应结果

#获取新闻分类

@router.get("/categories")
async def get_categories(skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)):
    #先获取数据库里面的新闻分类数据——>先定义模型类——>封装查询的数据方法
    categories = await news_cache.get_categories(db, skip, limit)
    return success_response(message="获取分类成功", data=categories)

#获取新闻列表
@router.get("/list")
async def get_news_list(
        category_id: int =  Query(...,alias="categoryId"), 
        page: int =1,
        page_size: int = Query(100,alias="pageSize"), 
        db: AsyncSession = Depends(get_db)
    ):
    #思路：处理分页规则——>查询新闻列表——>计算总量——>计算是否还有更多
    offset = (page - 1) * page_size
    news_list = await news_cache.get_news_list(db , category_id, offset, page_size)
    total = await news_cache.get_news_count(db, category_id)

    #查看是否还有更多
    has_more = total > offset + len(news_list)
    return success_response(message="获取新闻列表成功", data={
        "list": news_list,
        "total": total,
        "hasMore": has_more
    })

#获取新闻具体详情
@router.get("/detail")
async def get_news_detail(news_id: int= Query(...,alias="id"), db: AsyncSession = Depends(get_db)):
    #查询新闻详情 + 浏览量+1 + 相关新闻
    #1.查询新闻详情
    news_detail = await news_cache.get_news_detail(db, news_id)
    if not news_detail:
        raise HTTPException(status_code=404, detail="新闻不存在")

    #2.增加浏览量
    views_res = await news_cache.increase_news_views(db, news_detail.id)
    if not views_res:
        raise HTTPException(status_code=404, detail="新闻不存在")

    #3.回读自增后的最新浏览量（详情对象是自增前查询的，直接用会返回旧值）
    current_views = await news_cache.get_news_views(db, news_detail.id)

    #4.查询相关新闻
    related_news = await news_cache.get_related_news(db, news_detail.category_id, news_detail.id)

    return success_response(message="success", data={
        "id": news_detail.id,
        "title": news_detail.title,
        "content": news_detail.content,
        "image": news_detail.image,
        "author": news_detail.author,
        "publishTime": news_detail.publish_time,
        "categoryId": news_detail.category_id,
        "views": current_views,
        "relatedNews": related_news
    })