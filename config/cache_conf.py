import json
import logging
import os
from typing import Any

import redis.asyncio as redis

logger = logging.getLogger(__name__)

# Redis 连接信息通过环境变量注入，默认值仅用于本地开发
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6380"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

# 创建异步 Redis 客户端
redis_client = redis.Redis(
    host=REDIS_HOST,   #Redis服务器主机地址
    port=REDIS_PORT,   #Redis端口号
    db=REDIS_DB,       #Redis数据库编号，0-15
    decode_responses=True  # 自动将返回的字节转为字符串
)


# 设置 和 读取（字符串 和 列表或字典）

async def get_cache(key: str):
    """读取普通字符串缓存"""
    try:
        return await redis_client.get(key)
    except Exception as e:
        logger.warning(f"获取缓存失败：{e}")
        return None


async def get_json_cache(key: str):
    """读取 JSON 格式的列表或字典缓存"""
    try:
        data = await redis_client.get(key)
        if data:
            # 使用 json.loads 是反序列化（还原为字典/列表）
            return json.loads(data)
        return None
    except Exception as e:
        logger.warning(f"获取 JSON 缓存失败：{e}")
        return None


async def set_cache(key: str, value: Any, expire: int = 3600):
    """设置缓存（支持字符串、列表、字典），并设置过期时间"""
    try:
        if isinstance(value, (dict, list)):
            # 列表和字典需要先 json.dumps 转为字符串再存储
            value = json.dumps(value, ensure_ascii=False)

        await redis_client.setex(key, expire, value)
        return True
    except Exception as e:
        logger.warning(f"设置缓存失败：{e}")
        return False


async def delete_cache(key: str):
    """删除指定缓存（用于数据变更后的缓存失效）"""
    try:
        await redis_client.delete(key)
        return True
    except Exception as e:
        logger.warning(f"删除缓存失败：{e}")
        return False


async def acquire_lock(key: str, expire: int = 30) -> bool:
    """
    获取分布式互斥锁（SETNX + 过期时间），用于防止缓存击穿：
    热点 key 过期瞬间，只允许一个请求回源重建缓存，其余请求短暂等待后重试缓存。
    Redis 异常时直接放行（返回 True），保证降级可用。
    """
    try:
        return bool(await redis_client.set(key, "1", nx=True, ex=expire))
    except Exception as e:
        logger.warning(f"获取缓存锁失败：{e}")
        return True


async def release_lock(key: str):
    """释放互斥锁"""
    try:
        await redis_client.delete(key)
    except Exception as e:
        logger.warning(f"释放缓存锁失败：{e}")
