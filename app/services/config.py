import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql://root:Xiaoqianlang%40123.com@192.168.13.200:3306/netmgr?charset=utf8mb4"
)
JWT_SECRET = os.getenv("JWT_SECRET", "change_me")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24
CELERY_BROKER = os.getenv("CELERY_BROKER", "redis://192.168.13.200:6379/0")
CELERY_BACKEND = os.getenv("CELERY_BACKEND", "redis://192.168.13.200:6379/0")
