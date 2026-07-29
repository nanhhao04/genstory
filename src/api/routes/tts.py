import asyncio
import io
import logging
import os
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from src.api.deps import get_current_user
from src.api.schemas.tts import TTSRequest
from src.core.metrics import TTS_GENERATION_DURATION
from src.database.models import UserTable

router = APIRouter(prefix="/tts", tags=["tts"])


@router.post("")
async def text_to_speech(
    req: TTSRequest,
    current_user: UserTable = Depends(get_current_user),
):
    start_time = time.time()
    status = "success"
    try:
        tts_api_url = os.getenv("TTS_API_URL", "https://api.fpt.ai/hmi/tts/v5")
        tts_key = os.getenv("FPT_API_KEY", "")
        if not tts_key:
            raise HTTPException(status_code=500, detail="FPT_API_KEY chua duoc cau hinh")

        headers = {"api-key": tts_key, "speed": "", "voice": "banmai"}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    tts_api_url, data=req.text.encode("utf-8"), headers=headers, timeout=30
                )
                if response.status_code != 200:
                    logging.error("FPT.AI POST Error: %s - %s", response.status_code, response.text)
                    raise HTTPException(
                        status_code=response.status_code, detail="Loi gui yeu cau den FPT.AI"
                    )

                payload = response.json()
                audio_url = payload.get("async")
                if not audio_url:
                    raise HTTPException(
                        status_code=500, detail="Khong tim thay URL am thanh tu FPT.AI"
                    )

                audio_content = None
                for _ in range(30):
                    audio_response = await client.get(audio_url, timeout=10)
                    if audio_response.status_code == 200:
                        audio_content = audio_response.content
                        break
                    if audio_response.status_code == 404:
                        await asyncio.sleep(1.5)
                        continue
                    logging.error("FPT.AI GET Error: %s", audio_response.status_code)
                    raise HTTPException(
                        status_code=audio_response.status_code, detail="Loi tai file am thanh"
                    )

                if not audio_content:
                    raise HTTPException(
                        status_code=408,
                        detail="FPT.AI xu ly qua lau, vui long thu lai sau giay lat.",
                    )

                return StreamingResponse(io.BytesIO(audio_content), media_type="audio/mpeg")
            except httpx.TimeoutException as exc:
                raise HTTPException(
                    status_code=408, detail="Yeu cau den FPT.AI bi qua han"
                ) from exc
            except HTTPException:
                raise
            except Exception as exc:
                logging.error("TTS Unhandled Error: %s", exc)
                raise HTTPException(
                    status_code=500, detail=f"Loi he thong TTS: {str(exc)}"
                ) from exc
    except Exception as exc:
        status = "failed"
        raise exc
    finally:
        duration = time.time() - start_time
        TTS_GENERATION_DURATION.labels(status=status).observe(duration)
