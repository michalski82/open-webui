"""Bot integration endpoints — internal use only."""

from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from open_webui.models.users import Users

log = logging.getLogger(__name__)
router = APIRouter()

BOT_SECRET = os.getenv('BOT_SECRET', '')


def _verify_bot_secret(x_bot_secret: str | None = Header(default=None, alias='X-Bot-Secret')) -> None:
    if not BOT_SECRET:
        raise HTTPException(status_code=503, detail='BOT_SECRET not configured')
    if x_bot_secret != BOT_SECRET:
        raise HTTPException(status_code=401, detail='Invalid bot secret')


class GeminiAccessRequest(BaseModel):
    email: str
    hours: int = 24


class GeminiAccessResponse(BaseModel):
    ok: bool
    until: str  # ISO 8601


@router.post('/gemini-access', response_model=GeminiAccessResponse)
async def activate_gemini_access(
    form: GeminiAccessRequest,
    _: None = Depends(_verify_bot_secret),
):
    until_epoch = int(time.time()) + form.hours * 3600
    user = await Users.update_gemini_access_by_email(form.email, until_epoch)
    if not user:
        raise HTTPException(status_code=404, detail=f'User not found: {form.email}')
    until_dt = datetime.fromtimestamp(until_epoch, tz=timezone.utc)
    return GeminiAccessResponse(ok=True, until=until_dt.isoformat())
