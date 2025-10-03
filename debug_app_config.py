from app.main import app
import uvicorn

print("=== FastAPI Application Configuration ===")
print(f"Version: {app.version}")
print(f"Debug: {app.debug}")

print("\n=== Middleware ===")
for middleware in app.user_middleware:
    print(f"- {middleware.cls.__name__}")

print("\n=== Routes with Details ===")
for route in app.routes:
    if hasattr(route, 'path') and ("dashboard" in route.path or "test-root" in route.path or "ping" in route.path):
        print(f"Path: {route.path}")
        print(f"  Name: {route.name}")
        print(f"  Type: {type(route)}")
        if hasattr(route, 'dependencies'):
            print(f"  Dependencies: {[dep.call.__name__ if hasattr(dep.call, '__name__') else str(dep) for dep in route.dependencies]}")
        print()

print("=== CORS Settings ===")
if hasattr(app, 'middleware_stack'):
    print(f"Middleware stack exists: {hasattr(app, 'middleware_stack')}")

print("\n=== Trying to access routes programmatically ===")
# This is a very simplified version of how FastAPI routes requests
try:
    # Try to find the route that would handle /api/dashboard/stats
    dashboard_stats_route = None
    for route in app.routes:
        if hasattr(route, 'path') and route.path == "/api/dashboard/stats":
            dashboard_stats_route = route
            break
    
    if dashboard_stats_route:
        print(f"Found route for /api/dashboard/stats: {dashboard_stats_route.name}")
    else:
        print("Could not find route for /api/dashboard/stats")
        
    # Try to find the route that would handle /ping
    ping_route = None
    for route in app.routes:
        if hasattr(route, 'path') and route.path == "/ping":
            ping_route = route
            break
    
    if ping_route:
        print(f"Found route for /ping: {ping_route.name}")
    else:
        print("Could not find route for /ping")
except Exception as e:
    print(f"Error during route lookup: {e}")