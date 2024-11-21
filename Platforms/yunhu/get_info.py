import requests
import re

def decode_utf8(text):
    return re.sub(r'\\u([09a-fA-F]{4})', lambda x: chr(int(x.group(1), 16)), text)

def fetch_data(url, check_string, patterns):
    try:
        response = requests.get(url, timeout=5, verify=False)
        response.raise_for_status()
    except requests.RequestException as e:
        return {"code": -1, "msg": f"请求失败: {str(e)}"}

    if check_string not in response.text:
        data = {}
        for key, pattern in patterns.items():
            match = re.search(pattern, response.text)
            if match:
                value = match.group(1)
                if key.endswith('Id') or key == 'headcount':
                    value = int(value)
                elif key == 'private':
                    value = value == "1"
                elif key == 'isVip':
                    value = value != "0"
                elif key == 'medal':
                    value = [decode_utf8(m) for m in re.findall(pattern, response.text)]
                else:
                    value = decode_utf8(value)
                data[key] = value
        if all(key in data for key in patterns):
            return {"code": 1, "msg": "ok", "data": data}
        else:
            return {"code": -3, "msg": "解析数据失败"}
    else:
        return {"code": 2, "msg": "对象不存在，请检查输入的 ID 是否正确"}

def get_bot_info(input_id):
    url = f"https://www.yhchat.com/bot/homepage/{input_id}"
    check_string = "data-v-4f86f6dc>ID </span>"
    patterns = {
        "botId": r'ID\s+(\w+)',
        "id": r'id:(\d+)',
        "nickname": r'nickname:"(.*?)"',
        "nicknameId": r'nicknameId:(\d+)',
        "avatarId": r'avatarId:(\d+)',
        "avatarUrl": r'avatarUrl:"(.*?)"',
        "introduction": r'<div[^>]*>\s*机器人简介\s*<\/div>\s*<div[^>]*>\s*([\s\S]*?)\s*<\/div>',
        "createBy": r'createBy:"(.*?)"',
        "private": r'private:(.*?)\}'
    }
    return fetch_data(url, check_string, patterns)

def get_group_info(input_id):
    url = f"https://www.yhchat.com/group/homepage/{input_id}"
    check_string = "data-v-6eef215f>ID </span>"
    patterns = {
        "groupId": r'ID\s+(\w+)',
        "id": r'id:(\d+)',
        "name": r'name:"(.*?)"',
        "introduction": r'introduction:"(.*?)"',
        "createBy": r'createBy:"(.*?)"',
        "avatarId": r'avatarId:(\d+)',
        "avatarUrl": r'avatarUrl:"(.*?)"',
        "headcount": r'headcount:(\d+)',
        "category": r'<div[^>]*>\s*分类\s*<\/div>\s*<div[^>]*>\s*(.*?)\s*<\/div>'
    }
    return fetch_data(url, check_string, patterns)

def get_user_info(input_id):
    url = f"https://www.yhchat.com/user/homepage/{input_id}"
    check_string = "data-v-34a9b5c4>ID </span>"
    patterns = {
        "userId": r'userId:"(.*?)"',
        "nickname": r'nickname:"(.*?)"',
        "avatarUrl": r'avatarUrl:"(.*?)"',
        "registerTime": r'registerTime:(\d+)',
        "registerTimeText": r'registerTimeText:"(.*?)"',
        "onLineDay": r'在线天数<\/span> <span[^>]*>(\d+)天<\/span>',
        "continuousOnLineDay": r'连续在线<\/span> <span[^>]*>(\d+)天<\/span>',
        "isVip": r'isVip:(.*?)}/',
        "medal": r'<div class="medal-container"[^>]*>\s*(.*?)\s*<\/div>'
    }
    return fetch_data(url, check_string, patterns)