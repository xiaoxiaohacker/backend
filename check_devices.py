from app.services.db import SessionLocal
from app.services.models import Device

# 获取数据库会话
db = SessionLocal()

try:
    # 查询所有设备
    devices = db.query(Device).all()
    
    if not devices:
        print("数据库中没有设备记录")
    else:
        print("数据库中的设备信息:")
        print("="*80)
        print(f"{'ID':<5}|{'名称':<20}|{'IP地址':<20}|{'厂商':<10}|{'端口':<5}")
        print("="*80)
        
        for device in devices:
            print(f"{device.id:<5}|{device.name[:18]:<20}|{device.management_ip:<20}|{device.vendor:<10}|{device.port:<5}")
    
except Exception as e:
    print(f"查询数据库时出错: {str(e)}")
finally:
    # 关闭数据库连接
    db.close()
    print("数据库连接已关闭")