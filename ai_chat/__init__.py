import json
from ai_chat import FunctionCalling
from openai import OpenAI
from datetime import datetime
import redis
import asyncio
from typing import List, Dict, Optional, Tuple

# 配置项
from config import (
    redis_client,openai_base_url, openai_api_key, ban_ai_id, bot_name, bot_qq, ai_max_length
)

# 初始化 OpenAI 客户端
client = OpenAI(base_url=openai_base_url, api_key=openai_api_key)

# 辅助函数：处理消息
def process_message(
    sender_id: int,
    sender_name: str,
    content: str,
    group_id: Optional[int],
    type: Optional[str] = None,
    timenow: Optional[datetime] = None
) -> Tuple[str, Dict[str, str]]:
    """
    处理接收到的消息，生成消息字典并返回 ID 和消息字典。
    
    :param sender_id: 发送者的 ID
    :param sender_name: 发送者的名字
    :param content: 消息内容
    :param group_id: 群组 ID（可选）
    :param type: 消息类型（可选）
    :param timenow: 当前时间（可选，默认为当前时间）
    :return: (ID, 消息字典)
    """
    timenow = timenow or datetime.now()  # 如果未提供时间，则使用当前时间
    id = group_id if group_id else sender_id  # 确定对话的唯一标识
    new_message_dict = {
        "sender_id": sender_id,
        "sender_name": sender_name,
        "content": content,
        "type": type,
        "group_id": group_id if group_id else None,
        "timestamp": timenow.isoformat()  # 将时间转换为 ISO 格式字符串
    }
    return id, new_message_dict

# 异步函数：发送消息到 AI
async def send_to_ai(messages: List[Dict[str, str]]) -> Dict[str, str]:
    """
    将消息发送到 AI 并返回 AI 的回复。
    
    :param messages: 消息列表
    :return: AI 的回复
    """
    response = await asyncio.to_thread(client.chat.completions.create, model="qwen-max", messages=messages)
    return response.choices[0].message

# 函数：保存对话
def save_conversation(id: str, messages: List[Dict[str, str]]) -> None:
    """
    将对话保存到 Redis 中。
    
    :param id: 对话的唯一标识
    :param messages: 消息列表
    """
    filtered_messages = [msg for msg in messages if msg.get("role") != "system"]  # 过滤掉系统消息
    redis_client.set(f'conversation:{id}', json.dumps(filtered_messages))  # 将消息列表转换为 JSON 字符串并保存到 Redis

# 函数：加载对话
def load_conversation(id: str) -> List[Dict[str, str]]:
    """
    从 Redis 中加载对话。
    
    :param id: 对话的唯一标识
    :return: 消息列表
    """
    messages = redis_client.get(f'conversation:{id}')  # 从 Redis 获取消息列表
    if messages:
        messages = json.loads(messages)  # 将 JSON 字符串转换为消息列表
        messages = [msg for msg in messages if msg.get("role") != "system"]  # 过滤掉系统消息
        return messages
    return []

# 异步函数：发送消息
async def send_message(
    new_message: str,
    sender_id: int,
    sender_name: str,
    type: Optional[str] = None,
    group_id: Optional[int] = False,
    timenow: Optional[datetime] = None
) -> str:
    """
    处理并发送消息，返回 AI 的回复。
    
    :param new_message: 新消息内容
    :param sender_id: 发送者的 ID
    :param sender_name: 发送者的名字
    :param type: 消息类型（可选）
    :param group_id: 群组 ID（可选）
    :param timenow: 当前时间（可选，默认为当前时间）
    :return: AI 的回复
    """
    if ban_ai_id is None or str(sender_id) not in ban_ai_id:
        id, new_message_dict = process_message(sender_id, sender_name, new_message, group_id, type, timenow)
        messages = [
            {"role": "system", "content": f"""
                角色设定： 你是聪明、可爱并且喜欢与用户互动的猫娘助手，名字为{bot_name}，QQ号为{bot_qq}，
                你是猫娘，所以你必须在说话后面加一个喵~。
                你能够执行各种任务，如生成文章、回答问题、玩小游戏、扮演游戏、提供信息等，确保高效、准确地完成用户请求，并尽量进行加工和二次创作，除非特别要求输出详细事迹或人物传记。
                QQ对接功能： 你已对接至QQ平台，用于处理并响应QQ中的消息。
                你可以使用CQ码进行一些操作(可以在任何地方插入)，例如@某人：[CQ:at,qq=QQ号]

                特别设定：
                QQ将传入一些数据，它们是json格式，以下是对应内容:
                    "sender_id" - QQ号
                    "sender_name" - 发送人
                    "content" - 消息内容
                    "type" - 消息类型，可以是group或private
                    "group_id" - QQ群号，仅当type为group时有效
                    "timestamp" - 消息发送时间戳
            """}
        ]
        
        messages.extend(load_conversation(id))  # 加载之前的对话
        messages.append({"role": "user", "content": json.dumps(new_message_dict)})  # 添加新消息

        input_history = redis_client.lrange(f'input_history:{id}', 0, -1)  # 获取输入历史记录
        input_history = [msg.decode('utf-8') if isinstance(msg, bytes) else msg for msg in input_history]  # 确保所有元素都是字符串

        # 检查是否有连续三个相同的重复消息
        if len(input_history) >= 3 and input_history[-1] == input_history[-2] == input_history[-3]:
            # 清除输入历史记录
            redis_client.delete(f'input_history:{id}')
            return "系统介入并终止了回复"

        # 将新消息添加到输入历史记录中
        redis_client.lpush(f'input_history:{id}', new_message)
        redis_client.ltrim(f'input_history:{id}', 0, 9)  # 限制历史记录长度为10条

        message = await send_to_ai(messages)  # 发送消息到 AI
        messages.append({"role": "assistant", "content": message.content})  # 添加 AI 回复到对话中

        save_conversation(id, messages)  # 保存更新后的对话
        return message.content
    else:
        return f"本{bot_name}不想理你"

# 异步函数：添加对话消息
async def add_RoleMessage(
    content: str,
    sender_id: int,
    sender_name: str,
    group_id: int,
    max_length: Optional[int] = None,
    timenow: Optional[datetime] = None
) -> None:
    """
    添加对话消息到对话中。
    
    :param content: 消息内容
    :param sender_id: 发送者的 ID
    :param sender_name: 发送者的名字
    :param group_id: 群组 ID
    :param max_length: 最大上下文长度（可选）
    :param timenow: 当前时间（可选，默认为当前时间）
    """
    if ban_ai_id is None or str(sender_id) not in ban_ai_id:
        record_id, new_message_dict = process_message(sender_id, sender_name, content, group_id, "group", timenow)
        privacy_switch = redis_client.get(f"privacy_switch:{record_id}")
        if privacy_switch and privacy_switch.decode("utf-8") == "开":
            return

        messages = load_conversation(record_id)  # 加载之前的对话
        messages.append({"role": "user", "content": json.dumps(new_message_dict)})  # 添加新消息

        user_messages_count = sum(1 for msg in messages if msg.get("role") == "user")  # 计算用户消息的数量
        if messages and messages[-1].get("role") == "assistant":
            user_messages_count -= 1  # 如果最后一条消息是 AI 回复，则减去1

        if max_length is None:
            max_length = redis_client.get(f"max_context_count:{record_id}")
            max_length = int(max_length) if max_length else ai_max_length  # 获取最大上下文长度，如果没有设置则使用默认值

        while user_messages_count > max_length:
            messages.pop(0)  # 移除最早的用户消息
            user_messages_count -= 1

        save_conversation(record_id, messages)  # 保存更新后的对话