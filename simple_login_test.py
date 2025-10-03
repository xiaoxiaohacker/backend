import requests
import json

# 使用127.0.0.1作为主机
url = "http://127.0.0.1:8000/api/v1/auth/login"

# 登录数据 - 以表单数据格式发送
data = {
    "username": "admin",
    "password": "520131xiao"
}

print(f"尝试连接: {url}")

try:
    # 发送POST请求，使用data参数而不是json参数，这符合auth.py中的Form数据格式要求
    response = requests.post(url, data=data)
    
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.text}")
    
    if response.status_code == 200:
        print("登录成功！")
        # 尝试解析JSON响应
        try:
            result = response.json()
            print(f"访问令牌: {result.get('access_token', '未获取到令牌')}")
        except:
            print("无法解析JSON响应")
    else:
        print(f"登录失败，状态码: {response.status_code}")
        
except Exception as e:
    print(f"错误: {str(e)}")