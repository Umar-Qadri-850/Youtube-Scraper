"""
FastAPI YouTube Channel Latest-Video + Transcript Scraper
-----------------------------------------------------------
Wraps the Apify actor `starvibe/youtube-video-transcript` to:
  1. Accept a YouTube CHANNEL url (e.g. https://www.youtube.com/@JeffSu/videos)
  2. Fetch the latest video from that channel
  3. Return the video metadata + full transcript as JSON

SETUP
-----
1. pip install fastapi uvicorn httpx
2. Get a free Apify API token: https://console.apify.com/account/integrations
3. Set it as an environment variable before running:
       export APIFY_API_TOKEN="apify_api_xxxxxxxxxxxxxxxxxxxx"     (Linux/Mac)
       setx APIFY_API_TOKEN "apify_api_xxxxxxxxxxxxxxxxxxxx"       (Windows)
4. Run the server:
       uvicorn main:app --reload
5. Test it:
       curl "http://127.0.0.1:8000/latest-video?channel_url=https://www.youtube.com/@JeffSu/videos"

   or just open it in a browser, or use the interactive docs at http://127.0.0.1:8000/docs
"""

import os
import re
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN", "")
APIFY_ACTOR_ID = "starvibe~youtube-video-transcript"  # '~' used instead of '/' in the URL
APIFY_RUN_SYNC_URL = f"https://api.apify.com/v2/acts/{APIFY_ACTOR_ID}/run-sync-get-dataset-items"

REQUEST_TIMEOUT_SECONDS = 180.0  # transcript scraping can take a little while

app = FastAPI(
    title="YouTube Channel Latest Video & Transcript API",
    description="Give a YouTube channel URL, get back the latest video's metadata and transcript as JSON.",
    version="1.0.0",
)


# --------------------------------------------------------------------------
# Request / Response models
# --------------------------------------------------------------------------

def normalize_channel_url(v: str) -> str:
    v = (v or "").strip()
    if not v:
        raise HTTPException(status_code=422, detail="channel_url must not be empty")
    # Strip trailing '/videos', '/streams', '/shorts', '/featured' etc. so we
    # always hit the canonical channel URL that the actor expects.
    v = re.sub(r"/(videos|streams|shorts|featured|playlists|community|about)/?$", "", v)
    if "youtube.com" not in v:
        raise HTTPException(status_code=422, detail="channel_url must be a youtube.com URL")
    return v


class TranscriptSegment(BaseModel):
    start: float
    end: float
    text: str


class LatestVideoResponse(BaseModel):
    status: str
    channel_url: str
    video_id: Optional[str] = None
    title: Optional[str] = None
    url: Optional[str] = None
    channel_name: Optional[str] = None
    channel_username: Optional[str] = None
    published_at: Optional[str] = None
    view_count: Optional[int] = None
    like_count: Optional[int] = None
    comment_count: Optional[int] = None
    duration_seconds: Optional[int] = None
    description: Optional[str] = None
    thumbnail: Optional[str] = None
    selected_language: Optional[str] = None
    is_auto_generated: Optional[bool] = None
    available_languages: Optional[List[str]] = None
    transcript: Optional[List[TranscriptSegment]] = None
    transcript_text: Optional[str] = None
    message: Optional[str] = None


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------

async def call_apify_actor(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Calls the Apify actor synchronously and returns the dataset items list."""
    if not APIFY_API_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="Server misconfiguration: APIFY_API_TOKEN environment variable is not set.",
        )

    params = {"token": APIFY_API_TOKEN}

    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT_SECONDS) as client:
        try:
            resp = await client.post(APIFY_RUN_SYNC_URL, params=params, json=payload)
        except httpx.TimeoutException:
            raise HTTPException(status_code=504, detail="Timed out waiting for the Apify actor to finish.")
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Failed to reach Apify: {e}")

    if resp.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid APIFY_API_TOKEN.")
    if resp.status_code >= 400:
        raise HTTPException(
            status_code=resp.status_code,
            detail=f"Apify actor call failed: {resp.text}",
        )

    try:
        data = resp.json()
    except ValueError:
        raise HTTPException(status_code=502, detail="Apify returned a non-JSON response.")

    if not isinstance(data, list):
        raise HTTPException(status_code=502, detail="Unexpected response format from Apify actor.")

    return data


def pick_latest_video(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Picks the most recently published video from the returned items."""
    if not items:
        raise HTTPException(status_code=404, detail="No videos found for this channel.")

    def sort_key(item: Dict[str, Any]):
        # 'timestamp' is a unix epoch int; fall back to 0 if missing
        return item.get("timestamp") or 0

    return max(items, key=sort_key)


# --------------------------------------------------------------------------
# Routes
# --------------------------------------------------------------------------

@app.get("/")
async def root():
    return {
        "message": "YouTube Channel Latest Video & Transcript API",
        "usage": "GET /latest-video?channel_url=https://www.youtube.com/@JeffSu/videos",
        "docs": "/docs",
    }


@app.get("/latest-video", response_model=LatestVideoResponse)
async def get_latest_video_transcript(
    channel_url: str = Query(
        ...,
        description="YouTube channel URL, e.g. https://www.youtube.com/@JeffSu/videos "
                    "or https://www.youtube.com/@JeffSu or https://www.youtube.com/channel/UCxxxxxxxx",
        examples=["https://www.youtube.com/@JeffSu/videos"],
    ),
    language: Optional[str] = Query(
        default=None,
        description="Preferred transcript language, ISO 639-1 code (e.g. 'en', 'es', 'fr'). "
                    "Leave empty to accept the transcript in whatever language is available "
                    "for the video (recommended, since not every channel has English captions).",
    ),
    include_transcript_text: bool = Query(
        default=True,
        description="If true, also includes a plain-text (no timestamps) transcript field.",
    ),
):
    """
    Given a YouTube channel URL, fetches the latest video and its transcript.
    """
    clean_channel_url = normalize_channel_url(channel_url)

    payload = {
        "channel_url": clean_channel_url,
        "max_videos": 1,  # we only need the newest video
        "include_transcript_text": include_transcript_text,
    }
    if language:
        payload["language"] = language

    items = await call_apify_actor(payload)
    latest = pick_latest_video(items)

    # If the requested language isn't available for this video, the actor
    # returns an error item instead of falling back automatically. In that
    # case, retry once without forcing a language so we get whatever
    # transcript IS available (e.g. the video's native language).
    if latest.get("status") == "error" and language:
        retry_payload = dict(payload)
        retry_payload.pop("language", None)
        items = await call_apify_actor(retry_payload)
        latest = pick_latest_video(items)

    if latest.get("status") == "error":
        raise HTTPException(
            status_code=502,
            detail=latest.get("message", "Actor returned an error for this channel."),
        )

    return LatestVideoResponse(
        status=latest.get("status", "success"),
        channel_url=clean_channel_url,
        video_id=latest.get("video_id"),
        title=latest.get("title"),
        url=latest.get("url"),
        channel_name=latest.get("channel_name"),
        channel_username=latest.get("channel_username"),
        published_at=latest.get("published_at"),
        view_count=latest.get("view_count"),
        like_count=latest.get("like_count"),
        comment_count=latest.get("comment_count"),
        duration_seconds=latest.get("duration_seconds"),
        description=latest.get("description"),
        thumbnail=latest.get("thumbnail"),
        selected_language=latest.get("selected_language"),
        is_auto_generated=latest.get("is_auto_generated"),
        available_languages=latest.get("available_languages"),
        transcript=latest.get("transcript"),
        transcript_text=latest.get("transcript_text"),
        message=latest.get("message"),
    )


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "apify_token_configured": bool(APIFY_API_TOKEN)})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)