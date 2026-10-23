from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from schemas.base import NewsItemBase


"""
schemas/favorite.py 是收藏模块的 Pydantic 数据模型（Schema）文件，负责定义收藏相关接口的请求参数校验和响应数据序列化格式。
它是分层架构中连接 routers 层与前端的数据契约层。
"""

# 检查收藏状态
class FavoriteCheckResponse(BaseModel):
    is_favorite: bool = Field(..., alias="isFavorite")

# 添加收藏
class FavoriteAddRequest(BaseModel):
    news_id: int = Field(..., alias="newsId")

# 收藏列表中的单条新闻响应模型类
# 继承 NewsItemBase（包含新闻的 id、title、image、author、category_id 等基础字段），
# 在其基础上额外叠加"收藏"相关的两个字段，实现：新闻模型 + 收藏模型 的组合响应结构
class FavoriteNewsItemResponse(NewsItemBase):
    favorite_id: int = Field(alias="favoriteId")          # 收藏记录的主键 ID，序列化给前端时输出为 favoriteId
    favorite_time: datetime = Field(alias="favoriteTime") # 用户收藏该新闻的时间，序列化给前端时输出为 favoriteTime

    model_config = ConfigDict(
        populate_by_name=True,  # 既能用字段名 favorite_id 也能用别名 favoriteId 来赋值
        from_attributes=True  # 允许直接从 SQLAlchemy ORM 对象属性构造该模型（而不仅是 dict）
    )

# 收藏列表接口响应模型类
# 对应前端分页列表所需的完整数据结构：列表数据 + 总数 + 是否有下一页
class FavoriteListResponse(BaseModel):
    list: list[FavoriteNewsItemResponse]  # 当前页的收藏新闻列表，每个元素是"新闻+收藏信息"的组合模型
    total: int                            # 用户的收藏总条数，前端可用于展示/计算总页数
    has_more: bool = Field(alias="hasMore")  # 是否还有更多数据（用于前端"加载更多/上拉刷新"判断），输出为 hasMore

    model_config = ConfigDict(
        populate_by_name=True,   # 允许用字段名 has_more 或别名 hasMore 两种方式赋值
        from_attributes=True     # 支持直接从 ORM 对象构造，方便 crud 层返回的数据直接转换
    )

