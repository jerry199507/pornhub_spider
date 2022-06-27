import asyncio
from tqdm import tqdm
import sys
import os

sys.path.append(os.path.abspath("../"))
from service.retry import retry


@retry
async def get_redirect_url(url, session):
    """
    获取重定向后的视频链接
    """
    async with session.get(url, allow_redirects=False) as resp:
        new_url = resp.headers['location']
        return new_url


@retry
async def get_content_length(url, session, headers):
    """
    获取视频文件大小
    """
    async with session.get(url, headers=headers) as resp:
        content_length = int(resp.headers['Content-Length'])
        return content_length


async def download_video(url, path, session, headers, count=16):
    """
    下载视频
    """
    headers_1 = {'Range': 'bytes=0-0'}.update(headers)
    content_length = await get_content_length(url, session, headers_1)
    fp = open(path, 'wb')
    fp.truncate(content_length)             # 创建和视频一样大小的文件
    fp.close()
    queue = asyncio.Queue()                 # 将文件按大小分解为任务队列
    num = int(content_length) / 1024 / 1024
    num = 1 if num < 30 else (5 if num < 200 else 10)
    size = 1024 * 1024 * num                # 每个区块大小
    amount = content_length // size or 1
    for i in range(amount):
        start = i * size
        if i == amount - 1:
            end = content_length
        else:
            end = start + size
        if start > 0:
            start += 1
        # 设置请求视频位置
        headers_2 = {
            'Range': f'bytes={start}-{end}'
        }
        headers_2.update(headers)  # 合并请求头
        queue.put_nowait([session, path, url, start, headers_2])
    with tqdm(total=content_length, unit='', desc=f'下载：{path}', unit_divisor=1024, ascii=True,
              unit_scale=True) as bar:
        await asyncio.gather(*[__down_video(bar, queue) for _ in range(count)])


async def __down_video(bar, queue):
    """
    path: 保存位置+名字
    session: 请求客户端
    video_url: 视频地址
    start: 视频开始写入位置
    headers: 请求头，包含请求长度和位置
    bar: 进度条
    """
    while not queue.empty():
        task = await queue.get()
        session, path, video_url, start, headers = task[0], task[1], task[2], task[3], task[4]
        while True:
            try:
                async with session.get(video_url, headers=headers) as resp:
                    with open(path, 'rb+') as f:
                        # 写入位置，指针移到指定位置
                        f.seek(start)
                        async for b in resp.content.iter_chunked(1024 * 1024):
                            f.write(b)
                            # 更新进度条，每次请求得到的长度
                            bar.update(len(b))
                        break
            except Exception as e:
                await asyncio.sleep(3)
                continue
