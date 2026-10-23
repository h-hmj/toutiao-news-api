import os

from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession

#1.创建异步引擎
# 连接信息通过环境变量注入，默认值仅用于本地开发；生产环境务必设置环境变量
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123456")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "news_app")
ASYNC_DATABASE_URL = (
    f"mysql+asyncmy://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)
# SQL 日志由环境变量 SQL_ECHO 控制，默认关闭，避免生产环境性能损耗
SQL_ECHO = os.getenv("SQL_ECHO", "false").lower() == "true"
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=SQL_ECHO,  # 是否开启sql日志
    pool_size = 10, #设置连接
)

#2.创建异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,           # 绑定之前创建的异步引擎，决定连接哪个数据库、用什么驱动
    class_=AsyncSession,         # 指定工厂生产出的会话类型为异步Session
    expire_on_commit=False       # commit后对象属性不过期；若为True，commit后再访问属性会触发额外SELECT重新加载
)

#3.创建异步会话
async def get_db():
    async with AsyncSessionLocal() as session:  # 从工厂取出一个Session（相当于打开一条数据库连接）
        try:
            yield session                        # 【请求前】把Session交给路由函数的db参数使用
            await session.commit()               # 【请求后-成功】路由函数正常返回，提交本次事务（INSERT/UPDATE/DELETE生效）
        except Exception:
            await session.rollback()             # 【请求后-异常】路由函数抛出错误，回滚所有未提交操作，保证数据一致性
            raise                                # 继续向上抛出，让FastAPI返回500错误响应
        finally:
            await session.close()                # 【最终清理】无论成功失败，归还连接到连接池，防止资源泄漏
