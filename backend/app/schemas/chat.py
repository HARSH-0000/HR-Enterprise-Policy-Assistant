from typing import Optional, List
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: str
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    query: str = Field(
        min_length=1,
        max_length=4000
    )
    chat_history: Optional[List[Message]] = None


class Source(BaseModel):
    title: str
    policy_id: str
    page: int = 0
    department: str = "Human Resources"
    status: str = "pending_review"
    section: Optional[str] = None
    version: Optional[str] = None
    effective_date: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    sources: List[Source] = Field(
        default_factory=list
    )
    grounded: Optional[bool] = True
    status: Optional[str] = "answered"
