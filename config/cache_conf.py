import json
from typing import Any
import redis.asyncio as redis

REDIS_HOST = "localhost"
REDIS_PORT = 6380
REDIS_DB = 0

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
        # 使用 async with 确保连接正确释放
        async with redis_client:
            return await redis_client.get(key)
    except Exception as e:
        print(f"获取缓存失败：{e}")
        return None


async def get_json_cache(key: str):
    """读取 JSON 格式的列表或字典缓存"""
    try:
        async with redis_client:
            data = await redis_client.get(key)
        if data:
            # 使用 json.loads 是反序列化（还原为字典/列表）
            return json.loads(data)
        return None
    except Exception as e:
        print(f"获取 JSON 缓存失败：{e}")
        return None


async def set_cache(key: str, value: Any, expire: int = 3600):
    """设置缓存（支持字符串、列表、字典），并设置过期时间"""
    try:
        if isinstance(value, (dict, list)):
            # 列表和字典需要先 json.dumps 转为字符串再存储
            value = json.dumps(value, ensure_ascii=False)

        async with redis_client:
            await redis_client.setex(key, expire, value)
        return True
    except Exception as e:
        print(f"设置缓存失败：{e}")
        return False

# 测试调用示例：
# import asyncio
# asyncio.run(set_cache("my_list", [1, 2, 3], expire=600))