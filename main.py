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

# MC - 处理连接 (HTTP 路由)
@qqBot.server_app.route("/mc/handle", methods=['POST'])
async def mc_handle():
    try:
        data = await request.get_json()
        logger.info(data)
        token = data.get("token")
        action = data.get("action")
        if not token:
            logger.error("缺少 token 参数")
            return jsonify({"status": "error", "message": "缺少 token 参数"}), 400

        if action == "register":
            # if token in mc_clients:
            #     logger.warning(f"尝试重新注册已存在的 token: {token}")
            #     return jsonify({"status": "error", "message": "该 token 已经注册"}), 400
            mc_clients[token] = None
            logger.info(f"注册服务器, token: {token}")
            return jsonify({"status": "success"}), 200

        if action == "close":
            if token in mc_clients:
                del mc_clients[token]
                logger.info(f"关闭连接, token: {token}")
                return jsonify({"status": "success"}), 200
            # logger.error(f"无效的 token: {token}")
            # return jsonify({"status": "error", "message": "无效的 token 或未注册的服务器"}), 400
        if token in mc_clients:
            messages = await MC_handler(data, token)
            # 返回待发送的消息列表
            return jsonify({"status": "success", "messages": messages}), 200
        else:
            mc_clients[token] = None
            messages = await MC_handler(data, token)
            # 返回待发送的消息列表
            return jsonify({"status": "success", "messages": messages}), 200
        logger.error(f"无效的 token 或未注册的服务器: {token}")
        return jsonify({"status": "error", "message": "无效的 token 或未注册的服务器"}), 488

    except Exception as e:
        logger.exception("服务器内部错误: " + str(e))
        return jsonify({"status": "error", "message": "服务器内部错误"}), 500

# 服务器 , 启动!
if __name__ == "__main__":
    logger.info(f"启动Webserver,主机: {server_host}, 端口: {server_port}")
    uvicorn.run("main:qqBot.asgi", host=server_host, port=server_port, reload=True)