import uvicorn
from app.main import app

if __name__ == "__main__":
    # 打印所有注册的路由
    print("Registered routes:")
    for route in app.routes:
        print(f"{route.path} - {route.name}")