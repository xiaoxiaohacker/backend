from app.services.db import get_db
from app.services.models import Device


def update_device_ports(new_port=23):
    """更新所有设备的端口设置"""
    try:
        # 获取数据库会话
        db = next(get_db())
        
        # 查询所有设备
        devices = db.query(Device).all()
        
        if not devices:
            print("数据库中没有设备信息")
            return
        
        print(f"找到 {len(devices)} 台设备，准备将端口更新为 {new_port}")
        
        # 更新每台设备的端口
        updated_count = 0
        for device in devices:
            old_port = device.port
            if old_port != new_port:
                print(f"更新设备 '{device.name}' ({device.management_ip}) 的端口: {old_port} -> {new_port}")
                device.port = new_port
                updated_count += 1
            else:
                print(f"设备 '{device.name}' ({device.management_ip}) 的端口已经是 {new_port}，无需更新")
        
        # 提交更改
        db.commit()
        print(f"成功更新了 {updated_count} 台设备的端口设置")
        
    except Exception as e:
        print(f"更新过程中发生错误: {str(e)}")
        # 发生错误时回滚
        if 'db' in locals():
            db.rollback()
    finally:
        # 关闭数据库会话
        if 'db' in locals():
            db.close()


if __name__ == "__main__":
    # 将所有设备的端口更新为23
    update_device_ports(23)