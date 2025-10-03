import sys
import io
from app.services.db import get_db
from app.services.models import Device
from datetime import datetime

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def import_device_data():
    """导入用户截图中显示的设备数据"""
    db = next(get_db())
    
    try:
        # 检查是否已有设备数据
        existing_devices = db.query(Device).first()
        
        if existing_devices:
            print("警告：数据库中已存在设备数据。")
            response = input("是否要删除现有数据并导入新数据？(y/n): ")
            if response.lower() != 'y':
                print("取消导入操作。")
                return
            
            # 删除现有设备数据
            db.query(Device).delete()
            db.commit()
            print("已删除现有设备数据。")
        
        # 创建用户截图中显示的设备数据
        devices = [
            Device(
                name="核心交换机",
                management_ip="192.168.1.1",
                vendor="华为",
                model="S5700",
                username="admin",
                password="admin123",
                port=22,
                device_type="交换机",
                location="数据中心",
                status="online",
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            Device(
                name="路由器1",
                management_ip="192.168.1.2",
                vendor="思科",
                model="ISR 4321",
                username="admin",
                password="admin123",
                port=22,
                device_type="路由器",
                location="数据中心",
                status="online",
                created_at=datetime.now(),
                updated_at=datetime.now()
            ),
            Device(
                name="接入交换机1",
                management_ip="192.168.1.3",
                vendor="华为",
                model="S2700",
                username="admin",
                password="admin123",
                port=22,
                device_type="交换机",
                location="办公区",
                status="离线",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        ]
        
        # 添加设备到数据库
        db.add_all(devices)
        db.commit()
        
        print(f"成功导入 {len(devices)} 台设备数据。")
        for device in devices:
            print(f"- {device.name} ({device.management_ip}) - {device.vendor} - {device.status}")
            
    except Exception as e:
        print(f"导入设备数据时出错: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import_device_data()