import logging
import os
import uvicorn
from api.routes import router
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("asr-got-mcp")

# Initialize FastAPI app
app = FastAPI(
    title="ASR-GoT MCP Server",
    description="Model Context Protocol server implementing Advanced Scientific Reasoning Graph-of-Thoughts",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

@app.get("/")
async def root():
    return {"message": "ASR-GoT MCP Server is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    port = int(os.getenv("MCP_SERVER_PORT", 8082))
    logger.info(f"Starting ASR-GoT MCP Server on port {port}")
    uvicorn.run("server:app", host="0.0.0.0", port=port)
