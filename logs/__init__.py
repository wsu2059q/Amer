import logging
import os
from datetime import datetime

# 创建日志记录器
logger = logging.getLogger('logger')
logger.setLevel(logging.DEBUG)  # 设置日志级别

# 创建日志格式
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# 获取当前日期和时间
now = datetime.now()
log_dir = os.path.join(os.getcwd(), 'logs', str(now.year), str(now.month), str(now.day))

# 确保日志目录存在
os.makedirs(log_dir, exist_ok=True)

# 创建日志文件路径，包含时间戳
log_file = os.path.join(log_dir, f'app.log')

# 创建文件处理器
file_handler = logging.FileHandler(log_file)
file_handler.setLevel(logging.DEBUG)  # 文件处理器的日志级别
file_handler.setFormatter(formatter)

# 创建控制台处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # 控制台处理器的日志级别
console_handler.setFormatter(formatter)

# 添加处理器到日志记录器
logger.addHandler(file_handler)
logger.addHandler(console_handler)
# 禁用日志传播
logger.propagate = False

# 导出日志记录器
__all__ = ['logger']