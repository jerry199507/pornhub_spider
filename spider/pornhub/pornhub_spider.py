import parsel
import re
import os
import xlrd
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import json
from pyppeteer import launch
import sys
import subprocess


CONCURRENCY = 3
semaphore = asyncio.Semaphore(CONCURRENCY)

sys.path.append(os.path.abspath("../../"))
from config.config import VIDEO_PATH, EXCEL_PATH
from service.mkdir import mkdir
from service.download_video import download_video


class PornhubSpider(object):

    def __init__(self):
        self.headers = {
            "referer": "https://cn.pornhub.com/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/96.0.4664.93 Safari/537.36",
        }
        self.domain_name = 'cn.pornhub.com'
        self.path = os.path.join(VIDEO_PATH, self.domain_name)                   # 所有文件存储路径

    async def main(self):
        video_excel = os.path.join(EXCEL_PATH, 'Pornhub视频清单.xlsx')
        excel = xlrd.open_workbook(video_excel)                                  # 打开excel
        sh = excel.sheet_by_name('Sheet1')
        await mkdir(self.path)
        print('-------------------------开始爬取-------------------------')
        tasks = []
        timeout = aiohttp.ClientTimeout(total=60000)
        connector = aiohttp.TCPConnector(ssl=False)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout, headers=self.headers) as session:
            for i in range(sh.nrows):
                url = sh.row_values(i)[0]
                task = asyncio.create_task(self.parser_data(url, session))
                tasks.append(task)
            await asyncio.gather(*tasks)

    async def parser_data(self, url, session):
        async with semaphore:
            try:
                browser = await launch(options={'args': ['--no-sandbox']}, headless=True)
                page = await browser.newPage()
                await page.goto(url, options={'timeout': 60000})
                selector = parsel.Selector(await page.content())
                # 标题
                video_title = selector.xpath('//*[@id="hd-leftColVideoPage"]/div[1]/div[3]/h1/span/text()').get()
                # 视频
                script = selector.xpath('//div[@class="original mainPlayerDiv"]/script[1]/text()').get().strip()
                var_name = re.search('var flashvars_(.*) =', script).group(1)  # 提取flashvars变量名
                js = f"""
                    () => {{
                    var playerObjList = {{}}
                    {script}
                    var num = flashvars_{var_name}['mediaDefinitions'].length - 1
                    while (flashvars_{var_name}['mediaDefinitions'][num]['format'] != "mp4")
                    {{
                        num -= 1
                    }}
                    return flashvars_{var_name}['mediaDefinitions'][num]['videoUrl']
                    }}
                    """
                video_urls = await page.evaluate(js)  # 执行这段JS代码
                await asyncio.sleep(3)
                await page.goto(video_urls)
                bs = BeautifulSoup(await page.content(), 'html.parser')
                data = json.loads(bs.text)
                download_url = data[-1]['videoUrl']   # 选择最高清的版本
                video_name = '.'.join([video_title, 'mp4'])
                save_path = os.path.join(self.path, video_name)
                await download_video(download_url, save_path, session, headers=self.headers)
            except Exception as e:
                print(f"爬取失败：{url}, 错误信息:{e}")
            finally:
                await page.close()
                await browser.close()

    def __del__(self):
        # 杀死chrome进程
        # cmd = "ps -ef|grep chrome|grep -v grep |awk '{print $2}'|xargs kill -9"
        # p = subprocess.Popen(cmd, shell=True)
        # p.wait()
        print('-------------------------爬取结束-------------------------')


if __name__ == '__main__':
    run = PornhubSpider()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run.main())


