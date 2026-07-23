import os
import logging
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from open_webui.utils.auth import get_verified_user

log = logging.getLogger(__name__)
router = APIRouter()

SUNO_API_URL = os.getenv("SUNO_API_URL", "http://suno-api:3000")


class MusicGenerateForm(BaseModel):
    prompt: str
    make_instrumental: bool = False


@router.post("/generate")
async def generate_music(form: MusicGenerateForm, user=Depends(get_verified_user)):
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{SUNO_API_URL}/api/generate",
                json={
                    "prompt": form.prompt,
                    "make_instrumental": form.make_instrumental,
                    "wait_audio": True,
                },
            )
            response.raise_for_status()
            return response.json()
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="Suno API timeout — spróbuj ponownie")
    except httpx.HTTPStatusError as e:
        log.error(f"Music generation suno error: {e.response.status_code} {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        log.error(f"Music generation error: {e}")
        raise HTTPException(status_code=500, detail="Błąd komunikacji z Suno API")


@router.get("/limit")
async def get_music_limit(user=Depends(get_verified_user)):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{SUNO_API_URL}/api/get_limit")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        log.error(f"Music limit error: {e}")
        raise HTTPException(status_code=500, detail="Błąd komunikacji z Suno API")
