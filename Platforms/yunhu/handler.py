import json
import Platforms.bind as bind
import Platforms.yunhu.send as yhBot
from logs import logger
from Platforms.minecraft.handler import send_to_mc
from typing import Dict, Any
from config import(message_yh, message_yh_followed, bot_qq, replace_blocked_words)

qqBot = None

import json
from typing import Dict, Any

class MessageData:
    def __init__(self, data: Dict[str, Any]):
        self.version = data.get("version", "")
        self.header_event_id = data.get("header", {}).get("eventId", "")
        self.header_event_type = data.get("header", {}).get("eventType", "")
        self.header_event_time = data.get("header", {}).get("eventTime", "")

        event_info = data.get("event", {})
        sender_info = event_info.get("sender", {})
        self.userid = event_info.get("userId", "")
        self.sender_id = sender_info.get("senderId", "")
        self.sender_type = sender_info.get("senderType", "")
        self.sender_user_level = sender_info.get("senderUserLevel", "")
        self.sender_nickname = sender_info.get("senderNickname", "")

        message_info = event_info.get("message", {})
        self.msg_id = message_info.get("msgId", "")
        self.parent_id = message_info.get("parentId", "")
        self.send_time = message_info.get("sendTime", "")
        self.message_chat_id = message_info.get("chatId", "")
        self.message_chat_type = message_info.get("chatType", "")
        self.content_type = message_info.get("contentType", "")
        self.message_content = message_info.get("content", {}).get("text", "")
        self.message_content_base = message_info.get("content", {})
        self.instruction_id = message_info.get("instructionId", "")
        self.instruction_name = message_info.get("instructionName", "")
        self.command_id = message_info.get("commandId", "")
        self.command_name = message_info.get("commandName", "")

        # 图片相关属性
        self.image_url = self.message_content_base.get("imageUrl", "")
        self.image_name = self.message_content_base.get("imageName", "")
        self.etag = self.message_content_base.get("etag", "")

        self.setting_json = event_info.get('settingJson', '{}')
        self.settings = json.loads(self.setting_json)
        self.setting_group_id = event_info.get("groupId", "")

async def handler(data: Dict[str, Any], qBot):
    global qqBot
    qqBot = qBot
    message_data = MessageData(data)
    logger.info(f"源:{data}")
    event_handlers = {
        "message.receive.normal": handle_normal_message,
        "message.receive.instruction": handle_instruction_message,
        "bot.followed": handle_bot_followed,
        "bot.unfollowed": handle_bot_unfollowed,
        "bot.setting": handle_bot_setting,
        "group.join": handle_group_join,
        "group.leave": handle_group_leave,
        "button.report.inline": handle_button_event,
    }

    handler = event_handlers.get(message_data.header_event_type)
    if handler:
        await handler(message_data)
    else:
        logger.warning(f"未知事件类型: {message_data.header_event_type}")

async def handle_normal_message(message_data: MessageData):
    global qqBot
    logger.info(f"收到来自 {message_data.sender_nickname} 的普通消息: {message_data.message_content}")
    bind_infos = bind.get_info(message_data.message_chat_id, "云湖")
    if bind_infos:
        cleaned_message = replace_blocked_words(message_data.message_content)
        cleaned_name = replace_blocked_words(message_data.sender_nickname)
        for bind_info in bind_infos:
            QQ_group_id = bind_info["QQ_group_id"]
            MCToken = bind_info["MCToken"]
            sync_YHQQ_mode = bind_info["sync_YHQQ_mode"]
            sync_YHMC_mode = bind_info["sync_YHMC_mode"]
            if sync_YHQQ_mode:
                if message_data.image_url:
                    logger.info(f"收到来自 {message_data.sender_nickname} 的图片消息: {message_data.image_url}")
                    await qqBot.send_group_msg(group_id=QQ_group_id, message=f"来自 {cleaned_name}:")
                    await qqBot.send_group_msg(group_id=QQ_group_id, message=f"[CQ:image,file={message_data.image_url}]")
                if cleaned_message:
                    await qqBot.send_group_msg(group_id=QQ_group_id, message=f"[{cleaned_name}]: {cleaned_message}")
            elif sync_YHQQ_mode == False:
                logger.info(f"当前同步模式为 {sync_YHQQ_mode}，消息未发送到QQ群 {QQ_group_id}。")
            logger.info(f"MCToken: {MCToken}, sync_YHMC_mode: {sync_YHMC_mode}")
            if MCToken and sync_YHMC_mode:
                await send_to_mc(MCToken, "消息", f"[{cleaned_name}]: {cleaned_message}")

async def handle_instruction_message(message_data: MessageData):
    if message_data.message_chat_type == "group":
        if message_data.command_name == "帮助":
            yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "markdown", content=message_yh)
            return
        elif message_data.command_name == "群列表":
            bind_infos = bind.get_info(message_data.message_chat_id, "云湖")
            if not bind_infos:
                yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content="没有任何绑定")
            else:
                menu = f"云湖群: {message_data.message_chat_id}"
                for index, bind_info in enumerate(bind_infos, start=1):
                    QQ_group_id = bind_info["QQ_group_id"]
                    sync_YHQQ_mode = bind_info["sync_YHQQ_mode"]
                    sync_QQYH_mode = bind_info["sync_QQYH_mode"]
                    sync_YHMC_mode = bind_info["sync_YHMC_mode"]
                    MCToken = bind_info["MCToken"]
                    # mcserver_status = await send_to_mc(MCToken,"状态","")
                    # 初始化 sync_mode 为 "未设置"
                    sync_mode = "未设置"
                    # 根据 sync_YHQQ_mode 和 sync_QQYH_mode 设置 sync_mode
                    if sync_YHQQ_mode and sync_QQYH_mode:
                        sync_mode = "全同步"
                    elif sync_YHQQ_mode:
                        sync_mode = "云湖到QQ"
                    elif sync_QQYH_mode:
                        sync_mode = "QQ到云湖"
                    else:
                        sync_mode = "停止"
                    if MCToken:
                        pass
                        # menu += f"MC在线状态: {mcserver_status}"
                    else:
                        menu += f"\n{index}. QQ群: {QQ_group_id}, 同步模式: {sync_mode}"
                    
                yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content=menu)
                return
        elif message_data.command_name == "绑定":
            from_infos = message_data.message_content_base.get("formJson", {})
            bd_sync_QQYH_mode = None
            bd_sync_YHQQ_mode = None
            results = []
            group_ids = None
            member_info = await qqBot.get_group_list()
            bd_input_status = False
            for from_info in from_infos.values():
                id = from_info.get('id')
                id_value = from_info.get('value', from_info.get('selectValue'))
                valid_setting_ids = ['wondck', 'rrtllm']
                if id not in valid_setting_ids:
                    logger.error(f"无效的设置ID: {id}")
                    return
                if id == "wondck":
                    if id_value == "全同步":
                        bd_sync_QQYH_mode = True
                        bd_sync_YHQQ_mode = True
                    elif id_value == "QQ到云湖":
                        bd_sync_QQYH_mode = True
                        bd_sync_YHQQ_mode = False
                    elif id_value == "云湖到QQ":
                        bd_sync_QQYH_mode = False
                        bd_sync_YHQQ_mode = True
                    elif id_value == "停止":
                        bd_sync_QQYH_mode = False
                        bd_sync_YHQQ_mode = False
                    else:
                        yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content="无效的设置")
                        return
                if id == "rrtllm":
                    if id_value is not None:
                        group_ids = id_value.split(',')
                        for group_id in group_ids[:]:  # 使用切片来创建一个副本，以便在迭代时可以安全地修改列表
                            is_in_group = False
                            group_id = group_id.strip()  # 去除空白字符
                            if group_id == "":  # 检查是否为空字符串
                                results.append(f"绑定失败, 无效的QQ群号: {group_id}")
                                if group_id in group_ids:  # 检查 group_id 是否在列表中
                                    group_ids.remove(group_id)
                                continue
                            if not group_id.isdigit():  # 检查是否为数字
                                results.append(f"绑定失败, 无效的QQ群号: {group_id}")
                                if group_id in group_ids:  # 检查 group_id 是否在列表中
                                    group_ids.remove(group_id)
                                continue

                            for group in member_info:
                                if group['group_id'] == int(group_id):
                                    is_in_group = True
                                    break
                            if not is_in_group:
                                results.append(f"绑定失败, 机器人不在QQ群{group_id}中")
                                if group_id in group_ids:  # 检查 group_id 是否在列表中
                                    group_ids.remove(group_id)
                                continue
                    else:
                        results.append(f"绑定失败, 请输入需要绑定的QQ群")
                        return
            if group_ids:
                for qq_group_id in group_ids:
                    bind_status = bind.bind_QQYH_group(
                        qq_group_id,
                        message_data.message_chat_id,
                        message_data.sender_id,
                        None,
                        sync_QQYH_mode=bd_sync_QQYH_mode,
                        sync_YHQQ_mode=bd_sync_YHQQ_mode
                    )
                    logger.info(f"绑定状态: {bind_status}")
                    if bind_status == "Success":
                        await qqBot.send_group_msg(
                            group_id=int(qq_group_id),
                            message=f"此群已通过Amer和云湖群聊{message_data.message_chat_id}成功绑定,默认同步模式为全同步.请测试同步功能是否正常!"
                        )
                        results.append(f"云湖群已经绑定到了QQ群{qq_group_id},请检查QQ群是否有提醒")
                    elif bind_status == "Failed":
                        results.append(f"绑定失败,系统错误")
                    elif bind_status == "NotDigit":
                        results.append(f"{qq_group_id} 不是一个有效的QQ群号")
                    elif bind_status == "Repeat":
                        results.append(f"绑定失败,QQ群 {qq_group_id} 你已经绑定过了")
                result_message = "\n".join(results)
                yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content=result_message)
            else:
                result_message = "\n".join(results)
                yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content=result_message)

        elif message_data.command_name == "解绑":
            bind_list = bind.get_info(message_data.message_chat_id, "云湖")
            if not bind_list:
                yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content="该云湖群未绑定任何QQ群")
                return
            from_infos = message_data.message_content_base.get("formJson", {})
            group_ids = []
            results = []
            jb_input_status = False
            jb_switch_status = False
            for from_info in from_infos.values():
                id = from_info.get('id')
                id_value = from_info.get('value', from_info.get('selectValue'))
                valid_setting_ids = ['yvybln', 'rzaadk']
                if id not in valid_setting_ids:
                    logger.error(f"无效的设置ID: {id}")
                    return
                if id == "rzaadk":
                    if id_value is not None:
                        group_ids = id_value.split(',')
                        for group_id in group_ids[:]:
                            is_in_group = False
                            group_id = group_id.strip()  # 去除空白字符
                            if group_id == "":  # 检查是否为空字符串
                                results.append(f"解绑失败, 无效的QQ群号: {group_id}")
                                if group_id in group_ids:  # 检查 group_id 是否在列表中
                                    group_ids.remove(group_id)
                                continue
                            if not group_id.isdigit():  # 检查是否为数字
                                results.append(f"解绑失败, 无效的QQ群号: {group_id}")
                                if group_id in group_ids:  # 检查 group_id 是否在列表中
                                    group_ids.remove(group_id)
                                continue
                    else:
                        jb_input_status = True
                        
                if id == "yvybln":
                    if id_value == True:
                        bind.unbind_YH_allGroup(message_data.message_chat_id)
                        yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content="云湖群已全部解绑")
                        return
                    else:
                        jb_switch_status = True
            if group_ids:
                for group_id in group_ids:
                    unbind_status = bind.unbind_QQYH_group(group_id, message_data.message_chat_id)
                    if unbind_status == "Success":
                            results.append(f"成功解绑群号: {group_id}")
                            await qqBot.send_group_msg(
                                group_id=int(group_id),
                                message=f"此群已从云湖群聊{message_data.message_chat_id}解绑"
                            )
                    elif unbind_status == "BindingNotFound":
                        results.append(f"解绑失败,群号 {group_id} 未绑定过云湖群")
                    elif unbind_status == "Failed":
                        results.append(f"解绑群号 {group_id} 失败")
                    elif unbind_status == "NotDigit":
                        results.append(f"{group_id} 不是一个有效的QQ群号")
                logger.info(f"解绑状态: {unbind_status}")
                result_message = "\n".join(results)
                yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content=result_message)
            else:
                if jb_switch_status and jb_input_status:
                    yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content="请输入需要解绑的QQ群或全部解绑")
                else:
                    result_message = "\n".join(results)
                    yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content=result_message)

        elif message_data.command_name == "同步模式":
            from_infos = message_data.message_content_base.get("formJson", {})
            tb_sync_QQYH_mode = None
            tb_sync_YHQQ_mode = None
            results = []
            tb_input_status = False
            for from_info in from_infos.values():
                id = from_info.get('id')
                id_value = from_info.get('value', from_info.get('selectValue'))
                valid_setting_ids = ['vadtwo', 'tamzxv']
                sync_type = None
                if id not in valid_setting_ids:
                    logger.error(f"无效的设置ID: {id}")
                    return
                if id == "vadtwo":
                    sync_type = id_value
                    if id_value == "全同步":
                        tb_sync_QQYH_mode = True
                        tb_sync_YHQQ_mode = True
                    if id_value == "QQ到云湖":
                        tb_sync_QQYH_mode = True
                        tb_sync_YHQQ_mode = False
                    elif id_value == "云湖到QQ":
                        tb_sync_YHQQ_mode = True
                        tb_sync_QQYH_mode = False
                    elif id_value == "停止":
                        tb_sync_QQYH_mode = False
                        tb_sync_YHQQ_mode = False
                if id == "tamzxv":
                    if id_value is not None:
                        group_ids = id_value.split(',')
                        for group_id in group_ids[:]:
                            group_id = group_id.strip()  # 去除空白字符
                            if group_id == "":  # 检查是否为空字符串
                                results.append(f"无效的QQ群号: {group_id}")
                                if group_id in group_ids:  # 检查 group_id 是否在列表中
                                    group_ids.remove(group_id)
                                continue
                            if not group_id.isdigit():  # 检查是否为数字
                                results.append(f"无效的QQ群号: {group_id}")
                                if group_id in group_ids:  # 检查 group_id 是否在列表中
                                    group_ids.remove(group_id)
                                continue
                    else:
                        tb_input_status = True
            if tb_input_status is False:
                if group_ids:
                    for group_id in group_ids:
                        sync_status = bind.set_sync(sync_YHQQ_mode=tb_sync_YHQQ_mode, sync_QQYH_mode=tb_sync_QQYH_mode, YH_group_id=message_data.message_chat_id, QQ_group_id=group_id)
                        if sync_status == "Success":
                            results.append(f"成功设置群号: {group_id} 的同步模式为: {sync_QQYH_mode}")
                        elif sync_status == "Failed":
                            results.append(f"设置群号 {group_id} 的同步模式失败")
                        elif sync_status == "BindingNotFound":
                            results.append(f"和QQ群 {group_id} 的绑定状态无效")
            else:
                logger.info("tb_input_status")
                sync_status = bind.set_sync(sync_YHQQ_mode=tb_sync_YHQQ_mode, sync_QQYH_mode=tb_sync_QQYH_mode, YH_group_id=message_data.message_chat_id)
                if sync_status == "Success":
                    results.append(f"已更改所有绑定QQ群同步模式为 {sync_type}")
                elif sync_status == "Failed":
                    results.append(f"设置群号 {group_id} 的同步模式失败")
                elif sync_status == "BindingNotFound":
                    results.append(f"和QQ群 {group_id} 的绑定状态无效")
            result_message = "\n".join(results)
            yhBot.send(message_data.message_chat_id, message_data.message_chat_type, "text", content=result_message)
        elif message_data.command_name == "Minecraft服务器同步":
            from_infos = message_data.message_content_base.get("formJson", {})
            results = []
            mc_input_status = False
            mc_sync_YHMC_mode = False
            ningjy = False
            Switch = None
            for from_info in from_infos.values():
                setting_id = from_info.get('id')
                setting_value = from_info.get('value', from_info.get('selectValue'))
                valid_setting_ids = ['bulkps', 'ningjy']
                if setting_id not in valid_setting_ids:
                    logger.error(f"无效的设置ID: {setting_id}")
                    return
                
                if setting_id == 'ningjy':
                    if setting_value is not None:
                        setting_value = setting_value.strip()  # 去除空白字符
                        if setting_value == "":  # 检查是否为空字符串
                            results.append("无效的Token")
                            continue
                    
                    if setting_value is None:
                        ningjy = True
                        break
                    else:
                        Token = setting_value
                if setting_id == 'bulkps':
                    Switch = setting_value
            print(Switch)
            if ningjy:
                yhBot.send(message_data.message_chat_id, "group", "text", content="Token为空捏...")
            elif Switch is False:
                bind.set_sync(sync_YHMC_mode=False, YH_group_id=message_data.message_chat_id, MCToken=Token)
                yhBot.send(message_data.message_chat_id, "group", "text", content="关闭mc同步状态")
            elif Switch is True:
                res = bind.bind_YHMC(message_data.message_chat_id, Token)
                bind.set_sync(sync_YHMC_mode=True, YH_group_id=message_data.message_chat_id, MCToken=Token)
                print(res)
                if res == "Success":
                    logger.info(f"绑定云湖群 {message_data.message_chat_id} 成功")
                    yhBot.send(message_data.message_chat_id, "group", "text", content="Token设置成功")
                elif res == "Failed":
                    logger.error(f"绑定失败,系统错误")
                elif res == "Already":
                    logger.info(f"已经绑定")
                elif res == "Updated":
                    logger.info(f"已更新")
                    await yhBot.send(message_data.message_chat_id, "group", "text", content="Token已更新")
                    await send_to_mc(Token, "消息", f"Amer帮你绑定到了云湖群:{message_data.message_chat_id}")
    else:
        if message_data.command_name == "帮助":
            yhBot.send(message_data.sender_id, "user", "markdown", content=message_yh_followed)
        else:
            yhBot.send(message_data.sender_id, "user", "text", content="请在群内使用指令,您目前可且仅可以使用/帮助命令")
    
    
    
    logger.info(f"Received instruction message from {message_data.sender_nickname}: {message_data.message_content} (Command: {message_data.command_name})")

async def handle_bot_followed(message_data: MessageData):
    yhBot.send(message_data.userid, "user", "markdown", content=message_yh_followed)
    logger.info(f"{message_data.sender_nickname} 关注了机器人")

async def handle_bot_unfollowed(message_data: MessageData):
    unbind_user_allgroup = bind.unbind_user_allgroups(message_data.userid)
    if unbind_user_allgroup == "Success":
        logger.info(f"解绑用户 {message_data.userid} 所有群聊成功")
    elif unbind_user_allgroup == "Failed":
        logger.error(f"解绑用户 {message_data.userid} 所有群聊失败:数据库问题")
    elif unbind_user_allgroup == "NotBind":
        logger.warning(f"解绑用户 {message_data.userid} 未绑定任何群聊")
    logger.info(f"{message_data.sender_nickname} 取消关注了机器人")

async def handle_bot_setting(message_data: dict):
    settings = message_data.settings
    Token = None
    group_Id = message_data.setting_group_id
    for setting in settings.values():
        setting_id = setting.get('id')
        setting_value = setting.get('value', setting.get('selectValue'))
        valid_setting_ids = ['rproit', 'myxpyq']
        if setting_id not in valid_setting_ids:
            logger.error(f"无效的设置ID: {setting_id}")
            return
        if setting_id == 'myxpyq':
            if setting_value.strip() is None:
                yhBot.send(message_data.setting_group_id, "group", "text", content="Token啥也没输捏")
                return
            Token = setting_value.strip()
            print(Token)
        if setting_id == 'rproit':
            Switch = setting_value
    if Switch == 0:
        bind.set_sync(sync_YHMC_mode=False,YH_group_id=group_Id,MCToken=Token)
    elif Switch == 1:
        res = bind.bind_YHMC(group_Id, Token)
        bind.set_sync(sync_YHMC_mode=True,YH_group_id=group_Id,MCToken=Token)
        if res == "Success":
            logger.info(f"绑定云湖群 {group_Id} 成功")
            yhBot.send(group_Id, "group", "text", content="设置成功")
        if res == "Failed":
            logger.error(f"绑定失败")
        if res == "Already":
            logger.warning(f"已就绪")
        if res == "Updated":
            logger.info(f"已更新")
            await yhBot.send(group_Id, "group", "text", content="Token已更新")
        await send_to_mc(Token,"消息",f"Amer帮你绑定到了云湖群:{group_Id}")
    

async def handle_group_join(message_data: MessageData):
    logger.info(f"{message_data.sender_nickname} 加入了群聊 {message_data.message_chat_id}")

async def handle_group_leave(message_data: MessageData):
    logger.info(f"{message_data.sender_nickname} 离开了群聊 {message_data.message_chat_id}")

async def handle_button_event(message_data: MessageData):
    event_data = message_data.data
    msg_id = event_data.get("msgId", "")
    recv_id = event_data.get("recvId", "")
    recv_type = event_data.get("recvType", "")
    user_id = event_data.get("userId", "")
    value = event_data.get("value", "")
    logger.info(f"机器人设置: msgId={msg_id}, recvId={recv_id}, recvType={recv_type}, userId={user_id}, value={value}")