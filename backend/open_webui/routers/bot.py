"""Bot integration endpoints — internal use only."""

from __future__ import annotations

import httpx
import logging
import os
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel

from open_webui.internal.db import get_async_db_context
from open_webui.models.auths import Auth, Auths
from open_webui.models.users import Users
from open_webui.utils.auth import get_password_hash, get_verified_user
from sqlalchemy import update as sa_update

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


class UserEntry(BaseModel):
    id: str
    email: str
    name: str
    role: str


class UserCreateRequest(BaseModel):
    email: str
    name: str
    password: str
    role: str = 'user'


class UserEmailRequest(BaseModel):
    email: str


class GeminiAccessRequest(BaseModel):
    email: str
    hours: int = 24


class GeminiAccessResponse(BaseModel):
    ok: bool
    until: str  # ISO 8601


class NotifyAdminResponse(BaseModel):
    ok: bool


class GeminiUserEntry(BaseModel):
    email: str
    name: str
    active: bool
    until: str | None


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
                {"text": "Dezaktywuj", "callback_data": f"g0:{safe_email}"},
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


@router.get('/gemini-users', response_model=list[GeminiUserEntry])
async def list_gemini_users(
    _: None = Depends(_verify_bot_secret),
):
    users = await Users.get_all_users_gemini_panel()
    now = int(time.time())
    result = []
    for u in users:
        active = bool(u.gemini_access_until and u.gemini_access_until > now)
        if u.gemini_access_until and u.gemini_access_until > now:
            until_dt = datetime.fromtimestamp(u.gemini_access_until, tz=timezone.utc)
            until_str = until_dt.isoformat()
        else:
            until_str = None
        result.append(GeminiUserEntry(
            email=u.email,
            name=u.name,
            active=active,
            until=until_str,
        ))
    return result


@router.get('/users', response_model=list[UserEntry])
async def list_users(
    _: None = Depends(_verify_bot_secret),
):
    result = await Users.get_users()
    return [
        UserEntry(id=u.id, email=u.email, name=u.name, role=u.role)
        for u in result['users']
    ]


@router.post('/users/create', response_model=UserEntry, status_code=201)
async def create_user(
    form: UserCreateRequest,
    _: None = Depends(_verify_bot_secret),
):
    existing = await Users.get_user_by_email(form.email)
    if existing:
        raise HTTPException(status_code=409, detail=f'User already exists: {form.email}')
    hashed = await get_password_hash(form.password)
    user = await Auths.insert_new_auth(
        email=form.email.lower(),
        password=hashed,
        name=form.name,
        role=form.role,
    )
    if not user:
        raise HTTPException(status_code=500, detail='Failed to create user')
    return UserEntry(id=user.id, email=user.email, name=user.name, role=user.role)


@router.post('/users/disable')
async def disable_user(
    form: UserEmailRequest,
    _: None = Depends(_verify_bot_secret),
):
    user = await Users.get_user_by_email(form.email)
    if not user:
        raise HTTPException(status_code=404, detail=f'User not found: {form.email}')
    async with get_async_db_context() as session:
        await session.execute(
            sa_update(Auth).where(Auth.id == user.id).values(active=False)
        )
        await session.commit()
    return {'ok': True}


@router.post('/users/enable')
async def enable_user(
    form: UserEmailRequest,
    _: None = Depends(_verify_bot_secret),
):
    user = await Users.get_user_by_email(form.email)
    if not user:
        raise HTTPException(status_code=404, detail=f'User not found: {form.email}')
    async with get_async_db_context() as session:
        await session.execute(
            sa_update(Auth).where(Auth.id == user.id).values(active=True)
        )
        await session.commit()
    return {'ok': True}


@router.delete('/users/{email:path}')
async def delete_user(
    email: str,
    _: None = Depends(_verify_bot_secret),
):
    user = await Users.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail=f'User not found: {email}')
    success = await Auths.delete_auth_by_id(user.id)
    if not success:
        raise HTTPException(status_code=500, detail='Failed to delete user')
    return {'ok': True}
