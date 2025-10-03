import pymysql

print("开始执行添加description列的操作...")

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
    
    # 检查configs表是否存在description列
    print("检查configs表是否存在description列...")
    cursor.execute("SHOW COLUMNS FROM configs LIKE 'description'")
    result = cursor.fetchone()
    
    if result is None:
        print("configs表中不存在description列，准备添加...")
        # 添加description列
        cursor.execute("ALTER TABLE configs ADD COLUMN description VARCHAR(255) NULL")
        conn.commit()
        print("成功为configs表添加description列！")
    else:
        print("configs表中已存在description列，无需添加。")
    
    # 关闭连接
    cursor.close()
    conn.close()
    print("数据库连接已关闭。")
    
except Exception as e:
    print(f"添加description列失败: {str(e)}")
    import traceback
    traceback.print_exc()

print("操作完成。")