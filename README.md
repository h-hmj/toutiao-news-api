# toutiao_backend — 今日头条风格新闻聚合后端

基于 **FastAPI** 的异步新闻聚合后端项目，提供新闻浏览、用户注册登录、收藏、浏览历史等完整 REST API。适合作为 FastAPI + SQLAlchemy 2.0 异步全栈学习的实践项目。

## 技术栈

| 组件 | 技术选型 | 说明 |
|---|---|---|
| Web 框架 | FastAPI | 自动生成 OpenAPI 文档（`/docs`） |
| ORM | SQLAlchemy 2.0（async） | `Mapped` / `mapped_column` 声明式模型 |
| 数据库 | MySQL 8 + asyncmy | 异步驱动，连接池 `pool_size=10` |
| 缓存 | Redis（redis.asyncio） | 新闻分类 / 列表 / 详情 / 相关新闻缓存 |
| 密码加密 | passlib + bcrypt | 注册、改密均加密存储 |
| 认证 | 自定义 Token（uuid4） | 令牌落库 `user_token` 表，有效期 7 天 |
| 数据校验 | Pydantic v2 | `schemas/` 定义请求体与响应模型 |

## 功能总览

- **新闻模块**：分类列表、分页新闻列表、新闻详情（浏览量 +1、相关推荐）
- **缓存层**：热点查询走 Redis，按数据稳定性设置不同 TTL，降低 MySQL 压力
- **用户模块**：注册、登录、查询个人信息、修改个人信息、修改密码
- **收藏模块**：收藏检查、添加 / 取消收藏、分页收藏列表、一键清空
- **历史模块**：添加浏览记录（重复浏览自动更新时间）、分页历史列表、单条删除、一键清空
- **基础设施**：统一响应格式 `{code, message, data}`、全局异常处理器、CORS 中间件、登录依赖注入 `get_current_user`

## 项目结构

```text
toutiao_backend/
├── main.py                    # 应用入口：CORS、异常处理器注册、挂载 4 组路由
├── test_main.http             # PyCharm HTTP 测试文件（内容已过时）
├── config/
│   ├── db_conf.py             # MySQL 异步引擎、会话工厂、get_db 依赖
│   └── cache_conf.py          # Redis 异步客户端、get/set 缓存通用函数
├── models/                    # SQLAlchemy ORM 模型（建表依据）
│   ├── news.py                # Category(news_category) / News(news)
│   ├── users.py               # User(user) / UserToken(user_token)
│   ├── favorite.py            # Favorite(favorite)
│   └── history.py             # History(history)
├── schemas/                   # Pydantic 请求/响应模型
│   ├── base.py                # NewsItemBase（新闻公共字段）
│   ├── users.py               # 注册/登录/用户信息/改密模型
│   ├── favorite.py            # 收藏请求与列表响应模型
│   └── history.py             # 历史记录请求与列表响应模型
├── crud/                      # 数据库操作封装层
│   ├── news.py                # 新闻直查 MySQL 版本
│   ├── news_cache.py          # 新闻查询 + Redis 缓存版本（路由实际使用）
│   ├── users.py               # 用户增查改、Token 生成与校验
│   ├── favorite.py            # 收藏增删查、联表分页列表
│   └── history.py             # 历史记录 upsert、联表分页列表
├── cache/
│   └── news_cache.py          # 新闻缓存 key 设计与读写函数
├── routers/                   # API 路由层
│   ├── news.py                # /api/news/*
│   ├── users.py               # /api/user/*
│   ├── favorite.py            # /api/favorite/*
│   └── history.py             # /api/history/*
└── utils/
    ├── auth.py                # get_current_user：解析 Authorization 头校验登录
    ├── security.py            # bcrypt 密码哈希 / 验证
    ├── response.py            # success_response 统一响应包装
    ├── exception.py           # 4 个全局异常处理函数
    └── exception_handlers.py  # 向 app 注册异常处理器
```

## 架构与请求链路

```mermaid
graph TD
    C[客户端] --> M["main.py（FastAPI 应用）"]
    M --> R["routers/ 路由层<br/>news · users · favorite · history"]
    R --> U["utils/auth.py<br/>get_current_user 登录校验"]
    R --> D["crud/ 数据操作层"]
    D --> DB[(MySQL news_app<br/>asyncmy 异步驱动)]
    D --> RC["cache/news_cache.py"]
    RC --> RD[(Redis :6380)]
```

分层职责：

1. **routers/** 只做参数接收、权限依赖、组装响应，不写 SQL
2. **crud/** 封装所有数据库读写（select / update / delete / join）
3. **cache/** 只管 Redis key 的命名与读写，被 `crud/news_cache.py` 调用
4. **models/** 定义表结构；**schemas/** 定义数据进出格式
5. **config/** 提供 `get_db`、`get_cache` 等基础设施依赖

## 环境准备与启动

### 1. 安装依赖

```powershell
pip install fastapi uvicorn sqlalchemy asyncmy redis passlib bcrypt
```

### 2. 准备 MySQL

创建数据库（表结构需已存在，当前项目未内置建表脚本）：

```sql
CREATE DATABASE IF NOT EXISTS news_app
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

连接信息在 [config/db_conf.py](config/db_conf.py) 中硬编码：

```text
mysql+asyncmy://root:123456@localhost:3306/news_app
```

> 修改账号 / 密码 / 库名请直接编辑该文件。

### 3. 启动 Redis

本项目使用 **6380 端口**（非默认端口），配置见 [config/cache_conf.py](config/cache_conf.py)：

```powershell
redis-server --port 6380
```

### 4. 运行服务

```powershell
uvicorn main:app --reload
```

- 接口文档：http://127.0.0.1:8000/docs
- 根路径探活：`GET /` 返回 `{"message": "Hello World"}`

## 数据库表结构

| 表名 | 模型 | 关键字段 | 说明 |
|---|---|---|---|
| `news_category` | Category | id, name(唯一), sort_order, created_at, updated_at | 新闻分类 |
| `news` | News | id, title, description, content, image, author, category_id(FK), views, publish_time | 新闻主表；索引：`category_id`、`publish_time` |
| `user` | User | id, username(唯一), password(bcrypt), nickname, avatar, gender(enum: male/female/unknown), bio, phone(唯一) | 用户表 |
| `user_token` | UserToken | id, user_id(FK), token(唯一), expires_at | 登录令牌，一用户一条，重复登录刷新 |
| `favorite` | Favorite | id, user_id(FK), news_id(FK), created_at | 联合唯一约束 `(user_id, news_id)`，防重复收藏 |
| `history` | History | id, user_id(FK), news_id(FK), view_time | 同一用户同一新闻只保留一条，重复浏览更新时间 |

## API 接口文档

所有接口以 `/api` 为前缀。统一响应格式：

```json
{ "code": 200, "message": "success", "data": { } }
```

**认证方式**：登录后将返回的 `token` 放入请求头，支持两种格式：

```text
Authorization: Bearer <token>
Authorization: <token>
```

### 新闻模块（无需登录）

| 方法 | 路径 | 参数 | 说明 |
|---|---|---|---|
| GET | `/api/news/categories` | `skip`(默认0)、`limit`(默认10) | 新闻分类列表（Redis 缓存） |
| GET | `/api/news/list` | `categoryId`(必填)、`page`(默认1)、`pageSize`(默认100) | 分类下新闻分页列表（Redis 缓存） |
| GET | `/api/news/detail` | `id`(必填) | 新闻详情 + 浏览量 +1 + 5 条相关新闻（详情/相关均有缓存） |

`GET /api/news/detail?id=1` 响应示例：

```json
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 1,
    "title": "……",
    "content": "……",
    "image": "http://……",
    "author": "……",
    "publishTime": "2026-10-17T15:00:00",
    "categoryId": 2,
    "views": 128,
    "relatedNews": [ { "id": 5, "title": "……", "views": 90 } ]
  }
}
```

### 用户模块

| 方法 | 路径 | 需登录 | 请求体 / 参数 | 说明 |
|---|---|---|---|---|
| POST | `/api/user/register` | 否 | `{"username", "password"}` | 注册即登录，返回 token + 用户信息 |
| POST | `/api/user/login` | 否 | `{"username", "password"}` | 登录，返回 token + 用户信息 |
| GET | `/api/user/info` | 是 | — | 获取当前用户信息 |
| PUT | `/api/user/update` | 是 | `{"nickname?", "avatar?", "gender?", "bio?", "phone?"}` | 部分字段更新（只更新传入字段） |
| PUT | `/api/user/password` | 是 | `{"oldPassword", "newPassword"}` | 修改密码（新密码至少 6 位） |

`POST /api/user/register` 响应示例：

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "token": "3f2c8a…-uuid",
    "userInfo": { "id": 1, "username": "demo", "nickname": null, "avatar": "https://…cat.jpeg", "gender": "unknown", "bio": null }
  }
}
```

curl 示例：

```powershell
# 注册
curl -X POST http://127.0.0.1:8000/api/user/register -H "Content-Type: application/json" -d '{\"username\":\"demo\",\"password\":\"123456\"}'

# 携带 token 获取用户信息
curl http://127.0.0.1:8000/api/user/info -H "Authorization: Bearer <token>"
```

### 收藏模块（全部需要登录）

| 方法 | 路径 | 参数 | 说明 |
|---|---|---|---|
| GET | `/api/favorite/check` | `newsId` | 是否已收藏，`data.isFavorite` |
| POST | `/api/favorite/add` | `{"newsId"}` | 添加收藏（重复收藏受唯一约束保护） |
| GET | `/api/favorite/list` | `page`(≥1)、`pageSize`(1~100) | 收藏列表：新闻字段 + favoriteId / favoriteTime，按收藏时间倒序 |
| DELETE | `/api/favorite/remove` | `newsId` | 取消收藏 |
| DELETE | `/api/favorite/clear` | — | 清空当前用户全部收藏 |

### 浏览历史模块（全部需要登录）

| 方法 | 路径 | 参数 | 说明 |
|---|---|---|---|
| POST | `/api/history/add` | `{"newsId"}` | 添加记录；已存在则刷新 `view_time` |
| GET | `/api/history/list` | `page`、`pageSize` | 历史列表：新闻字段 + historyId / viewTime，按浏览时间倒序 |
| DELETE | `/api/history/delete/{news_id}` | 路径参数 | 删除单条记录 |
| DELETE | `/api/history/clear` | — | 清空当前用户全部记录 |

## 认证机制说明

Token 方案为**数据库存储型**（非 JWT），流程如下：

1. 注册 / 登录成功 → `crud/users.create_token()` 生成 `uuid4`，写入 `user_token` 表，过期时间 **7 天**（同一用户重复登录为刷新，不新增记录）
2. 需登录接口通过依赖 `utils/auth.get_current_user`：
   - 读取 `Authorization` 头（兼容 `Bearer xxx` 与裸 token）
   - 调 `get_user_by_token()` 查库校验存在性与过期时间
   - 失败统一返回 401
3. 密码使用 bcrypt 哈希存储，任何接口不回传密码字段

## Redis 缓存策略

缓存读写封装在 [cache/news_cache.py](cache/news_cache.py)，由 [crud/news_cache.py](crud/news_cache.py) 在查询前命中、未命中回源 MySQL 并写回（Cache-Aside 模式）。TTL 按"数据越稳定，缓存越持久"设计：

| Key | 内容 | TTL |
|---|---|---|
| `news:categories` | 全部新闻分类 | 7200s |
| `news_list:{categoryId}:{page}:{pageSize}` | 新闻列表分页页 | 1800s |
| `news:detail:{newsId}` | 新闻详情 | 300s |
| `news:related:{newsId}:{categoryId}` | 相关新闻 | 1800s |

不同 key 使用不同 TTL，也避免了同时过期引发缓存雪崩。

## 统一响应与异常处理

- 成功响应统一走 [utils/response.py](utils/response.py) 的 `success_response()`，内部用 `jsonable_encoder` 兼容 Pydantic / ORM 对象
- [utils/exception_handlers.py](utils/exception_handlers.py) 注册 4 级全局异常处理：

| 异常类型 | HTTP 状态码 | 返回 message |
|---|---|---|
| `HTTPException` | 原状态码 | 业务错误详情 |
| `IntegrityError` | 400 | 用户名已存在 / 关联数据不存在等 |
| `SQLAlchemyError` | 500 | 数据库操作失败，请稍后重试 |
| `Exception` | 500 | 服务器内部错误 |

`utils/exception.py` 中 `DEBUG_MODE = True` 时，500 类错误的 `data` 会附带异常类型、详情与 traceback（教学用途，生产应关闭）。

## 已知问题与开发注意事项

以下为当前代码中已确认的问题，后续迭代建议修复：

1. **多余的误导入**：[crud/favorite.py](crud/favorite.py) 首行 `from dns.e164 import query` 是编辑器自动导入产物，导致项目隐式依赖 `dnspython`，应删除
2. **三套 `Base` 未统一**：`models/news.py`、`models/users.py`、`models/favorite.py` 各自定义了 `DeclarativeBase`，无法用一条 `Base.metadata.create_all()` 建全所有表；目前依赖手工建表，建议统一 Base 并引入 Alembic 迁移
3. **`datetime.now()` 写成了立即调用**：[models/users.py](models/users.py) 中 `User.created_at/updated_at` 的 `default=datetime.now()`（带括号）在模块导入时求值一次，所有新行会共用同一时间戳，应改为 `default=datetime.now`（不带括号）
4. **清空接口消息错误**：`remove_all_favorites` / `delete_all_history` 返回 `bool`，但路由消息写成 `f"清空了{result}条记录"`，实际会显示"清空了True条记录"，应返回 `rowcount`
5. **详情浏览量有两处滞后**：详情接口返回的 `views` 是本次 +1 前的旧值（UPDATE 后未 `refresh`）；且详情缓存 300s，缓存期间 `views` 不更新
6. **响应字段命名不统一**：`categories` / `list` 返回 snake_case（ORM 直出），`detail` / 收藏 / 历史返回 camelCase，前端需两套约定；建议统一经 `schemas/` 输出
7. **配置硬编码**：数据库密码、Redis 地址直接写死在 `config/`，建议迁移到 `.env` + `pydantic-settings`
8. **CORS 全开**：`allow_origins=["*"]` 与 `allow_credentials=True` 组合仅适用于开发环境
9. **token 过期只校验不删除**：过期令牌仍留在 `user_token` 表，长期运行建议定期清理

## 后续规划（参考）

- 新闻管理端（发布 / 编辑 / 下架）
- JWT 替换数据库 Token，支持多端登录与主动登出
- 图片上传、关键词搜索、分页改用游标
- pytest + httpx 接口测试、Alembic 表迁移、日志与配置管理

## License

仅用于学习交流。
