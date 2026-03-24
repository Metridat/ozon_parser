import requests

url = "https://www.ozon.ru/api/entrypoint-api.bx/page/json/v2"

params = {
    "url": "/search/?text=нож туристический&page=1"
}

headers = {
    "user-agent": "Mozilla/5.0",
    "accept": "application/json",
}

response = requests.get(url, params=params, headers=headers)

print(response.status_code)
print(response.json())