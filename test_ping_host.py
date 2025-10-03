import logging
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入ping_host函数
from app.api.v1.devices import ping_host

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 测试ping_host函数
def test_ping_host():
    # 测试本地主机
    ip = "127.0.0.1"
    try:
        logger.info(f"测试ping_host函数，IP: {ip}")
        result = ping_host(ip)
        logger.info(f"ping_host函数结果: {result}")
        
        if result['is_reachable']:
            logger.info(f"✓ 成功: {ip} 是可达的")
        else:
            logger.warning(f"✗ 失败: {ip} 是不可达的")
    except Exception as e:
        logger.error(f"调用ping_host函数出错: {str(e)}")

if __name__ == "__main__":
    test_ping_host()