"""
ReadMe Backend - FastAPI Local Server
Main entry point for the local API server
"""
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Create FastAPI app
app = FastAPI(
    title="ReadMe Local API",
    description="Local API server for document parsing, TTS, and library management",
    version="0.1.0"
)

# Configure CORS for localhost only
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "http://127.0.0.1:*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "ReadMe Local API",
        "version": "0.1.0"
    }

@app.get("/api/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "not_implemented",
        "parsers": "not_implemented"
    }

if __name__ == "__main__":
    # Run the server on localhost only for security
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=5000,
        reload=True,
        log_level="info"
    )
