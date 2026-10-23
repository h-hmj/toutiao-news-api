from datetime import datetime

from sqlalchemy import Integer, DateTime, ForeignKey, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from models.base import Base
from models.users import User
from models.news import News


class History(Base):
    """
    浏览历史表ORM模型
    """
    __tablename__ = 'history'

    # 创建索引
    # UniqueConstraint：同一用户同一新闻只保留一条记录，配合 upsert 语句从数据库层杜绝并发重复插入
    __table_args__ = (
        UniqueConstraint('user_id', 'news_id', name='user_news_history_unique'),
        Index('fk_history_user_idx', 'user_id'),
        Index('fk_history_news_idx', 'news_id'),
        Index('idx_view_time', 'view_time'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="历史ID")
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey(User.id), nullable=False, comment="用户ID")
    news_id: Mapped[int] = mapped_column(Integer, ForeignKey(News.id), nullable=False, comment="新闻ID")
    view_time: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, comment="浏览时间")

    def __repr__(self):
        return f"<History(id={self.id}, user_id={self.user_id}, news_id={self.news_id}, view_time={self.view_time})>"
