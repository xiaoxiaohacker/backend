import requests
import json

# API基础URL
BASE_URL = "http://127.0.0.1:8000/api/v1"

# 登录信息
USERNAME = "admin"
PASSWORD = "520131xiao"  # 用户提到的密码

print("测试登录功能...")

# 构建登录请求
def test_login():
    url = f"{BASE_URL}/auth/login"
    
    # 准备登录数据
    login_data = {
        "username": USERNAME,
        "password": PASSWORD
    }
    
    try:
        # 发送登录请求
        print(f"发送登录请求，用户名: {USERNAME}")
        response = requests.post(url, data=login_data)
        
        # 打印响应状态码和内容
        print(f"响应状态码: {response.status_code}")
        print(f"响应内容: {response.text}")
        
        if response.status_code == 200:
            # 登录成功，尝试使用令牌访问需要认证的接口
            token = response.json().get("access_token")
            print(f"登录成功！获取的令牌: {token[:20]}...")
            
            # 测试访问me接口
            test_me_endpoint(token)
        else:
            print("登录失败！")
            
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")

# 测试me接口
def test_me_endpoint(token):
    url = f"{BASE_URL}/auth/me"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    try:
        print("测试访问me接口...")
        response = requests.get(url, headers=headers)
        
        print(f"me接口响应状态码: {response.status_code}")
        print(f"me接口响应内容: {response.text}")
        
        if response.status_code == 200:
            print("me接口访问成功！认证功能正常工作。")
        else:
            print("me接口访问失败！")
            
    except Exception as e:
        print(f"访问me接口过程中发生错误: {str(e)}")

if __name__ == "__main__":
    test_login()