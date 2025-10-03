from fastapi import APIRouter

router = APIRouter()

@router.get("/new-dashboard/stats")
def get_new_dashboard_stats():
    """New, completely independent dashboard stats endpoint"""
    return {
        "success": True,
        "message": "This is a test from the new dashboard module",
        "data": {
            "active_devices": 42,
            "total_traffic": "1.2 TB"
        }
    }