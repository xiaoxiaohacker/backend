import sys
import io
import requests

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def simple_test():
    """简单测试仪表板API端点"""
    endpoints = [
        "http://localhost:8000/api/dashboard/stats",
        "http://localhost:8000/api/dashboard/performance",
        "http://localhost:8000/api/dashboard/warnings",
        "http://localhost:8000/api/dashboard/device-status"
    ]
    
    print("开始测试仪表板API端点...\n")
    
    for url in endpoints:
        print(f"测试: {url}")
        try:
            response = requests.get(url)
            print(f"状态码: {response.status_code}")
            print(f"内容类型: {response.headers.get('Content-Type')}")
            
            # 尝试直接打印响应内容（前200个字符）
            print(f"响应内容(前200字符): {response.text[:200]}...")
        except Exception as e:
            print(f"请求失败: {str(e)}")
        print("=" * 60)

if __name__ == "__main__":
    simple_test()