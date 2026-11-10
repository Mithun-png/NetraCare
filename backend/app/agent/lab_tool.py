"""CityCare Lab MCP Partner Client Tool (Iteration 6 R3).
Connects to CityCare Hospital Lab's MCP server over Streamable HTTP (http://localhost:8002/mcp).
Provides graceful offline fallback when the lab server is unreachable.
"""
import os
import json
import asyncio
from typing import Dict, Any, Optional
from langchain_core.tools import tool

CITYCARE_LAB_MCP_URL = os.getenv("CITYCARE_LAB_MCP_URL", "http://localhost:8002/mcp")
OFFLINE_LAB_MESSAGE = "I can't check CityCare Lab just now. Please ask Staff at the front desk."

async def _fetch_lab_test_info_async(test: str = "") -> Dict[str, Any]:
    from langchain_mcp_adapters.client import MultiServerMCPClient
    client = MultiServerMCPClient({
        "citycare_lab": {
            "transport": "streamable_http",
            "url": CITYCARE_LAB_MCP_URL,
        }
    })
    try:
        tools = await client.get_tools()
        lab_tool = next((t for t in tools if t.name == "get_lab_test_info"), None)
        if not lab_tool:
            return {"found": False, "offline": True, "message": OFFLINE_LAB_MESSAGE}
        
        raw_res = await lab_tool.ainvoke({"test": test})
        # Parse MCP text content
        if isinstance(raw_res, list) and len(raw_res) > 0 and isinstance(raw_res[0], dict) and "text" in raw_res[0]:
            try:
                return json.loads(raw_res[0]["text"])
            except Exception:
                return {"found": True, "raw": raw_res[0]["text"]}
        elif isinstance(raw_res, dict):
            return raw_res
        elif isinstance(raw_res, str):
            try:
                return json.loads(raw_res)
            except Exception:
                return {"found": True, "raw": raw_res}
        return {"found": True, "data": str(raw_res)}
    except Exception as e:
        return {"found": False, "offline": True, "message": OFFLINE_LAB_MESSAGE, "error": str(e)}

@tool
def get_lab_test_info(test: str = "") -> Dict[str, Any]:
    """Information about a blood or urine test at CityCare Hospital Lab, NetraCare's partner lab.
    Returns fasting rules, sample type, when the report is ready, timings, and indicative price.
    Information only: it cannot book tests, read/interpret test results, or prescribe tests.
    
    Args:
        test: The test name in plain words (e.g. 'HbA1c', 'fasting sugar', 'CBC').
              Leave empty to get general lab details (timings, home collection) and the list of offered tests.
    """
    try:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            # If running inside an existing event loop, create task or run in thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                return pool.submit(lambda: asyncio.run(_fetch_lab_test_info_async(test))).result(timeout=10)
        else:
            return asyncio.run(_fetch_lab_test_info_async(test))
    except Exception as e:
        return {"found": False, "offline": True, "message": OFFLINE_LAB_MESSAGE, "error": str(e)}

