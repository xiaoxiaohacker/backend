import sqlite3
import json
from datetime import datetime

# 设备数据
devices_data = [
    {
        "name": "TuanWei-A",
        "management_ip": "192.168.121.51",
        "vendor": "ruijie",
        "model": "S2928G-E",
        "os_version": "",
        "serial_number": "",
        "username": "admin",
        "port": 23,
        "device_type": "switch",
        "location": "团委、学工部",
        "status": "online",
        "id": 3,
        "created_at": "2025-09-30T21:55:59",
        "updated_at": "2025-10-03T22:05:33"
    },
    {
        "name": "TuanWei-B",
        "management_ip": "192.168.121.50",
        "vendor": "ruijie",
        "model": "S2928G-E",
        "os_version": "",
        "serial_number": "",
        "username": "admin",
        "port": 23,
        "device_type": "switch",
        "location": "团委、学工部",
        "status": "online",
        "id": 4,
        "created_at": "2025-09-30T22:36:58",
        "updated_at": "2025-10-03T22:04:09"
    },
    {
        "name": "23GongYu",
        "management_ip": "192.168.121.152",
        "vendor": "huawei",
        "model": "S5700 ",
        "os_version": "",
        "serial_number": "",
        "username": "admin",
        "port": 23,
        "device_type": "switch",
        "location": "23公寓负一楼弱电间",
        "status": "online",
        "id": 5,
        "created_at": "2025-09-30T22:38:58",
        "updated_at": "2025-10-01T17:27:30"
    }
]

# 连接到SQLite数据库
conn = sqlite3.connect('netmgr.db')
cursor = conn.cursor()

# 插入设备数据
success_count = 0
failed_count = 0

for device in devices_data:
    try:
        # 将空字符串转换为None，使数据库使用NULL
        for key, value in device.items():
            if value == "":
                device[key] = None
        
        # 准备SQL语句
        cursor.execute('''
        INSERT OR REPLACE INTO devices (
            id, name, management_ip, vendor, model, os_version, serial_number,
            username, password, enable_password, port, device_type, location, status,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            device['id'],
            device['name'],
            device['management_ip'],
            device['vendor'],
            device['model'],
            device['os_version'],
            device['serial_number'],
            device['username'],
            "default_password",  # 使用默认密码，实际使用时应该修改
            None,  # enable_password
            device['port'],
            device['device_type'],
            device['location'],
            device['status'],
            device['created_at'],
            device['updated_at']
        ))
        
        print(f"设备 '{device['name']}' (ID: {device['id']}) 导入成功")
        success_count += 1
        
    except sqlite3.Error as e:
        print(f"设备 '{device['name']}' (ID: {device['id']}) 导入失败: {e}")
        failed_count += 1

# 提交更改
conn.commit()

# 关闭连接
conn.close()

print(f"\n导入完成！成功: {success_count}, 失败: {failed_count}")
print("注意：默认密码为'default_password'，请在系统中及时修改")