from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(
    title="Distributed Rate Limiter",
    description="High-performance rate limiting service with priority-based scheduling",
    version="1.0.0"
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "distributed-rate-limiter"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
