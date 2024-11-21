import json
import os
import redis
from logs import logger
# 读取配置
config_file_path = os.getenv('CONFIG_FILE_PATH', 'config/config.json')
try:
    with open(config_file_path, 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print(f"配置文件 {config_file_path} 未找到")
    exit(1)
except json.JSONDecodeError:
    print(f"配置文件 {config_file_path} 格式错误")
    exit(1)

# 全局变量
temp_folder = config['temp_folder']

server_host = config['server']['host']
server_port = config['server']['port']

bot_name = config['qq']['bot_name']
bot_qq = config['qq']['bot_qq']
qq_commands = config['commands']['qq']

yh_token = config['yh']['token']
yh_webhook_path = config['yh']['webhook']['path']
message_yh = config['Message']['message-YH']
message_yh_followed = config['Message']['message-YH-followed']

weather_api_url = config['WeatherApi']['url']
weather_api_token = config['WeatherApi']['token']

openai_base_url = config['OpenAI']['base_url']
openai_api_key = config['OpenAI']['api_key']
ban_ai_id = config['AI']['Ban']['ban_ai_id']
ai_max_length = config['AI']['max_length']
blocked_words = config['blocked_words']

def replace_blocked_words(message: str) -> str:
    replaced_words = []
    for category, words in blocked_words.items():
        for word in words:
            if word in message:
                message = message.replace(word, '***')
                replaced_words.append((word, category))
    if replaced_words:
        logger.info(f"屏蔽字符: {replaced_words}")
    return message
'''
    数据库
    1. Redis
    2. SQLite
'''
# Redis
redis_host = config['Redis']['host']
redis_port = config['Redis']['port']
redis_db = config['Redis']['db']
redis_password = config['Redis']['password']
try:
    redis_client = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        password=redis_password,
        decode_responses=True  # 解码响应为字符串
    )
    redis_client.ping()  # 测试连接
except redis.ConnectionError:
    logger.warning(f"无法连接到 Redis 服务器: {redis_host}:{redis_port}")
    exit(1)
# SQLite
sqlite_db_path = config['SQLite']['db_path']
