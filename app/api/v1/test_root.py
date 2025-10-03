from fastapi import APIRouter

router = APIRouter()

@router.get("/test-root")
def test_root_endpoint():
    """Test endpoint at the root level to verify API connectivity"""
    return {"message": "Test root endpoint is working!"}