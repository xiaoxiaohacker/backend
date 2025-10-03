import pymysql

print("开始执行更新configs表结构的操作...")

# 数据库连接信息
DB_USER = "root"
DB_PASSWORD = "Xiaoqianlang%40123.com"
DB_HOST = "192.168.13.200"
DB_PORT = 3306
DB_NAME = "netmgr"

# 替换密码中的URL编码
DB_PASSWORD = DB_PASSWORD.replace("%40", "@")
print(f"尝试连接到数据库: {DB_HOST}:{DB_PORT} 数据库名: {DB_NAME}")

try:
    # 连接到数据库
    print("正在建立数据库连接...")
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset='utf8mb4'
    )
    print("数据库连接成功！")
    
    # 创建游标
    cursor = conn.cursor()
    
    # 检查configs表结构并添加缺失的列
    
    # 检查filename列
    print("检查configs表是否存在filename列...")
    cursor.execute("SHOW COLUMNS FROM configs LIKE 'filename'")
    result = cursor.fetchone()
    
    if result is None:
        print("configs表中不存在filename列，准备添加...")
        cursor.execute("ALTER TABLE configs ADD COLUMN filename VARCHAR(255) NOT NULL")
        conn.commit()
        print("成功为configs表添加filename列！")
    else:
        print("configs表中已存在filename列，无需添加。")
    
    # 检查file_size列
    print("检查configs表是否存在file_size列...")
    cursor.execute("SHOW COLUMNS FROM configs LIKE 'file_size'")
    result = cursor.fetchone()
    
    if result is None:
        print("configs表中不存在file_size列，准备添加...")
        cursor.execute("ALTER TABLE configs ADD COLUMN file_size INT NOT NULL")
        conn.commit()
        print("成功为configs表添加file_size列！")
    else:
        print("configs表中已存在file_size列，无需添加。")
    
    # 检查hash列
    print("检查configs表是否存在hash列...")
    cursor.execute("SHOW COLUMNS FROM configs LIKE 'hash'")
    result = cursor.fetchone()
    
    if result is None:
        print("configs表中不存在hash列，准备添加...")
        cursor.execute("ALTER TABLE configs ADD COLUMN hash VARCHAR(64) NOT NULL")
        conn.commit()
        print("成功为configs表添加hash列！")
    else:
        print("configs表中已存在hash列，无需添加。")
    
    # 关闭连接
    cursor.close()
    conn.close()
    print("数据库连接已关闭。")
    
except Exception as e:
    print(f"更新configs表结构失败: {str(e)}")
    import traceback
    traceback.print_exc()

print("操作完成。")