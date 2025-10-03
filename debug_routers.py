import inspect
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.test_root import router as test_root_router
from app.main import app

print("=== Dashboard Router Properties ===")
print(f"Type: {type(dashboard_router)}")
print(f"Module: {dashboard_router.__module__}")
print(f"Has routes attribute: {hasattr(dashboard_router, 'routes')}")
if hasattr(dashboard_router, 'routes'):
    print(f"Routes length: {len(dashboard_router.routes)}")
    print(f"Routes type: {type(dashboard_router.routes)}")
    for route in dashboard_router.routes:
        print(f"- Path: {route.path}, Name: {route.name}")

print("\n=== Test Root Router Properties ===")
print(f"Type: {type(test_root_router)}")
print(f"Module: {test_root_router.__module__}")
print(f"Has routes attribute: {hasattr(test_root_router, 'routes')}")
if hasattr(test_root_router, 'routes'):
    print(f"Routes length: {len(test_root_router.routes)}")
    print(f"Routes type: {type(test_root_router.routes)}")
    for route in test_root_router.routes:
        print(f"- Path: {route.path}, Name: {route.name}")

print("\n=== Main App Includes ===")
for route in app.routes:
    if hasattr(route, 'path') and ("dashboard" in route.path or "test-root" in route.path or "ping" in route.path):
        print(f"Path: {route.path}, Name: {route.name}, Type: {type(route)}")