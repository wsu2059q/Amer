import requests
from typing import List, Dict, Any
import time

class Setu:
    def __init__(self, pid: int, p: int, uid: int, title: str, author: str, r18: bool, width: int, height: int,
                 tags: List[str], ext: str, ai_type: int, upload_date: int, urls: Dict[str, str]):
        self.pid = pid
        self.p = p
        self.uid = uid
        self.title = title
        self.author = author
        self.r18 = r18
        self.width = width
        self.height = height
        self.tags = tags
        self.ext = ext
        self.ai_type = ai_type
        self.upload_date = upload_date
        self.urls = urls

    def __repr__(self):
        return f"Setu(pid={self.pid}, title='{self.title}', author='{self.author}')"

    def to_details(self):
        return (f"标题: {self.title}\n"
                f"PID: {self.pid}\n"
                f"作者: {self.author}")

class SetuResponse:
    def __init__(self, error: str, data: List[Setu]):
        self.error = error
        self.data = data

    def __repr__(self):
        return f"SetuResponse(error='{self.error}', data={self.data})"

class LoliconClient:
    BASE_URL = "https://api.lolicon.app/setu/v2"

    def __init__(self, timeout=20, max_retries=3, retry_delay=1):
        self.session = requests.Session()
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.seen_urls = set()  # 记录已请求过的图片URL

    def check_url_validity(self, url: str) -> bool:
        try:
            response = self.session.head(url, timeout=self.timeout)
            response.raise_for_status()
            return True
        except requests.RequestException:
            return False

    def get_setu(self, r18: int = 0, num: int = 1, uid: List[int] = None, keyword: str = None,
                 tag: List[str] = None, author: str = None, pid: int = None, size: List[str] = ["original"],
                 proxy: str = "i.pixiv.re", date_after: int = None, date_before: int = None, dsc: bool = False,
                 exclude_ai: bool = False, aspect_ratio: str = None) -> SetuResponse:
        params = {
            "r18": r18,
            "num": num,
            "uid": uid,
            "keyword": keyword,
            "tag": tag,
            "author": author,
            "pid": pid,
            "size": size,
            "proxy": proxy,
            "dateAfter": date_after,
            "dateBefore": date_before,
            "dsc": dsc,
            "excludeAI": exclude_ai,
            "aspectRatio": aspect_ratio
        }

        for attempt in range(self.max_retries + 1):
            try:
                response = self.session.get(self.BASE_URL, params=params, timeout=self.timeout)
                response.raise_for_status()
                response_data = response.json()
            except requests.RequestException as e:
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                return SetuResponse(error=str(e), data=[])

            if 'error' in response_data and response_data['error']:
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                    continue
                return SetuResponse(error=response_data['error'], data=[])

            setu_list = []
            new_urls = set()
            for item in response_data.get('data', []):
                urls = {s: item['urls'].get(s, '') for s in size}
                if all(self.check_url_validity(url) for url in urls.values()):
                    setu = Setu(
                        pid=item['pid'],
                        p=item['p'],
                        uid=item['uid'],
                        title=item['title'],
                        author=item['author'],
                        r18=item['r18'],
                        width=item['width'],
                        height=item['height'],
                        tags=item['tags'],
                        ext=item['ext'],
                        ai_type=item['aiType'],
                        upload_date=item['uploadDate'],
                        urls=urls
                    )
                    setu_list.append(setu)
                    new_urls.update(urls.values())

            # 检查是否有重复的URL
            if new_urls & self.seen_urls:
                return SetuResponse(error="没有相关色图", data=[])

            # 更新已请求过的图片URL
            self.seen_urls.update(new_urls)

            if setu_list:
                return SetuResponse(error='', data=setu_list)

            # 如果没有有效URL且未达到最大重试次数，则继续重试
            if attempt < self.max_retries:
                time.sleep(self.retry_delay)

        return SetuResponse(error="没有相关色图", data=[])

def get_setu(r18: int = 0, num: int = 1, uid: List[int] = None, keyword: str = None,
             tag: List[str] = None, author: str = None, pid: int = None, size: List[str] = ["original"],
             proxy: str = "i.pixiv.re", date_after: int = None, date_before: int = None, dsc: bool = False,
             exclude_ai: bool = False, aspect_ratio: str = None) -> SetuResponse:
    client = LoliconClient()
    return client.get_setu(r18, num, uid, keyword, tag, author, pid, size, proxy, date_after, date_before, dsc, exclude_ai, aspect_ratio)