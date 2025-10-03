import sys
import io
from app.services.db import get_db
from app.services.models import Device
from sqlalchemy.orm import Session

# 设置标准输出为UTF-8编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_database_encoding():
    """检查数据库中的数据编码"""
    db = next(get_db())
    
    try:
        # 查询所有设备
        devices = db.query(Device).all()
        
        print("数据库中的设备数据（使用UTF-8编码输出）:")
        for device in devices:
            print(f"ID: {device.id}")
            print(f"名称: {device.name}")
            print(f"管理IP: {device.management_ip}")
            print(f"厂商: {device.vendor}")
            print(f"设备类型: {device.device_type}")
            print(f"状态: {device.status}")
            print(f"位置: {device.location}")
            print("---")
    except Exception as e:
        print(f"查询数据库时出错: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    check_database_encoding()