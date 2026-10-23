from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from schemas.base import NewsItemBase

# 添加添加浏览历史记录
class HistoryAddRequest(BaseModel):
    news_id: int = Field(..., alias="newsId")


#新闻模型类 + 浏览记录模型类
class HistoryNewsItemResponse(NewsItemBase):
    history_id: int = Field(alias="historyId")
    view_time: datetime = Field(alias="viewTime")  # 与 ORM 模型 History.view_time 及 router 中的 key 保持一致

    model_config = ConfigDict(
        populate_by_name=True,  # 既能用字段名 view_time 也能用别名 viewTime 来赋值
        from_attributes=True  # 允许直接从 SQLAlchemy ORM 对象属性构造该模型（而不仅是 dict）
    )

# 浏览历史列表接口响应模型类
class HistoryListResponse(BaseModel):
    list: list[HistoryNewsItemResponse]
    total: int
    has_more: bool = Field(alias="hasMore")

    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )
