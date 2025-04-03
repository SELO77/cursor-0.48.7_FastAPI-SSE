from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from typing import List
import logging
import json

from app.models.models import Character, ChatMessage
from app.schemas.schemas import (
    CharacterCreate,
    CharacterResponse,
    MessageCreate,
    MessageResponse,
)
from app.core.openrouter import generate_response_stream

router = APIRouter()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@router.post("/characters/", response_model=CharacterResponse)
async def create_character(character: CharacterCreate):
    char = await Character.create(**character.model_dump())
    return char


@router.get("/characters/", response_model=List[CharacterResponse])
async def list_characters(user_id: str):
    return await Character.filter(user_id=user_id)


@router.get("/characters/{char_id}", response_model=CharacterResponse)
async def get_character(char_id: int):
    return await Character.get(id=char_id)


@router.post("/characters/{char_id}/chat")
async def chat_with_character(char_id: int, message: MessageCreate):
    try:
        character = await Character.get(id=char_id)
        if not character:
            raise HTTPException(status_code=404, detail="Character not found")

        # Save user message
        user_message = await ChatMessage.create(
            character=character, content=message.content, is_user=True
        )

        # Get recent chat history
        recent_messages = (
            await ChatMessage.filter(character=character)
            .order_by("-created_at")
            .limit(10)
        )
        chat_history = [
            {"role": "user" if msg.is_user else "assistant", "content": msg.content}
            for msg in reversed(recent_messages)
        ]

        logger.info(f"Generating streaming response for character {char_id}")

        # Initialize response content
        full_response = ""

        async def response_stream():
            nonlocal full_response
            try:
                async for content in generate_response_stream(
                    character.personality, chat_history
                ):
                    full_response += content
                    yield f"data: {json.dumps({'content': content})}\n\n"

                # Save the complete response after streaming
                await ChatMessage.create(
                    character=character, content=full_response, is_user=False
                )

                # Send [DONE] message
                yield "data: [DONE]\n\n"

            except Exception as e:
                logger.error(f"Error in stream: {str(e)}")
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(response_stream(), media_type="text/event-stream")

    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/characters/{char_id}/messages", response_model=List[MessageResponse])
async def get_chat_history(char_id: int):
    character = await Character.get(id=char_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")

    messages = await ChatMessage.filter(character=character).order_by("created_at")
    return messages
