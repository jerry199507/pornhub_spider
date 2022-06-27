import os


async def mkdir(path):
    """
    创建文件夹
    """
    if not os.path.exists(path):
        os.makedirs(path)
        return True
    else:
        return False