import requests
import json
from config import(weather_api_url, weather_api_token)
def get_weather(location):
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