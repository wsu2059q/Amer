import requests
import json
from config import(yh_token)

def send(recvId, recvType, contentType, content='content', fileName='fileName', url='url', buttons=None):
    headers = {'Content-Type': 'application/json'}
    sampleDict = {
        "recvId": recvId,
        "recvType": recvType,
        "contentType": contentType,
        "content": {}
    }

    if contentType == 'text' or contentType == 'markdown':
        sampleDict['content']['text'] = content
    elif contentType == 'image':
        sampleDict['content']['imageKey'] = url
    elif contentType == 'file':
        sampleDict['content'] = {'fileName': fileName, 'fileUrl': url}

    if buttons:
        sampleDict['content']['buttons'] = [buttons]

    sjson = json.dumps(sampleDict)
    response = requests.post(f"https://chat-go.jwzhd.com/open-apis/v1/bot/send?token={yh_token}", headers=headers, data=sjson)
    reply = response.json()
    print (reply)

def edit(msgId, recvId, recvType, contentType, content='content', fileName='fileName', url='url', buttons=None):
    headers = {'Content-Type': 'application/json'}
    sampleDict = {
        "msgId": msgId,
        "recvId": recvId,
        "recvType": recvType,
        "contentType": contentType,
        "content": {}
    }

    if contentType == 'text':
        sampleDict['content']['text'] = content
    elif contentType == 'image':
        sampleDict['content']['imageUrl'] = url
    elif contentType == 'file':
        sampleDict['content'] = {'fileName': fileName, 'fileUrl': url}

    if buttons:
        sampleDict['content']['buttons'] = [buttons]

    sjson = json.dumps(sampleDict)
    response = requests.post(f"https://chat-go.jwzhd.com/open-apis/v1/bot/edit?token={yh_token}", headers=headers, data=sjson)
    reply = response.json()
