from sqlalchemy.orm import Session
from app.services.db import engine, get_db
from app.services.models import Device, InterfaceStatus
from datetime import datetime
import random

# 模拟设备数据
def generate_mock_devices():
    """生成模拟设备数据并插入到数据库中"""
    # 厂商列表
    vendors = ["huawei", "h3c", "ruijie", "cisco"]
    
    # 设备类型列表
    device_types = ["switch", "router", "firewall", "access_point"]
    
    # 设备型号列表
    models = {
        "huawei": ["S5700", "S6720", "AR2200", "USG6000"],
        "h3c": ["S5560", "S6520", "MSR3600", "F1000"],
        "ruijie": ["RG-S5750", "RG-S6510", "RG-AR1200", "RG-WALL"],
        "cisco": ["Catalyst 2960", "Catalyst 3850", "ISR 4321", "ASA 5506"]
    }
    
    # 设备位置列表
    locations = ["Main Building", "Data Center", "Branch Office", "Warehouse", "Remote Site"]
    
    # 设备状态列表
    statuses = ["online", "online", "online", "online", "offline", "unknown"]
    
    devices = []
    
    # 生成25台模拟设备
    for i in range(1, 26):
        vendor = random.choice(vendors)
        device_type = random.choice(device_types)
        
        # 根据厂商选择型号
        model = random.choice(models[vendor])
        
        # 生成管理IP
        ip_octet = i // 256 if i >= 256 else i
        ip = f"192.168.{ip_octet}.{i % 256 + 1}"
        
        # 生成序列号
        serial = f"SN{vendor.upper()}{random.randint(100000, 999999)}"
        
        device = Device(
            name=f"Device-{i}",
            management_ip=ip,
            vendor=vendor,
            model=model,
            os_version=f"V{random.randint(10, 99)}.{random.randint(0, 9)}.{random.randint(0, 99)}",
            serial_number=serial,
            username="admin",
            password="admin123",
            enable_password="enable123" if random.random() > 0.3 else None,
            port=22,
            device_type=device_type,
            location=random.choice(locations),
            status=random.choice(statuses),
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        devices.append(device)
    
    return devices

# 为设备生成接口数据
def generate_mock_interfaces(devices):
    """为设备生成模拟接口数据"""
    interfaces = []
    
    for device in devices:
        # 每个设备生成8-24个接口
        num_interfaces = random.randint(8, 24)
        
        for i in range(1, num_interfaces + 1):
            # 根据设备类型决定接口类型
            if device.device_type == "switch":
                interface_name = f"GigabitEthernet1/0/{i}"
            elif device.device_type == "router":
                interface_name = f"GigabitEthernet0/{i}"
            elif device.device_type == "firewall":
                interface_name = f"Ethernet0/{i}"
            else:  # access_point
                if i == 1:
                    interface_name = "GigabitEthernet0"
                else:
                    interface_name = f"Radio{i-1}"
            
            # 接口状态，在线设备的接口大部分是up的
            if device.status == "online":
                operational_status = "up" if random.random() > 0.2 else "down"
            else:
                operational_status = "down"
            
            # 管理状态
            admin_status = "up" if random.random() > 0.1 else "down"
            
            # 生成MAC地址
            mac = "".join([f"{random.randint(0, 255):02x}" for _ in range(6)])
            mac = ":".join([mac[i:i+2] for i in range(0, 12, 2)])
            
            # 生成IP地址（部分接口有IP）
            ip = None
            if device.device_type in ["router", "firewall"] and random.random() > 0.5:
                ip_octet1 = random.randint(1, 223)
                ip_octet2 = random.randint(0, 255)
                ip_octet3 = random.randint(0, 255)
                ip = f"{ip_octet1}.{ip_octet2}.{ip_octet3}.{i % 256 + 1}/24"
            
            # 接口速度
            speed = "1Gbps" if random.random() > 0.1 else "100Mbps"
            
            interface = InterfaceStatus(
                device_id=device.id,
                interface_name=interface_name,
                admin_status=admin_status,
                operational_status=operational_status,
                mac_address=mac,
                ip_address=ip,
                speed=speed,
                last_seen=datetime.now()
            )
            
            interfaces.append(interface)
    
    return interfaces

# 主函数，将模拟数据插入到数据库
def populate_mock_data():
    """将模拟数据插入到数据库中"""
    # 获取数据库会话
    db = next(get_db())
    
    try:
        # 检查是否已有设备数据
        existing_devices = db.query(Device).first()
        
        if existing_devices:
            print("数据库中已存在设备数据，跳过生成模拟数据。")
            return
        
        print("开始生成模拟设备数据...")
        
        # 生成模拟设备数据
        devices = generate_mock_devices()
        
        # 添加设备到数据库
        db.add_all(devices)
        db.commit()
        
        print(f"成功添加 {len(devices)} 台模拟设备。")
        
        # 生成并添加接口数据
        print("开始生成模拟接口数据...")
        interfaces = generate_mock_interfaces(devices)
        
        # 添加接口到数据库
        db.add_all(interfaces)
        db.commit()
        
        print(f"成功添加 {len(interfaces)} 个模拟接口。")
        
    except Exception as e:
        print(f"生成模拟数据时出错: {str(e)}")
        db.rollback()
    finally:
        db.close()

# 如果直接运行此脚本，则执行数据填充if __name__ == "__main__":
    populate_mock_data()