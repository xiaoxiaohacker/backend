import sqlite3
from datetime import datetime

# 连接到数据库
conn = sqlite3.connect('netmgr.db')
cursor = conn.cursor()

# 查询所有设备
cursor.execute('SELECT id, name, management_ip, vendor, model, device_type FROM devices')
devices = cursor.fetchall()

print("=== 模拟SNMP数据采集 ===\n")

# 为每台设备模拟SNMP数据采集和接口状态
for device in devices:
    device_id, name, ip, vendor, model, device_type = device
    print(f"设备: {name} (IP: {ip}, 厂商: {vendor}, 型号: {model})")
    print("--- 设备信息 ---")
    
    # 模拟SNMP获取设备信息
    if vendor.lower() == 'huawei':
        os_version = "V200R003C00"
        serial_number = "HW" + str(device_id).zfill(8)
        uptime = "45 days, 12:30:45"
    elif vendor.lower() == 'ruijie':
        os_version = "RGOS 10.4(3b23p2)"
        serial_number = "RJ" + str(device_id).zfill(8)
        uptime = "30 days, 08:15:30"
    else:
        os_version = "Unknown"
        serial_number = "N/A"
        uptime = "Unknown"
    
    # 更新设备表中的操作系统版本和序列号
    cursor.execute('''
    UPDATE devices 
    SET os_version = ?, serial_number = ?, updated_at = ? 
    WHERE id = ?
    ''', (os_version, serial_number, datetime.now().isoformat(), device_id))
    
    print(f"  操作系统版本: {os_version}")
    print(f"  序列号: {serial_number}")
    print(f"  运行时间: {uptime}")
    
    # 模拟SNMP获取接口状态
    print("--- 接口状态 ---")
    
    # 根据设备类型和厂商生成模拟接口
    if device_type.lower() == 'switch':
        if vendor.lower() == 'huawei':
            interfaces = [
                ('GigabitEthernet0/0/1', 'up', 'up', '00:E0:FC:12:34:56', '192.168.1.1/24', '1000Mbps'),
                ('GigabitEthernet0/0/2', 'up', 'up', '00:E0:FC:12:34:57', '192.168.1.2/24', '1000Mbps'),
                ('GigabitEthernet0/0/3', 'down', 'down', '00:E0:FC:12:34:58', None, '1000Mbps'),
            ]
        else:  # ruijie
            interfaces = [
                ('GigabitEthernet1/0/1', 'up', 'up', '00:11:22:33:44:55', '192.168.1.1/24', '1000Mbps'),
                ('GigabitEthernet1/0/2', 'up', 'up', '00:11:22:33:44:56', '192.168.1.2/24', '1000Mbps'),
                ('GigabitEthernet1/0/3', 'up', 'down', '00:11:22:33:44:57', None, '1000Mbps'),
            ]
        
        # 清除旧的接口状态数据
        cursor.execute('DELETE FROM interface_status WHERE device_id = ?', (device_id,))
        
        # 插入新的接口状态数据
        for interface in interfaces:
            interface_name, admin_status, oper_status, mac, ip_addr, speed = interface
            cursor.execute('''
            INSERT INTO interface_status (
                device_id, interface_name, admin_status, operational_status,
                mac_address, ip_address, speed, last_seen
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                device_id,
                interface_name,
                admin_status,
                oper_status,
                mac,
                ip_addr,
                speed,
                datetime.now().isoformat()
            ))
            
            print(f"  接口: {interface_name}")
            print(f"    管理状态: {admin_status}")
            print(f"    操作状态: {oper_status}")
            print(f"    MAC地址: {mac}")
            print(f"    IP地址: {ip_addr if ip_addr else 'N/A'}")
            print(f"    速率: {speed}")
    
    print()

# 提交更改
conn.commit()

# 验证数据插入
cursor.execute('SELECT COUNT(*) FROM interface_status')
interface_count = cursor.fetchone()[0]
print(f"已成功为 {len(devices)} 台设备生成模拟接口状态数据，共 {interface_count} 条记录")

# 关闭连接
conn.close()
print("\n数据采集完成，数据库连接已关闭")
print("注意：这是模拟的SNMP数据采集，实际使用时需要配置正确的SNMP参数并确保设备可访问")