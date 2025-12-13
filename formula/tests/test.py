# test_post.py
import requests
import json

# 发送POST请求
response = requests.post(
    'http://127.0.0.1:5000/api/v1/formula/convert',
    json={'text': 'x = (-b ± sqrt(b^2 - 4ac)) / (2a)'}
)

print(f"状态码: {response.status_code}")
print(f"响应: {response.text}")