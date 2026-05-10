"""
FastAPI 백엔드 — 당신의 조상은 아닙니다만 응원팀 정해드립니다
"""
import sys
import os
from pathlib import Path

# kbo_scraper 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "data" / "scraper"))
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from data_store import find_players_by_jersey, get_updated_at
from recommend import build_recommendation

JERSEY_MIN = 0
JERSEY_MAX = 99

app = FastAPI(title="응원팀 추천 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# ── 추천 API ──────────────────────────────────────────────────────────────────

@app.get("/api/recommend")
async def recommend(number: int = Query(..., ge=JERSEY_MIN, le=JERSEY_MAX)):
    """
    등번호를 입력받아 응원팀 + 팬 성향을 반환합니다.
    """
    players = find_players_by_jersey(number)
    return build_recommendation(players)


@app.get("/api/health")
async def health():
    return {"status": "ok", "data_updated_at": get_updated_at()}


# ── 프론트엔드 정적 파일 서빙 ──────────────────────────────────────────────────

_frontend = Path(__file__).parent.parent / "frontend"

app.mount("/css",    StaticFiles(directory=str(_frontend / "css")),    name="css")
app.mount("/js",     StaticFiles(directory=str(_frontend / "js")),     name="js")
app.mount("/images", StaticFiles(directory=str(_frontend / "images")), name="images")

@app.get("/")
async def index():
    return FileResponse(str(_frontend / "index.html"))
