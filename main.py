import uvicorn
import os
from config import (server_host, server_port, yh_webhook_path, bot_qq, temp_folder)
from aiocqhttp import CQHttp, Event
from quart import request, jsonify, websocket
from logs import logger
from Platforms.yunhu.handler import handler as YH_handler
from Platforms.qq.handler import msg_handler as QQ_msg_handler
from Platforms.qq.request_handler import handle_request
from Platforms.qq.notice_handler import handle_notice
from Platforms.minecraft.handler import handler as MC_handler
from Platforms.minecraft.clients import mc_clients

if not os.path.exists(temp_folder):
    os.makedirs(temp_folder)

qqBot = CQHttp(__name__)

# QQ - 处理消息
@qqBot.on_message
async def handle_msg(event: Event):
    if event:
        await QQ_msg_handler(event, qqBot)
    else:
        logger.warning("事件为空")
        return {'reply': "我的机体出错了喵", 'at_sender': False}
# QQ - 处理请求
@qqBot.on_request
async def handle_requests(event: Event):
    await handle_request(event, qqBot)
# QQ - 处理通知
@qqBot.on_notice
async def handle_notices(event: Event):
    await handle_notice(event, qqBot)

# 云湖 - 订阅消息的 webhook
@qqBot.server_app.route(yh_webhook_path, methods=['POST'])
async def webhook():
    data = await request.get_json()
    if data:
        await YH_handler(data, qqBot)
        return jsonify({"status": "success"}), 200
    logger.error("接收到的数据为空")
    return jsonify({"status": "error"}), 400

# MC - 处理连接
@qqBot.server_app.websocket("/mc/ws")
async def mc_ws_server():
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive()
            if data.startswith("register:"):
                token = data[len("register:"):].strip()
                logger.info(f"注册服务器, token: {token}")
                mc_clients[token] = websocket
            elif data.startswith("close:"):
                token = data[len("close:"):].strip()
                if token in mc_clients:
                    del mc_clients[token]
                await websocket.close(code=1000)
                logger.info(f"WebSocket 连接已关闭, token: {token}")
                break
            else:
                await MC_handler(data, websocket)
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")

# 服务器 , 启动!
if __name__ == "__main__":
    logger.info(f"启动Webserver,主机: {server_host}, 端口: {server_port}")
    uvicorn.run("main:qqBot.asgi", host=server_host, port=server_port, reload=True)