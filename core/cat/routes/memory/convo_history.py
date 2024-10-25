
import time
from pydantic import BaseModel
from typing import Dict, Optional
from fastapi import Request, APIRouter, Depends, Form, HTTPException

from cat.auth.connection import HTTPAuth
from cat.auth.permissions import AuthPermission, AuthResource
from cat.looking_glass.stray_cat import StrayCat
from cat.convo.messages import Role

router = APIRouter()

class HistoryMessage(BaseModel):
    who:str
    message:str
    why: Dict
    


# DELETE conversation history from working memory
@router.delete("/conversation_history")
async def wipe_conversation_history(
    request: Request,
    stray: StrayCat = Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.DELETE)),
) -> Dict:
    """Delete the specified user's conversation history from working memory"""

    stray.working_memory.history = []

    return {
        "deleted": True,
    }


# GET conversation history from working memory
@router.get("/conversation_history")
async def get_conversation_history(
    request: Request,
    stray: StrayCat = Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.READ)),
) -> Dict:
    """Get the specified user's conversation history from working memory"""

    return {"history": stray.working_memory.history}


# PUT conversation history from working memory
@router.put("/conversation_history/{conversation_history_index}")
async def put_conversation_history(
    request: Request,
    conversation_history_index: int,
    historyMessage: HistoryMessage,
    stray: StrayCat = Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.WRITE)),
) -> Dict:
    """Edit a conversation history in working memory in a specified index"""

    history = stray.working_memory.history 
    if conversation_history_index < 0 or conversation_history_index >= len(history):
        raise HTTPException(
            status_code=400, detail={"error": f"Invalid conversation history index. Please use a valid index >= 0 AND < {len(stray.working_memory)}."}
        )

    prev_history_message = history[conversation_history_index]   

    history[conversation_history_index] = {
        "who": historyMessage.who,
        "message": historyMessage.message,
        "why": historyMessage.why,
        "when": prev_history_message["when"],
        "role": prev_history_message["role"]
    }

    return history[conversation_history_index]

