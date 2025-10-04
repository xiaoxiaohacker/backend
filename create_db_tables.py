import sqlite3
import datetime

# 连接到SQLite数据库
conn = sqlite3.connect('netmgr.db')
cursor = conn.cursor()

# 创建devices表
try:
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS devices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        management_ip TEXT NOT NULL UNIQUE,
        vendor TEXT NOT NULL,
        model TEXT,
        os_version TEXT,
        serial_number TEXT,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        enable_password TEXT,
        port INTEGER DEFAULT 22,
        device_type TEXT,
        location TEXT,
        status TEXT DEFAULT 'unknown',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    print('devices表创建成功')
except sqlite3.Error as e:
    print(f'创建devices表失败: {e}')

# 创建interface_status表
try:
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS interface_status (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL,
        interface_name TEXT NOT NULL,
        admin_status TEXT,
        operational_status TEXT,
        mac_address TEXT,
        ip_address TEXT,
        speed TEXT,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES devices (id)
    )
    ''')
    print('interface_status表创建成功')
except sqlite3.Error as e:
    print(f'创建interface_status表失败: {e}')

# 创建configs表
try:
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS configs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        file_size INTEGER NOT NULL,
        hash TEXT NOT NULL,
        taken_by TEXT,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES devices (id)
    )
    ''')
    print('configs表创建成功')
except sqlite3.Error as e:
    print(f'创建configs表失败: {e}')

# 创建command_logs表
try:
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS command_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        device_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        command TEXT NOT NULL,
        output TEXT,
        success INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (device_id) REFERENCES devices (id),
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    print('command_logs表创建成功')
except sqlite3.Error as e:
    print(f'创建command_logs表失败: {e}')

# 创建users表
try:
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL UNIQUE,
        hashed_password TEXT NOT NULL,
        email TEXT,
        is_active INTEGER DEFAULT 1
    )
    ''')
    print('users表创建成功')
except sqlite3.Error as e:
    print(f'创建users表失败: {e}')

# 提交更改
conn.commit()

# 关闭连接
conn.close()
print('数据库表结构创建完成，连接已关闭')