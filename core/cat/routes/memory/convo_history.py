
from pydantic import BaseModel
from typing import Dict, Optional
from fastapi import Request, APIRouter, Depends, Form

from cat.auth.connection import HTTPAuth
from cat.auth.permissions import AuthPermission, AuthResource
from cat.looking_glass.stray_cat import StrayCat

from cat.convo.messages import MessageWhy

router = APIRouter()

class HistoryMessage(BaseModel):
    who:str
    message:str
    why: Dict = {}
    


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


# POST conversation history from working memory
@router.post("/conversation_history")
async def post_conversation_history(
    request: Request,
    historyMessage: HistoryMessage,
    stray: StrayCat = Depends(HTTPAuth(AuthResource.MEMORY, AuthPermission.WRITE)),
) -> Dict:
    """Insert a conversation history into working memory"""

    stray.working_memory.update_conversation_history(historyMessage.who,historyMessage.message,why=historyMessage.why)
    return {"history": stray.working_memory.history}

