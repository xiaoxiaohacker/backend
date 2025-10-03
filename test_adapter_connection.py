from app.services.adapter_manager import AdapterManager
from app.services.models import Device
from sqlalchemy.orm import Session
from app.services.db import get_db
import time


def test_device_connections():
    """测试所有设备的连接"""
    try:
        # 获取数据库会话
        db = next(get_db())
        
        # 查询所有设备
        devices = db.query(Device).all()
        
        if not devices:
            print("数据库中没有设备信息")
            return
        
        print(f"找到 {len(devices)} 台设备，开始测试连接...\n")
        
        # 遍历测试每台设备
        for device in devices:
            print(f"=== 测试设备: {device.name} ===")
            print(f"IP: {device.management_ip}")
            print(f"端口: {device.port}")
            print(f"厂商: {device.vendor}")
            # 从端口推断协议
            protocol = 'ssh' if device.port == 22 else 'telnet'
            print(f"协议: {protocol}\n")
            
            try:
                # 获取设备适配器
                adapter = AdapterManager.get_adapter(device.to_dict())
                
                # 测试连接
                start_time = time.time()
                connected = adapter.connect()
                end_time = time.time()
                
                if connected:
                    print(f"✅ 连接成功! 耗时: {end_time - start_time:.2f} 秒")
                    # 获取一些基本信息验证连接
                    try:
                        device_info = adapter.get_device_info()
                        print(f"设备信息: {device_info.get('hostname', 'N/A')}")
                    except Exception as e:
                        print(f"获取设备信息时出错: {str(e)}")
                    # 断开连接
                    adapter.disconnect()
                else:
                    print("❌ 连接失败: 未知原因")
                    
            except Exception as e:
                print(f"❌ 连接失败: {str(e)}")
                
            print("=" * 50)
            print()
            
    except Exception as e:
        print(f"测试过程中发生错误: {str(e)}")
    finally:
        # 关闭数据库会话
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    test_device_connections()