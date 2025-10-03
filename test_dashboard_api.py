import sys
import io
import json
import requests

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_dashboard_api():
    """测试仪表板API的所有端点"""
    base_url = "http://localhost:8000/api/dashboard"
    
    # 测试的端点列表
    endpoints = [
        "/stats",
        "/performance",
        "/warnings",
        "/device-status"
    ]
    
    print("开始测试仪表板API端点...\n")
    
    for endpoint in endpoints:
        url = base_url + endpoint
        print(f"测试端点: {url}")
        
        try:
            # 发送GET请求
            response = requests.get(url)
            
            # 检查响应状态码
            if response.status_code == 200:
                print(f"✅ 响应状态码: {response.status_code}")
                
                # 检查响应头中的编码
                content_type = response.headers.get('Content-Type', '')
                print(f"响应内容类型: {content_type}")
                
                # 尝试解析JSON响应
                try:
                    data = response.json()
                    print(f"返回数据类型: {type(data).__name__}")
                    
                    # 打印部分数据（不打印全部以避免输出过多）
                    print("返回数据摘要:")
                    if isinstance(data, dict):
                        for key, value in list(data.items())[:5]:  # 只显示前5个键值对
                            if isinstance(value, (dict, list)):
                                print(f"  {key}: {type(value).__name__}({len(value)})个元素")
                            else:
                                print(f"  {key}: {value}")
                    elif isinstance(data, list):
                        print(f"  列表包含 {len(data)} 个元素")
                        if data and isinstance(data[0], dict):
                            print(f"  第一个元素的键: {', '.join(data[0].keys())}")
                except json.JSONDecodeError:
                    print("❌ 无法解析JSON响应")
                    print(f"响应内容: {response.text[:100]}...")
            else:
                print(f"❌ 响应状态码: {response.status_code}")
                print(f"错误信息: {response.text}")
            
        except Exception as e:
            print(f"❌ 请求失败: {str(e)}")
        
        print("-" * 50)