from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from app.services.db import Base, engine
from app.api.v1 import auth_router, devices_router, backup_tasks_router, dashboard_router, test_root_router, device_stats_router, alerts_router
from app.new_dashboard import router as new_dashboard_router
import os
import json
from typing import Any
from fastapi.responses import JSONResponse

# 自定义JSONResponse，确保UTF-8编码
class UTF8JSONResponse(JSONResponse):
    media_type = "application/json; charset=utf-8"

    def render(self, content: Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")

# ✅ 自动创建数据库表
Base.metadata.create_all(bind=engine)

# 检查并填充模拟数据（如果数据库为空）
from app.services.mock_data import populate_mock_data
try:
    populate_mock_data()
except Exception as e:
    print(f"填充模拟数据时出错: {str(e)}")

# 创建静态文件目录
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
os.makedirs(static_dir, exist_ok=True)

# 配置FastAPI应用，禁用默认文档路由，并设置默认响应类为UTF8JSONResponse
app = FastAPI(
    title="NetMgr API", 
    docs_url=None, 
    redoc_url=None,
    default_response_class=UTF8JSONResponse
)

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory=static_dir), name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(devices_router, prefix="/api/v1/devices", tags=["Devices"])
app.include_router(backup_tasks_router, prefix="/api/v1/backup-tasks", tags=["Backup Tasks"])    
app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(test_root_router, tags=["Test"])
app.include_router(new_dashboard_router, tags=["New Dashboard"])
app.include_router(device_stats_router, prefix="/api/v1/device-stats", tags=["Device Statistics"])
app.include_router(alerts_router, prefix="/api/v1/alerts", tags=["Alerts"])

# Simple ping endpoint
@app.get("/ping")
def ping():
    return {"ping": "pong"}

# 使用FastAPI内置的Swagger UI，不依赖外部CDN
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title=app.title + " - Swagger UI",
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url="/openapi.json",
        title=app.title + " - ReDoc",
    )

@app.get("/openapi.json", include_in_schema=False)
async def openapi():
    return get_openapi(title=app.title, version="0.1.0", routes=app.routes)

@app.get("/ping")
def ping():
    return {"msg": "pong"}
