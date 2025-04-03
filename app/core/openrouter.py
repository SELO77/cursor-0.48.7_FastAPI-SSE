import aiohttp
import os
import logging
import json
import asyncio
from typing import AsyncGenerator
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


async def generate_response_stream(
    character_personality: str, messages: list
) -> AsyncGenerator[str, None]:
    if not OPENROUTER_API_KEY:
        raise Exception("OpenRouter API key not found")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "HTTP-Referer": "http://localhost:8080",
        "X-Title": "AI Character Chat",
        "Content-Type": "application/json",
    }

    system_message = f"You are an AI character with the following personality: {character_personality}. Respond accordingly."

    payload = {
        "model": "anthropic/claude-3-opus-20240229",
        "messages": [{"role": "system", "content": system_message}, *messages],
        "stream": True,
    }

    logger.info(f"Sending streaming request to OpenRouter with payload: {payload}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OPENROUTER_URL, json=payload, headers=headers
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error(
                        f"OpenRouter API error: Status {response.status}, Response: {error_text}"
                    )
                    raise Exception(f"OpenRouter API error: {error_text}")

                # Process the stream
                async for line in response.content:
                    if line:
                        try:
                            line = line.decode("utf-8").strip()
                            if line.startswith("data: ") and line != "data: [DONE]":
                                json_str = line[6:]  # Remove 'data: ' prefix
                                data = json.loads(json_str)
                                if (
                                    content := data.get("choices", [{}])[0]
                                    .get("delta", {})
                                    .get("content")
                                ):
                                    yield content
                        except json.JSONDecodeError as e:
                            logger.error(f"Error parsing JSON: {e}")
                            continue
                        except Exception as e:
                            logger.error(f"Error processing stream: {e}")
                            continue

    except aiohttp.ClientError as e:
        logger.error(f"Network error: {str(e)}")
        raise Exception(f"Network error: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise
