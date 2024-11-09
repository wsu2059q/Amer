import re
import os
import requests
import Platforms.bind as bind
import Platforms.yunhu.send as yhBot
import Platforms.yunhu.upload as yh_upload
from Platforms.minecraft.handler import send_to_mc
from Platforms.minecraft.clients import mc_clients
import ai_chat
import redis
from config import (ban_ai_id, ai_max_length, qq_commands as commands, bot_name, bot_qq, redis_host, redis_port, redis_db, redis_password, temp_folder, replace_blocked_words)
from typing import Dict, Any
from logs import logger
from setu import get_setu
cq_code_pattern = re.compile(r'\[CQ:(.*?)\]')
def check_ws_link(token):
    ws_link = mc_clients.get(token)
    if ws_link:
        logger.info(f"找到 WebSocket 链接: {ws_link}")
    else:
        logger.info(f"未找到 WebSocket 链接")
    return ws_link
class MessageData:
    def __init__(self, data: Dict[str, Any]):
        self.self_id = data.get('self_id', "")
        self.user_id = data.get('user_id', "")
        self.time = data.get('time', "")
        self.message_id = data.get('message_id', "")
        self.message_seq = data.get('message_seq', "")
        self.real_id = data.get('real_id', "")
        self.message_type = data.get('message_type', "")
        self.raw_message = data.get('raw_message', "")
        self.font = data.get('font', "")
        self.sub_type = data.get('sub_type', "")
        self.message_format = data.get('message_format', "")
        self.post_type = data.get('post_type', "")
        self.group_id = data.get('group_id', "")
        
        sender_info = data.get('sender', {})
        self.sender_user_id = sender_info.get('user_id', "")
        self.sender_nickname = sender_info.get('nickname', "")
        self.sender_card = sender_info.get('card', "")
        self.sender_role = sender_info.get('role', "")

async def msg_handler(data: Dict[str, Any], qqBot):
    message_data = MessageData(data)
    logger.info(f"收到消息: {message_data.raw_message}")
    if message_data.message_type == "private":
        airesp = await ai_chat.send_message(message_data.raw_message, message_data.sender_user_id, message_data.sender_nickname)
        await qqBot.send_private_msg(user_id=message_data.sender_user_id, message=airesp)
        logger.info(f"发送私聊回复: {airesp}")
    elif message_data.message_type == "group":
        if message_data.raw_message.startswith('/'):
            await handle_command(message_data, qqBot)
            return
        elif (bot_name in message_data.raw_message or bot_qq in message_data.raw_message):
            if message_data.sender_nickname:
                sender_name = message_data.sender_nickname
            else:
                sender_name = "未知用户"
            airesp = await ai_chat.send_message(message_data.raw_message, message_data.sender_user_id, sender_name, type="qq_group", group_id=message_data.group_id)
            await qqBot.send_group_msg(group_id=message_data.group_id, message=airesp)
            logger.info(f"发送群聊回复: {airesp}")
            return
        else:
            await ai_chat.add_RoleMessage(message_data.raw_message, message_data.sender_user_id, message_data.sender_nickname, message_data.group_id)
        bind_infos = bind.get_info(message_data.group_id, "QQ")
        if bind_infos:
            cq_codes = extract_cq_codes(message_data.raw_message)
            cleaned_message = remove_cq_codes(message_data.raw_message).strip()
            # 替换敏感词
            cleaned_message = replace_blocked_words(cleaned_message)
            cleaned_name = replace_blocked_words(message_data.sender_nickname)
            for bind_info in bind_infos:
                YH_group_id = bind_info["YH_group_id"]
                MCToken = bind_info["MCToken"]
                sync_QQMC_mode = bind_info["sync_QQMC_mode"]
                sync_QQYH_mode = bind_info["sync_QQYH_mode"]
                if sync_QQYH_mode:
                    if cq_codes:
                        for cq_code in cq_codes:
                            processed_cq_code = await process_cq_code(cq_code)
                            if processed_cq_code[0]:
                                yhBot.send(recvId=YH_group_id, recvType="group", contentType="text", content=f"来自 {cleaned_name}:")
                                yhBot.send(recvId=YH_group_id, recvType="group", contentType=processed_cq_code[1], url=processed_cq_code[0])
                                logger.info(f"发送CQ码到YH群: {YH_group_id}, 类型: {processed_cq_code[1]}, key: {processed_cq_code[0]}")
                    if cleaned_message:
                        yhBot.send(recvId=YH_group_id, recvType="group", contentType="text", content=f"[{cleaned_name}]:{cleaned_message}")
                        logger.info(f"发送消息到YH群: {YH_group_id}, 内容: {cleaned_message}")
                if MCToken and sync_QQMC_mode:
                    logger.info(f"MCToken: {MCToken}, sync_QQMC_mode: {sync_QQMC_mode}")
                    #await send_to_mc(MCToken, "指令", 'gamerule commandBlockOutput false')
                    await send_to_mc(MCToken, "消息", f"[{cleaned_name}] : {cleaned_message}")
                    await send_to_mc(MCToken, "指令", 'title @a title {"text":""}')
                    await send_to_mc(MCToken, "指令", f'title @a subtitle {{"text":"{cleaned_message}"}}')
                    logger.info(f"发送消息到Minecraft: {MCToken}, 内容: {cleaned_message}")

# 处理命令
async def handle_command(message_data: MessageData, qqBot):
    command = message_data.raw_message[1:]
    logger.info(f"处理命令: {command}")

    if command == "帮助":
        overview = "📌 指令指南 📌\n\n"
        for idx, cmd in enumerate(commands.keys(), start=1):
            overview += f"{idx}. {cmd}\n"
        overview += "\n输入 /帮助 <编号> 查看详细信息"
        await qqBot.send_group_msg(group_id=message_data.group_id, message=overview)
        logger.info(f"发送帮助信息: {overview}")
    elif command.startswith("帮助 "):
        try:
            command_number = int(command.split()[1])
            if 1 <= command_number <= len(commands):
                cmd_name = list(commands.keys())[command_number - 1]
                cmd_detail = commands[cmd_name]
                await qqBot.send_group_msg(group_id=message_data.group_id, message=f"📌 {cmd_name} 📌\n\n{cmd_detail}")
                logger.info(f"发送详细帮助信息: {cmd_name}, 内容: {cmd_detail}")
            else:
                await qqBot.send_group_msg(group_id=message_data.group_id, message="无效的指令编号")
                logger.warning(f"无效的指令编号: {command_number}")
        except ValueError:
            await qqBot.send_group_msg(group_id=message_data.group_id, message="无效的指令编号，请输入一个整数")
            logger.warning(f"无效的指令编号: {command}")
    elif command.startswith("绑定mc服务器"):
        parts = command.split()
        if len(parts) == 2:
            mc_token = parts[1]
            bind_status = bind.bind_QQMC(message_data.group_id, mc_token)
            if bind_status == "Success":
                await send_to_mc(mc_token, "消息", f"Amer帮你绑定到了QQ群:{message_data.group_id}")
                await qqBot.send_group_msg(group_id=message_data.group_id, message=f"Minecraft 服务器已成功绑定")
                logger.info(f"Minecraft 服务器已成功绑定: {message_data.group_id}")
            elif bind_status == "Failed":
                await qqBot.send_group_msg(group_id=message_data.group_id, message="绑定失败，系统错误")
                logger.error(f"绑定失败: {message_data.group_id}")
            elif bind_status == "None":
                await qqBot.send_group_msg(group_id=message_data.group_id, message="绑定失败，你什么都没有输")
                logger.warning(f"绑定失败: {message_data.group_id}")
            elif bind_status == "Updated":
                await send_to_mc(mc_token, "消息", f"Amer帮你把绑定更新啦,QQ群: {message_data.group_id} 更新绑定到了本服务器")
                await qqBot.send_group_msg(group_id=message_data.group_id, message=f"Minecraft 服务器已更新绑定")
                logger.info(f"Minecraft 服务器已更新绑定: {message_data.group_id}")
            else:
                await qqBot.send_group_msg(group_id=message_data.group_id, message="绑定MC指令格式错误，请使用 /绑定mc服务器 <Token>")
                logger.warning(f"绑定MC指令格式错误: {command}")
    elif command.startswith("来张色图") or command.startswith("色图") or command.startswith("setu"):
        parts = command.split()
        if len(parts) > 1:
            sub_command = parts[1]
            if sub_command in ["tag", "author", "id", "r18"]:
                if len(parts) > 2:
                    if sub_command == "tag":
                        tags = parts[2].split(',')
                        r18 = 1 if "r18" in parts else None
                        response = get_setu(tag=tags, r18=r18)
                    elif sub_command == "author":
                        author = parts[2]
                        r18 = 1 if "r18" in parts else None
                        response = get_setu(author=author, r18=r18)
                    elif sub_command == "id":
                        try:
                            pid = int(parts[2])
                            r18 = 1 if "r18" in parts else None
                            response = get_setu(pid=pid, r18=r18)
                        except ValueError:
                            await qqBot.send_group_msg(group_id=message_data.group_id, message="请输入有效的ID，例如: /来张色图 id 123456")
                            logger.warning(f"无效的ID: {parts[2]}")
                            return
                else:
                    await qqBot.send_group_msg(group_id=message_data.group_id, message="请输入参数，例如: /来张色图 tag 萝莉,白丝")
                    logger.warning(f"缺少参数: {command}")
                    return
            else:
                await qqBot.send_group_msg(group_id=message_data.group_id, message="无效的二级命令")
                logger.warning(f"无效的二级命令: {sub_command}")
                return

            if response.error:
                await qqBot.send_group_msg(group_id=message_data.group_id, message=f"获取色图失败: {response.error}")
                logger.error(f"获取色图失败: {response.error}")
            elif not response.data:
                await qqBot.send_group_msg(group_id=message_data.group_id, message="没有找到符合条件的色图")
                logger.warning(f"没有找到符合条件的色图: {command}")
            else:
                for setu in response.data:
                    image_url = setu.urls['original']
                    details = setu.to_details()
                    cq_code = f"[CQ:image,file={image_url}]"
                    await qqBot.send_group_msg(group_id=message_data.group_id, message=cq_code)
                    await qqBot.send_group_msg(group_id=message_data.group_id, message=details)
                    logger.info(f"发送色图: {setu.title}")
        else:
            response = get_setu()
            if response.error:
                await qqBot.send_group_msg(group_id=message_data.group_id, message=f"获取色图失败: {response.error}")
                logger.error(f"获取色图失败: {response.error}")
            elif not response.data:
                await qqBot.send_group_msg(group_id=message_data.group_id, message="没有找到随机色图")
                logger.warning(f"没有找到随机色图")
            else:
                for setu in response.data:
                    image_url = setu.urls['original']
                    details = setu.to_details()
                    cq_code = f"[CQ:image,file={image_url}]"
                    await qqBot.send_group_msg(group_id=message_data.group_id, message=cq_code)
                    await qqBot.send_group_msg(group_id=message_data.group_id, message=details)
                    logger.info(f"发送色图: {setu.title}")
    elif command.startswith("隐私模式"):
        parts = command.split()
        if len(parts) > 1:
            if parts[1] in ["开", "关"]:
                switch_status = parts[1]
                redis.Redis(host=redis_host, port=redis_port, db=redis_db, password=redis_password).set(f"privacy_switch:{message_data.group_id}", switch_status)
                await qqBot.send_group_msg(group_id=message_data.group_id, message=f"隐私模式已设置为 {switch_status}")
                logger.info(f"隐私模式已设置为: {switch_status}")
            elif parts[1] == "最大上文提示":
                if len(parts) > 2:
                    try:
                        max_context_count = int(parts[2])
                        redis.Redis(host=redis_host, port=redis_port, db=redis_db, password=redis_password).set(f"max_context_count:{message_data.group_id}", max_context_count)
                        await qqBot.send_group_msg(group_id=message_data.group_id, message=f"最大上文提示数已设置为 {max_context_count}")
                        logger.info(f"最大上文提示数已设置为: {max_context_count}")
                    except ValueError:
                        await qqBot.send_group_msg(group_id=message_data.group_id, message="无效的数量，请输入一个整数")
                        logger.warning(f"无效的数量: {parts[2]}")
                else:
                    await qqBot.send_group_msg(group_id=message_data.group_id, message="缺少数量参数，请输入一个整数")
                    logger.warning(f"缺少数量参数: {command}")
            else:
                await qqBot.send_group_msg(group_id=message_data.group_id, message="无效的子指令，请使用 '开'、'关' 或 '最大上文提示'")
                logger.warning(f"无效的子指令: {command}")
        else:
            await qqBot.send_group_msg(group_id=message_data.group_id, message="缺少子指令，请使用 '开'、'关' 或 '最大上文提示'")
            logger.warning(f"缺少子指令: {command}")
    else:
        await qqBot.send_group_msg(group_id=message_data.group_id, message=f"未知指令: {command}")
        logger.warning(f"未知指令: {command}")

# 获取CQ码的函数
def extract_cq_codes(raw_message):
    return cq_code_pattern.findall(raw_message)

# 处理CQ码的函数
async def process_cq_code(cq_code):
    if cq_code.startswith("image"):
        image_url_match = re.search(r'url=(.*?)(?:,|$)', cq_code)
        if image_url_match:
            image_url = image_url_match.group(1).replace("&amp;", "&")
            image_filename_match = re.search(r'file=(.*?)(?:,|$)', cq_code)
            if image_filename_match:
                image_filename = image_filename_match.group(1)
                if not image_filename.lower().endswith('.png'):
                    image_filename += '.png'
            else:
                image_filename = os.path.basename(image_url)
                if not image_filename.lower().endswith('.png'):
                    image_filename += '.png'
            image_data = requests.get(image_url).content
            image_path = os.path.join(temp_folder, image_filename)
            with open(image_path, "wb") as image_file:
                image_file.write(image_data)
            image_key = await yh_upload.image(image_path, image_filename)
            if image_key:
                logger.info(f"处理CQ码图片成功: {image_key}")
                return image_key
            else:
                logger.error(f"处理CQ码图片失败: {image_url}")
                return None, None
    return None, None

# 删除CQ码的函数
def remove_cq_codes(raw_message):
    return cq_code_pattern.sub('', raw_message)