import requests
from config import yh_token
from logs import logger
async def image(image_path, image_filename):
    """
    上传图片到云湖，指定文件名为原始文件名并添加.png后缀

    :param image_path: 图片文件的路径
    :param image_filename: 图片文件的原始文件名
    :param yh_token: 云湖的访问令牌
    :return: 返回一个元组，包含上传后的图片key和类型（"image"），如果上传失败则返回 (None, None)
    """
    upload_url = f"https://chat-go.jwzhd.com/open-apis/v1/image/upload?token={yh_token}"
    
    with open(image_path, "rb") as image_file:
        files = {'image': (image_filename, image_file)}
        response = requests.post(upload_url, files=files)
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data['msg'] == "success":
                image_key = response_data['data']['imageKey']
                return image_key, "image"
            else:
                logger.debug(f"上传图片失败: {response_data['msg']}")
                return None, None
        else:
            logger.info(f"上传图片失败: {response.status_code}")
            return None, None