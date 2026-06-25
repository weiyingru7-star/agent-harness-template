from fastapi import APIRouter, HTTPException, status

from app.models.run import ToolCall
from app.services.run_store import run_store


router = APIRouter(prefix="/api/tool-calls", tags=["tool-calls"])


@router.get("/{tool_call_id}", response_model=ToolCall)
def get_tool_call(tool_call_id: str) -> ToolCall:
    tool_call = run_store.get_tool_call(tool_call_id)
    if tool_call is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tool call not found")
    return tool_call
