import requests
import time

session = requests.Session()

headers = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
}

session.get("https://www.ozon.ru/", headers=headers)

time.sleep(2)

url = "https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2"

params = {
    "url": "/search/?text=нож туристический&page=1"
}

headers.update({
    "accept": "application/json",
    "referer": "https://www.ozon.ru/",
    "x-o3-app-name": "dweb_client",
})

response = session.get(url, params=params, headers=headers)

print(response.status_code)
print(response.text[:500])