from app.services.db import get_db
from app.services.models import Device

# 获取数据库会话
db = next(get_db())

# 查询所有设备
devices = db.query(Device).all()

print("数据库中的设备数据:")
for device in devices:
    print(f"ID: {device.id}")
    print(f"名称: {device.name}")
    print(f"管理IP: {device.management_ip}")
    print(f"厂商: {device.vendor}")
    print(f"设备类型: {device.device_type}")
    print(f"状态: {device.status}")
    print(f"位置: {device.location}")
    print("---")