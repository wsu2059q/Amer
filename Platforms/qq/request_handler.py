from logs import logger

async def handle_request(event, bot):
    if event.detail_type == 'friend':
        await bot.set_friend_add_request(flag=event.flag, approve=True)
    elif event.detail_type == 'group':
        await bot.set_group_add_request(flag=event.flag, sub_type=event.sub_type, approve=True)
    else:
        logger.warning(f"未知的请求类型: {event.detail_type}")