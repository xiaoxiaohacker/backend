import logging
import requests
import json
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 测试check_connectivity API
def test_check_connectivity():
    api_url = "http://localhost:8000/api/v1/devices/check-connectivity"
    
    # 测试多个IP地址
    test_ips = [
        "127.0.0.1",      # 本地主机，应该总是可达
        "192.168.121.51",  # 用户提到的交换机IP
        "192.168.1.1"      # 常见的路由器IP，可能可达也可能不可达
    ]
    
    for ip in test_ips:
        try:
            # 发送GET请求到API
            logger.info(f"\n测试check_connectivity API，URL: {api_url}?ip={ip}")
            start_time = time.time()
            response = requests.get(f"{api_url}?ip={ip}")
            end_time = time.time()
            
            # 检查响应状态码
            if response.status_code == 200:
                # 解析响应内容
                result = response.json()
                logger.info(f"API响应状态码: {response.status_code}")
                logger.info(f"API响应时间: {(end_time - start_time) * 1000:.2f} ms")
                logger.info(f"API响应结果: {json.dumps(result, indent=2)}")
                
                if result['is_reachable']:
                    logger.info(f"✓ 成功: API返回 {ip} 是可达的")
                else:
                    logger.warning(f"✗ 失败: API返回 {ip} 是不可达的")
            else:
                logger.error(f"API请求失败，状态码: {response.status_code}, 响应内容: {response.text}")
        except Exception as e:
            logger.error(f"测试API出错: {str(e)}")
        
        # 等待一段时间再测试下一个IP
        time.sleep(1)

if __name__ == "__main__":
    test_check_connectivity()