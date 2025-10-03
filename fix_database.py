from app.services.db import engine
from sqlalchemy import text

# 连接到数据库并添加缺失的name列
try:
    with engine.connect() as conn:
        conn.execute(text('ALTER TABLE devices ADD COLUMN name VARCHAR(100) NULL AFTER id'))
        conn.commit()
        print('✅ 已成功在devices表中添加name列')
except Exception as e:
    print(f'❌ 执行失败: {str(e)}')