import asyncio
import json
from collections import defaultdict, deque
import Platforms.bind as bind
import Platforms.yunhu.send as yhBot
from logs import logger
from config import replace_blocked_words
from Platforms.minecraft.clients import mc_clients

# 存储待发送消息的字典，每个 token 对应一个消息队列
pending_messages: defaultdict[str, deque[str]] = defaultdict(deque)

class EventHandler:
    def __init__(self):
        """
        初始化事件处理器，定义各种事件的处理函数。
        """
        self.event_handlers: dict[str, callable] = {
            "玩家加入": self.handle_player_join,
            "玩家退出": self.handle_player_quit,
            "聊天消息": self.handle_chat_message,
            "玩家命令": self.handle_player_command,
            "玩家死亡": self.handle_player_death,
            "玩家重生": self.handle_player_respawn,
            "服务器加载": self.handle_server_load,
        }

    async def handle_player_join(self, sender_name: str, token: str) -> None:
        """
        处理玩家加入事件。

        :param sender_name: 加入的玩家名称
        :param token: 与事件相关的唯一标识符
        """
        logger.info(f"玩家加入: {sender_name}")
        # 处理玩家加入事件的具体逻辑

    async def handle_player_quit(self, sender_name: str, token: str) -> None:
        """
        处理玩家退出事件。

        :param sender_name: 退出的玩家名称
        :param token: 与事件相关的唯一标识符
        """
        logger.info(f"玩家退出: {sender_name}")
        # 处理玩家退出事件的具体逻辑

    async def handle_chat_message(self, sender_name: str, message: str, token: str) -> None:
        """
        处理聊天消息事件。

        :param sender_name: 发送消息的玩家名称
        :param message: 聊天消息内容
        :param token: 与消息相关的唯一标识符
        """
        logger.info(f"聊天消息来自 {sender_name}: {message}")
        bind_infos = bind.get_info(token, "MC")
        from main import qqBot
        for bind_info in bind_infos:
            cleaned_message = replace_blocked_words(message)
            if bind_info["QQ_group_id"]:
                await qqBot.send_group_msg(group_id=bind_info["QQ_group_id"], message=f"{sender_name}: {cleaned_message}")
            if bind_info["YH_group_id"] and bind_info["sync_YHMC_mode"]:
                yhBot.send(recvId=bind_info["YH_group_id"], recvType="group", contentType="text", content=f"{sender_name}: {cleaned_message}")

    async def handle_player_command(self, sender_name: str, command: str, token: str) -> None:
        """
        处理玩家命令事件。

        :param sender_name: 发送命令的玩家名称
        :param command: 命令内容
        :param token: 与命令相关的唯一标识符
        """
        logger.info(f"玩家命令来自 {sender_name}: {command}")
        # 处理玩家命令事件的具体逻辑

    async def handle_player_death(self, sender_name: str, death_message: str, token: str) -> None:
        """
        处理玩家死亡事件。

        :param sender_name: 死亡的玩家名称
        :param death_message: 死亡消息内容
        :param token: 与死亡事件相关的唯一标识符
        """
        logger.info(f"玩家死亡: {sender_name}, 消息: {death_message}")
        # 处理玩家死亡事件的具体逻辑

    async def handle_player_respawn(self, sender_name: str, token: str) -> None:
        """
        处理玩家重生事件。

        :param sender_name: 重生的玩家名称
        :param token: 与事件相关的唯一标识符
        """
        logger.info(f"玩家重生: {sender_name}")
        # 处理玩家重生事件的具体逻辑

    async def handle_server_load(self, token: str) -> None:
        """
        处理服务器加载事件。

        :param token: 与事件相关的唯一标识符
        """
        logger.info("服务器加载")
        # 处理服务器加载事件的具体逻辑

async def handler(data: dict, token: str) -> list:
    """
    处理接收到的消息，并返回待发送的消息列表。

    :param data: 接收到的数据
    :param token: 与消息相关的唯一标识符
    :return: 待发送的消息列表
    """
    try:
        # 获取消息内容
        message_data = data
        
        # 检查必要的字段
        if not all(key in message_data for key in ["type"]):
            logger.error("消息格式错误: 缺少必要字段")
            return []

        event_type = message_data["type"]
        sender_name = message_data["senderName"]
        value = message_data.get("value", "")

        if event_type == "心跳":
            # logger.info(f"收到{token}心跳")
            return await handle_heartbeat(token)
        logger.info(f"收到消息: {message_data}")
        event_handler = EventHandler()
        handler_func = event_handler.event_handlers.get(event_type)
        if handler_func:
            if event_type in ["玩家加入", "玩家退出", "玩家重生", "服务器加载"]:
                await handler_func(sender_name, token)
            elif event_type in ["聊天消息", "玩家命令", "玩家死亡"]:
                await handler_func(sender_name, value, token)
        else:
            logger.info(f"未知事件: {event_type}")

    except json.JSONDecodeError as e:
        logger.error(f"JSON 解析错误: {e}")
        return []
    except Exception as e:
        logger.error(f"服务器内部错误: {e}")
        return []

async def handle_heartbeat(token: str) -> list:
    """
    处理心跳消息，发送待发送的消息队列中的消息。

    :param token: 与心跳消息相关的唯一标识符
    :return: 待发送的所有消息列表
    """
    # 从 pending_messages 中取出对应 token 消息队列
    messages = pending_messages.get(token, deque())
    if messages:
        # 收集所有待发送的消息
        sent_messages = []
        while messages:
            message = messages.popleft()
            logger.info(f"发送消息: {message}")
            sent_messages.append(message)
        # 清空该 token 队列
        pending_messages[token] = deque()
        return sent_messages
    else:
        return []

async def send_to_mc(token: str, message_type: str, message_content: str) -> None:
    """
    根据消息类型构建消息并将其通过保存的 WebSocket 连接发送。

    :param token: 与消息相关的唯一标识符
    :param message_type: 消息类型
    :param message_content: 消息内容
    """
    if message_type == "状态":
        message = f"{token}, 状态, 服务器, "
    elif message_type == "指令":
        message = f"{token}, 指令, 服务器, {message_content}"
    elif message_type == "消息":
        message = f"{token}, 消息, 服务器, §7{message_content}"
    else:
        logger.info(f"未知消息类型: {message_type}")
        return
    # 将消息添加到待发送的消息队列
    pending_messages[token].append(message)