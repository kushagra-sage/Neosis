"""Inquiry routes — REST + WebSocket.

  POST  /inquiries                  — sync run (returns when pipeline completes)
  GET   /inquiries                  — list history
  GET   /inquiries/{id}             — get a single inquiry
  WS    /ws/inquiry                 — streaming inquiry (token + stage events)
"""
from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.inquiry import InquiryHistoryItem, InquiryRequest, InquiryResponse
from app.security.dependencies import CurrentUser, get_current_user
from app.services.inquiry_service import (
    create_and_run_inquiry,
    get_inquiry,
    list_inquiries,
)

router = APIRouter(tags=["inquiry"])


@router.post("/inquiries", response_model=InquiryResponse, status_code=status.HTTP_201_CREATED)
async def run_inquiry_sync(
    body: InquiryRequest,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InquiryResponse:
    record = await create_and_run_inquiry(
        db,
        question=body.question,
        user_id=current_user.id,
        workspace_id=body.workspace_id,
    )
    await db.commit()
    await db.refresh(record)
    return InquiryResponse.model_validate(record)


@router.get("/inquiries", response_model=list[InquiryHistoryItem])
async def inquiry_history(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    workspace_id: str | None = Query(default=None),
    limit: int = Query(default=20, le=100),
) -> list[InquiryHistoryItem]:
    inquiries = await list_inquiries(db, current_user.id, workspace_id, limit)
    return [InquiryHistoryItem.model_validate(i) for i in inquiries]


@router.get("/inquiries/{inquiry_id}", response_model=InquiryResponse)
async def get_inquiry_detail(
    inquiry_id: str,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> InquiryResponse:
    from fastapi import HTTPException
    record = await get_inquiry(db, inquiry_id, current_user.id)
    if not record:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    return InquiryResponse.model_validate(record)


# ── WebSocket streaming ───────────────────────────────────────────────────────


@router.websocket("/ws/inquiry")
async def inquiry_websocket(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token"),
    workspace_id: str | None = Query(default=None),
):
    """
    WS protocol:
      1. Client sends: {"question": "..."}
      2. Server sends stage events:  {"type":"stage", "stage":"planning"}
      3. Server sends token events:  {"type":"token", "content":"..."}
      4. Server sends dossier event: {"type":"dossier", "items":[...]}
      5. Server sends critic event:  {"type":"critic", "scores":{...}}
      6. Server sends done event:    {"type":"done", "inquiry_id":"..."}
    """
    await websocket.accept()

    # Authenticate via query-param token
    from app.cache.redis_client import get_redis
    from app.db.session import SessionLocal
    from app.security.tokens import decode_access_token
    from jose import JWTError

    try:
        user_id = decode_access_token(token)
    except JWTError:
        await websocket.send_json({"type": "error", "message": "Invalid token"})
        await websocket.close(code=4001)
        return

    async with SessionLocal() as db:
        from app.services.user_service import get_user_by_id
        user = await get_user_by_id(db, user_id)
        if not user or not user.is_active:
            await websocket.send_json({"type": "error", "message": "Unauthorized"})
            await websocket.close(code=4001)
            return

        try:
            raw = await websocket.receive_text()
            payload = json.loads(raw)
            question = payload.get("question", "").strip()
            if not question:
                await websocket.send_json({"type": "error", "message": "Empty question"})
                return
        except Exception:
            await websocket.send_json({"type": "error", "message": "Invalid message format"})
            return

        async def token_cb(chunk: str) -> None:
            try:
                await websocket.send_json({"type": "token", "content": chunk})
            except Exception:
                pass

        async def stage_cb(stage: str, data: dict) -> None:
            try:
                await websocket.send_json({"type": "stage", "stage": stage, **data})
            except Exception:
                pass

        try:
            record = await create_and_run_inquiry(
                db,
                question=question,
                user_id=user.id,
                workspace_id=workspace_id,
                token_callback=token_cb,
                stage_callback=stage_cb,
            )
            await db.commit()
            await db.refresh(record)

            # Send dossier + critic scores as structured events
            if record.dossier:
                await websocket.send_json({"type": "dossier", "items": record.dossier[:10]})
            if record.critic_scores:
                await websocket.send_json({"type": "critic", "scores": record.critic_scores})

            await websocket.send_json({"type": "done", "inquiry_id": record.id})

        except WebSocketDisconnect:
            pass
        except Exception as exc:
            try:
                await websocket.send_json({"type": "error", "message": str(exc)})
            except Exception:
                pass
