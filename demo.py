import asyncio
import json
from gitpulse_mcp.main import _dispatch

async def run_demo():
    print("Testing get_repo_health for tiangolo/fastapi...")
    try:
        result = await _dispatch("get_repo_health", {"owner": "tiangolo", "repo": "fastapi"})
        print(json.dumps(result, indent=2))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(run_demo())
