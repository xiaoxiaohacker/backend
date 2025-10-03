from app.services.db import engine
from sqlalchemy import text
from app.services.models import Device

# 连接到数据库并添加所有缺失的列
def add_missing_columns():
    try:
        with engine.connect() as conn:
            # 获取Device模型中的所有字段名
            model_columns = [column.name for column in Device.__table__.columns]
            
            # 获取数据库表中的所有字段名
            result = conn.execute(text('DESCRIBE devices'))
            db_columns = [row[0] for row in result.fetchall()]
            
            # 找出缺失的字段
            missing_columns = [col for col in model_columns if col not in db_columns]
            
            if not missing_columns:
                print('✅ 数据库表结构已完整，没有缺失的列')
                return
            
            print(f'发现 {len(missing_columns)} 个缺失的列: {missing_columns}')
            
            # 为每个缺失的列添加到表中
            for column in missing_columns:
                column_obj = Device.__table__.columns[column]
                column_type = str(column_obj.type)
                
                # 简单处理列类型，实际可能需要更复杂的映射
                if 'VARCHAR' in column_type:
                    # 提取长度信息
                    length = column_type.split('(')[1].split(')')[0]
                    sql = f'ALTER TABLE devices ADD COLUMN {column} VARCHAR({length}) NULL'
                elif 'INTEGER' in column_type:
                    sql = f'ALTER TABLE devices ADD COLUMN {column} INT NULL'
                elif 'DATETIME' in column_type:
                    sql = f'ALTER TABLE devices ADD COLUMN {column} DATETIME NULL'
                else:
                    # 默认使用VARCHAR类型
                    sql = f'ALTER TABLE devices ADD COLUMN {column} VARCHAR(255) NULL'
                
                print(f'添加列: {column} ({column_type})')
                conn.execute(text(sql))
                
            conn.commit()
            print('✅ 所有缺失的列已成功添加')
            
    except Exception as e:
        print(f'❌ 执行失败: {str(e)}')

if __name__ == '__main__':
    print('开始检查并修复数据库表结构...')
    add_missing_columns()