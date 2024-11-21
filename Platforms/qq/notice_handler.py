from logs import logger
from config import bot_qq

async def handle_group_increase(event, bot):
    try:
        info = await bot.get_group_member_info(group_id=event.group_id, user_id=event.user_id)
        nickname = info.get('nickname', '新人')
        
        if info['user_id'] == bot_qq:
            logger.info(f"机器人 {nickname} 加入了群聊 {event.group_id}")
            await bot.send(event, message=f'{nickname}来咯~ {nickname}是一直可可爱爱的猫娘喔,欢迎cue{nickname}～', at_sender=False)
        else:
            logger.info(f"新成员 {nickname} 加入了群聊 {event.group_id}")
            await bot.send(event, message=f'欢迎{nickname}～', at_sender=True, auto_escape=True)
    except Exception as e:
        logger.error(f"处理群成员增加通知时发生错误: {e}")

async def handle_notice(event, bot):
    if event.detail_type == 'group_increase':
        await handle_group_increase(event, bot)
    else:
        logger.warning(f"未知的通知类型: {event.detail_type}")