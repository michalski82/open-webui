"""Bot integration endpoints — internal use only."""

from __future__ import annotations

import httpx
import logging
import os
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from open_webui.models.users import Users
from open_webui.utils.auth import get_verified_user

log = logging.getLogger(__name__)
router = APIRouter()

BOT_SECRET = os.getenv('BOT_SECRET', '')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_ADMIN_CHAT_ID = os.getenv('TELEGRAM_ADMIN_CHAT_ID', '')


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


class NotifyAdminResponse(BaseModel):
    ok: bool


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


@router.post('/notify-admin', response_model=NotifyAdminResponse)
async def notify_admin(
    user=Depends(get_verified_user),
):
    if not TELEGRAM_BOT_TOKEN:
        raise HTTPException(status_code=503, detail='TELEGRAM_BOT_TOKEN not configured')
    if not TELEGRAM_ADMIN_CHAT_ID:
        raise HTTPException(status_code=503, detail='TELEGRAM_ADMIN_CHAT_ID not configured')

    email = user.email
    # callback_data limit: 64 bytes. Format: "g24:<email>" (5 bytes + email).
    # Max email length: 59 bytes. Truncate defensively.
    safe_email = email[:59]
    text = (
        f"Uzytkownik prosi o dostep Gemini:\n"
        f"`{email}`\n\n"
        f"Wybierz czas aktywacji:"
    )
    payload = {
        "chat_id": TELEGRAM_ADMIN_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
        "reply_markup": {
            "inline_keyboard": [[
                {"text": "Aktywuj 24h", "callback_data": f"g24:{safe_email}"},
                {"text": "Aktywuj 48h", "callback_data": f"g48:{safe_email}"},
            ]]
        },
    }
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, json=payload)
        if not resp.is_success:
            log.error("Telegram API error: %s %s", resp.status_code, resp.text)
            raise HTTPException(status_code=502, detail='Failed to send Telegram notification')
    return NotifyAdminResponse(ok=True)
