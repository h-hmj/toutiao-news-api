from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# 全项目唯一的声明式基类：所有模型共用一套 metadata，
# 才能用 Base.metadata.create_all() 一次性建出全部表
class Base(DeclarativeBase):
    pass


# 公共时间戳列，供需要的表以 Mixin 方式复用
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        comment="创建时间"
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now,
        onupdate=datetime.now,
        comment="更新时间"
    )
