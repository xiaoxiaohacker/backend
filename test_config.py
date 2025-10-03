from app.adapters.huawei import HuaweiAdapter

# 手动设置设备信息进行测试
device_info = {
    'management_ip': '192.168.1.1',  # 替换为实际设备IP
    'vendor': 'huawei',
    'username': 'admin',  # 替换为实际用户名
    'password': 'admin@123',  # 替换为实际密码
    'port': 22
}

# 创建适配器并获取配置
adapter = HuaweiAdapter(device_info)
try:
    print(f"正在连接设备: {device_info['management_ip']}")
    adapter.connect()
    
    print("尝试获取设备配置...")
    config = adapter.get_config()
    
    if config:
        print(f"成功获取配置，长度: {len(config)} 字符")
        print("\n配置前100个字符:\n")
        print(config[:100])
    else:
        print("获取配置失败，返回为空")
except Exception as e:
    print(f"获取配置时发生错误: {str(e)}")
finally:
    adapter.disconnect()