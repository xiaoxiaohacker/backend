import time
import subprocess
import platform
import time
from app.adapters.huawei import HuaweiAdapter
from app.adapters.ruijie import RuijieAdapter


def ping_host(ip: str) -> dict:
    """执行ping命令检测设备连通性"""
    # 根据操作系统选择ping命令参数
    param = '-n 1' if platform.system().lower() == 'windows' else '-c 1'
    
    try:
        # 执行ping命令
        if platform.system().lower() == 'windows':
            command = f'ping {param} {ip}'
            result = subprocess.run(
                command,  # 整个命令作为一个字符串
                shell=True,  # 使用shell执行
                capture_output=True,
                text=True,
                timeout=2
            )
        else:
            command_parts = ['ping', param, ip]
            result = subprocess.run(
                command_parts,
                capture_output=True,
                text=True,
                timeout=2
            )
        
        # 检查ping是否成功
        is_reachable = False
        if platform.system().lower() == 'windows':
            is_reachable = "来自" in result.stdout and "的回复" in result.stdout
        else:
            is_reachable = result.returncode == 0
        
        return {
            "ip": ip,
            "is_reachable": is_reachable,
            "output": result.stdout
        }
    except Exception as e:
        return {
            "ip": ip,
            "is_reachable": False,
            "output": str(e)
        }

def test_device_connection(device_info, adapter_class):
    """
    测试设备连接并获取配置和接口信息
    
    Args:
        device_info: 设备信息字典
        adapter_class: 适配器类
    """
    print(f"\n{'='*60}")
    print(f"测试连接: {device_info['vendor']} - {device_info['management_ip']}")
    print(f"{'='*60}")
    
    # 首先ping设备检查连通性
    ping_result = ping_host(device_info['management_ip'])
    print(f"设备连通性测试: {'可达' if ping_result['is_reachable'] else '不可达'}")
    if not ping_result['is_reachable']:
        print(f"Ping输出: {ping_result['output']}")
        print("设备不可达，跳过后续连接测试。")
        return False
    
    try:
        # 创建适配器实例
        adapter = adapter_class(device_info)
        
        # 连接设备
        print("正在连接设备...")
        start_time = time.time()
        adapter.connect()
        connection_time = time.time() - start_time
        print(f"连接成功，耗时: {connection_time:.2f}秒")
        
        # 获取设备基本信息
        print("\n获取设备基本信息...")
        device_info_data = adapter.get_device_info()
        print(f"设备型号: {device_info_data.get('model')}")
        print(f"软件版本: {device_info_data.get('version')}")
        
        # 获取配置信息
        print("\n获取设备配置...")
        config = adapter.get_config()
        print(f"配置长度: {len(config)} 字符")
        print("配置前100个字符:")
        print(config[:100] + "...")
        
        # 获取所有接口信息
        print("\n获取所有接口信息...")
        interfaces = adapter.get_interfaces()
        print(f"接口数量: {len(interfaces)}")
        if interfaces:
            print("前3个接口:")
            for interface in interfaces[:3]:
                print(f"  - {interface['name']}: 状态={interface['status']}")
        
        # 获取第一个接口的详细状态（如果有接口）
        if interfaces:
            first_interface = interfaces[0]['name']
            print(f"\n获取接口 {first_interface} 详细状态...")
            interface_status = adapter.get_interface_status(first_interface)
            print(f"  描述: {interface_status.get('description', '无')}")
            print(f"  操作状态: {interface_status.get('oper_status', '无')}")
        
        # 断开连接
        adapter.disconnect()
        print("\n已断开连接")
        return True
        
    except ConnectionError as e:
        print(f"连接错误: {str(e)}")
        return False
    except Exception as e:
        print(f"操作失败: {str(e)}")
        try:
            adapter.disconnect()
        except:
            pass
        return False


if __name__ == "__main__":
    # 华为设备信息 - 默认使用telnet协议
    huawei_device = {
        'management_ip': '192.168.121.152',
        'vendor': 'huawei',
        'username': 'admin',  # 请替换为实际用户名
        'password': 'wlzx@2014',  # 请替换为实际密码
        'port': 23
        # 不指定protocol，将默认使用telnet
    }
    
    # 锐捷设备信息 - 默认使用telnet协议
    ruijie_device = {
        'management_ip': '192.168.121.50',
        'vendor': 'ruijie',
        'username': 'admin',  # 请替换为实际用户名
        'password': 'wlzx@2014',  # 请替换为实际密码
        'port': 23
        # 不指定protocol，将默认使用telnet
    }
    
    # 测试华为设备
    print("开始测试设备连接...")
    
    # 测试华为设备
    test_device_connection(huawei_device, HuaweiAdapter)
    
    # 测试锐捷设备
    test_device_connection(ruijie_device, RuijieAdapter)
    
    print("\n所有设备测试完成")