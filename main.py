from fastapi import FastAPI
from routers import news,users
from fastapi.middleware.cors import CORSMiddleware
from utils.exception_handlers import register_exception_handlers
from routers import favorite
from routers import history
app = FastAPI()


# 注册异常处理器
register_exception_handlers(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   #允许的源，开发阶段允许所有源，生产环境需要指定源
    allow_credentials=True,   #允许携带cookie
    allow_methods=["*"],   #允许的请求方法
    allow_headers=["*"],   #允许的请求头
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

#挂载路由，注册路由
app.include_router(news.router, prefix="/api")
app.include_router(users.router, prefix="/api")

app.include_router(favorite.router, prefix="/api")

app.include_router(history.router, prefix="/api")



