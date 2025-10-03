import os
from datetime import timedelta

# ✅ 环境配置类型（development, testing, production）
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# ✅ JWT配置
SECRET_KEY = os.getenv("SECRET_KEY", "_change_this_in_production_with_a_secure_key_")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))

# ✅ 数据库配置（MySQL）
# 优先从DATABASE_URL环境变量获取完整连接字符串
DATABASE_URL = os.getenv("DATABASE_URL")

# 如果没有提供完整连接字符串，则使用单独的数据库配置项
if not DATABASE_URL:
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "Xiaoqianlang%40123.com")
    DB_HOST = os.getenv("DB_HOST", "192.168.13.200")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "netmgr")
    DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# ✅ Redis配置（用于Celery任务队列）
REDIS_URL = os.getenv("REDIS_URL", "redis://192.168.13.200:6379/0")

# ✅ Token过期时间
ACCESS_TOKEN_EXPIRE = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

# ✅ 日志配置
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ✅ 交换机连接配置
DEFAULT_TIMEOUT = int(os.getenv("DEFAULT_TIMEOUT", "30"))  # 默认连接超时时间（秒）
MAX_CONNECT_ATTEMPTS = int(os.getenv("MAX_CONNECT_ATTEMPTS", "3"))  # 最大连接尝试次数

# ✅ 调试模式
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
