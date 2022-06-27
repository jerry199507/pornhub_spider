import asyncio


def retry(func):
    """
    重试函数装饰器
    """
    async def inner_wrapper(*args, **kwargs):
        while True:
            try:
                return await func(*args, **kwargs)
            except Exception :
                await asyncio.sleep(3)
                continue
    return inner_wrapper

