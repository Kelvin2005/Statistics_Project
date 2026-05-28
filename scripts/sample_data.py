import requests
import json

# Function to get access token using username and password
def get_access_token(username, password, token_url):
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }
    data = {
          'username': username,
          'password': password,
          'grant_type': "password",
          'client_id': "acled",
          'scope': "authenticated"
    }

    response = requests.post(token_url, headers=headers, data=data)

    if response.status_code == 200:
        token_data = response.json()
        return token_data['access_token']
    else:
        raise Exception(f"Failed to get access token: {response.status_code} {response.text}")


# Get an access token
my_token = get_access_token(
    username="24421020@buaa.edu.cn",
    password="Kelvin2005",
    token_url="https://acleddata.com/oauth/token",
)


# 测试 1: 最简单的查询 - 只查一个国家，最近几条
print("\n=== 测试 1: 简单查询 (Yemen, limit=5) ===")
base_url = "https://acleddata.com/api/acled/read?_format=json&country=Yemen&limit=5"
response = requests.get(
    base_url,
    headers={"Authorization": f"Bearer {my_token}", "Content-Type": "application/json"},
    timeout=60,
)
print("Status:", response.status_code)
print("Text preview:", response.text[:300] if response.text else "(empty)")
if response.status_code == 200:
    try:
        data = response.json()
        print("JSON status:", data.get("status"))
        print("Count:", data.get("count"))
        print("Data records:", len(data.get("data", [])))
    except:
        print("Not JSON:", response.text[:200])

# 测试 2: 带日期范围的查询
print("\n=== 测试 2: 带日期范围 (Yemen, 2024-01-01|2024-01-31, limit=10) ===")
base_url2 = "https://acleddata.com/api/acled/read?_format=json&country=Yemen&event_date=2024-01-01|2024-01-31&event_date_where=BETWEEN&limit=10"
response2 = requests.get(
    base_url2,
    headers={"Authorization": f"Bearer {my_token}", "Content-Type": "application/json"},
    timeout=60,
)
print("Status:", response2.status_code)
if response2.status_code == 200:
    try:
        data2 = response2.json()
        print("JSON status:", data2.get("status"))
        print("Count:", data2.get("count"))
        print("Data records:", len(data2.get("data", [])))
        if data2.get("data"):
            print("First record:", data2["data"][0].get("event_id_cnty"), data2["data"][0].get("event_date"))
    except Exception as e:
        print("Error parsing JSON:", e)
else:
    print("Text:", response2.text[:300])

# 测试 3: 原脚本的多国查询（可能超时）
print("\n=== 测试 3: 原脚本查询 (Georgia/Armenia, 2021) ===")
base_url3 = "https://acleddata.com/api/acled/read?_format=json&country=Georgia:OR:country=Armenia&year=2021&fields=event_id_cnty|event_date|event_type|country|fatalities&limit=5"
response3 = requests.get(
    base_url3,
    headers={"Authorization": f"Bearer {my_token}", "Content-Type": "application/json"},
    timeout=30,
)
print("Status:", response3.status_code)
if response3.status_code == 200:
    try:
        data3 = response3.json()
        print("JSON status:", data3.get("status"))
        print("Count:", data3.get("count"))
    except:
        print("Not valid JSON")
else:
    print("Failed:", response3.text[:200])