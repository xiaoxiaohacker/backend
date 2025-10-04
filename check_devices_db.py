import sqlite3

# 连接到数据库
try:
    conn = sqlite3.connect('netmgr.db')
    cursor = conn.cursor()
    
    # 查询设备表结构
    print('设备表结构:')
    cursor.execute('PRAGMA table_info(devices)')
    columns = cursor.fetchall()
    for column in columns:
        print(f'ID: {column[0]}, 名称: {column[1]}, 类型: {column[2]}, 非空: {column[3]}, 默认值: {column[4]}, 主键: {column[5]}')
    
    # 查询设备数据
    print('\n设备数据:')
    cursor.execute('SELECT id, name, management_ip, vendor, model, status, device_type FROM devices')
    devices = cursor.fetchall()
    
    if not devices:
        print('数据库中没有设备数据。')
    else:
        print(f'共找到 {len(devices)} 台设备:')
        for device in devices:
            print(f'ID: {device[0]}, 名称: {device[1]}, IP: {device[2]}, 厂商: {device[3]}, 型号: {device[4]}, 状态: {device[5]}, 设备类型: {device[6]}')
    
    # 查询接口状态表，了解设备纳管后的监控数据
    print('\n接口状态表结构:')
    try:
        cursor.execute('PRAGMA table_info(interface_status)')
        interface_columns = cursor.fetchall()
        for column in interface_columns:
            print(f'ID: {column[0]}, 名称: {column[1]}, 类型: {column[2]}')
        
        # 检查是否有接口状态数据
        cursor.execute('SELECT COUNT(*) FROM interface_status')
        interface_count = cursor.fetchone()[0]
        print(f'\n接口状态表中有 {interface_count} 条记录')
        
        if interface_count > 0:
            # 查询前5条接口状态数据
            cursor.execute('SELECT device_id, interface_name, status, in_octets, out_octets FROM interface_status LIMIT 5')
            print('前5条接口状态数据:')
            for row in cursor.fetchall():
                print(f'设备ID: {row[0]}, 接口: {row[1]}, 状态: {row[2]}, 入流量: {row[3]}, 出流量: {row[4]}')
    except sqlite3.OperationalError:
        print('接口状态表不存在')
    
except sqlite3.Error as e:
    print(f'数据库错误: {e}')
finally:
    if conn:
        conn.close()
        print('\n数据库连接已关闭')