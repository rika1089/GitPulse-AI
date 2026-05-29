from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from gitpulse_mcp.main import _dispatch

app = FastAPI()

# Simple health check
@app.get("/")
async def root():
    return {"status": "ok"}

# Allow all origins for development (adjust for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)




class ToolRequest(BaseModel):
    name: str
    arguments: dict

@app.post("/tool")
async def call_tool(request: ToolRequest):
    try:
        result = await _dispatch(request.name, request.arguments)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@app.options("/tool")
async def tool_options():
    return {}
@app.get("/health")
async def health_check():
    return {"status": "healthy"}
