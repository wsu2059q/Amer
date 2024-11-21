import requests
from bs4 import BeautifulSoup
from config import weather_api_url, weather_api_token

# 定义函数
def get_weather(location):
    """
    获取指定城市的天气信息。
    
    :param location: 城市名称或城市ID
    :return: 天气信息字符串
    """
    complete_url = f"{weather_api_url}?key={weather_api_token}&q={location}&lang=zh"
    response = requests.get(complete_url)
    data = response.json()
    if "error" not in data:
        current = data["current"]
        temperature = current["temp_c"]
        condition = current["condition"]["text"]
        return f"在 {location} 的天气是 {condition}，温度为 {temperature}°C。"
    else:
        return f"无法找到 {location} 的天气信息。"

def web_search(query: str) -> str:
    """
    在网络上搜索指定的问题。
    
    :param query: 搜索查询
    :return: 搜索结果
    """
    # 这里可以调用实际的搜索引擎API
    return f"Search results for '{query}': Some relevant information."

def web_crawler(url: str) -> str:
    """
    爬取指定网页的内容。
    
    :param url: 网页URL
    :return: 网页内容摘要
    """
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        # 提取页面的主要内容
        main_content = soup.get_text().strip()
        return f"Crawled content from {url}: {main_content[:100]}..."
    except Exception as e:
        return f"Error crawling {url}: {str(e)}"