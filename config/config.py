import os
import sys
import logging


# 数据库配置
MONGO_CONN_STR = 'xxxxx'


# 存储路径配置
VIDEO_PATH = '/data/app/videos'
EXCEL_PATH = '../../excel'

# 日志配置
file_name = os.path.basename(sys.argv[0]).replace('.py', '')
logging.basicConfig(level=logging.ERROR,
                    filename=f'../../log/{file_name}.log',
                    filemode='a',
                    format=
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                    )
console = logging.StreamHandler()
console.setLevel(logging.ERROR)
logging.getLogger('').addHandler(console)