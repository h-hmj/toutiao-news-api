from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker,AsyncSession

#1.创建异步引擎
ASYNC_DATABASE_URL = "mysql+asyncmy://root:123456@localhost:3306/news_app?charset=utf8mb4"
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=True,  # 是否开启sql日志
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
