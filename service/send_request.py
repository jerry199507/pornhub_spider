import aiofiles
import sys
import os

sys.path.append(os.path.abspath("../"))
from service.retry import retry


@retry
async def send_request(url, session, get_read=False):
    """
    发送get请求
    """
    async with session.get(url=url) as resp:
        if resp.status == 200:
            return await resp.text() if not get_read else await resp.read()
        else:
            print(f'请求异常:{resp.status}')
            return False


async def download_img(url, path, session):
    """
    下载图片
    """
    img_con = await send_request(url, session, get_read=True)
    async with aiofiles.open(path, 'wb') as f:
        await f.write(img_con)

