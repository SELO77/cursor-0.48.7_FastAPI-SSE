from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class CharacterCreate(BaseModel):
    name: str
    description: str
    personality: str
    user_id: str


class CharacterResponse(BaseModel):
    id: int
    name: str
    description: str
    personality: str
    created_at: datetime
    user_id: str


class MessageCreate(BaseModel):
    content: str


class MessageResponse(BaseModel):
    id: int
    content: str
    is_user: bool
    created_at: datetime
