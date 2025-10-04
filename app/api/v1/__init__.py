# 导出各个模块的router
from .dashboard import router as dashboard_router
from .devices import router as devices_router
from .auth import router as auth_router
from .backup_tasks import router as backup_tasks_router
from .test_root import router as test_root_router
from .device_stats import router as device_stats_router
from .alerts import router as alerts_router

__all__ = [
    "dashboard_router",
    "devices_router",
    "auth_router",
    "backup_tasks_router",
    "test_root_router",
    "device_stats_router",
    "alerts_router"
]