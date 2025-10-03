from fastapi import FastAPI, APIRouter

# Create a router
router = APIRouter()

# Add endpoints to the router
@router.get("/test-router")
def test_router_endpoint():
    return {"message": "Router endpoint is working!"}

# Create the FastAPI app
app = FastAPI()

# Include the router
app.include_router(router)

# Add a direct endpoint
@app.get("/test-direct")
def test_direct_endpoint():
    return {"message": "Direct endpoint is working!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)