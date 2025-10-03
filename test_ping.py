import logging
import subprocess
import platform
import re

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 测试ping功能
def test_ping():
    # 测试本地主机
    ip = "127.0.0.1"
    param = '-n 1' if platform.system().lower() == 'windows' else '-c 1'
    
    try:
        # 执行ping命令 - 在Windows上，参数需要特殊处理
        if platform.system().lower() == 'windows':
            # 在Windows上，整个命令作为一个字符串传递
            command = f'ping {param} {ip}'
            logger.info(f"执行ping命令: {command}")
            result = subprocess.run(
                command,  # 整个命令作为一个字符串
                shell=True,  # 使用shell执行
                capture_output=True,
                text=True,
                timeout=2
            )
        else:
            # 在Linux/macOS上，参数拆分成列表项
            command_parts = ['ping', param, ip]
            logger.info(f"执行ping命令: {' '.join(command_parts)}")
            result = subprocess.run(
                command_parts,
                capture_output=True,
                text=True,
                timeout=2
            )
        
        # 打印完整输出和返回码
        logger.info(f"返回码: {result.returncode}")
        logger.info(f"标准输出:\n{result.stdout}")
        logger.info(f"标准错误:\n{result.stderr}")
        
        # 检查连通性
        is_reachable = False
        if platform.system().lower() == 'windows':
            # 检查输出中是否包含"来自"和"的回复"
            logger.info(f"'来自' 在输出中: {'来自' in result.stdout}")
            logger.info(f"'的回复' 在输出中: {'的回复' in result.stdout}")
            is_reachable = "来自" in result.stdout and "的回复" in result.stdout
        else:
            is_reachable = result.returncode == 0
        
        logger.info(f"连通性检测结果: {is_reachable}")
        
        # 提取响应时间
        response_time = None
        if is_reachable:
            if platform.system().lower() == 'windows':
                match = re.search(r'时间[<|=](\d+)ms', result.stdout)
                logger.info(f"响应时间匹配结果: {match}")
                if match:
                    response_time = int(match.group(1))
            else:
                match = re.search(r'time=(\d+)\s+ms', result.stdout)
                if match:
                    response_time = int(match.group(1))
        
        logger.info(f"最终结果: {{'ip': '{ip}', 'is_reachable': {is_reachable}, 'response_time': {response_time}}}")
        
    except Exception as e:
        logger.error(f"Ping {ip} 出错: {str(e)}")

if __name__ == "__main__":
    test_ping()