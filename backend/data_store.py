"""
data/YEAR.json 에서 로스터+스탯+WAR 데이터를 읽어 제공합니다.
라이브 스크래핑 없이 사전 수집된 데이터만 사용합니다.
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)

KST = timezone(timedelta(hours=9))
_DATA_DIR = Path(__file__).parent.parent / "data"


def _load() -> dict:
    year = datetime.now(KST).year
    path = _DATA_DIR / f"{year}.json"
    if not path.exists():
        # 전년도 fallback
        path = _DATA_DIR / f"{year - 1}.json"
    if not path.exists():
        logger.error("데이터 파일 없음: %s", _DATA_DIR)
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    logger.info("데이터 로드: %s (갱신: %s)", path.name, data.get("updated_at", "?"))
    return data


# 앱 시작 시 1회 로드
_db: dict = _load()


def get_updated_at() -> str:
    return _db.get("updated_at", "unknown")


def find_players_by_jersey(jersey: int) -> list:
    """등번호로 해당 선수 목록 반환."""
    rosters: dict = _db.get("rosters", {})
    stats_map: dict = _db.get("stats", {})
    war_map: dict = _db.get("war", {})

    jersey_str = str(jersey)
    result = []

    for team_name, players in rosters.items():
        for p in players:
            if p["jersey"] != jersey_str:
                continue

            name = p["name"]
            stat = stats_map.get(name, {})
            war_info = war_map.get(name, {})
            is_carry = bool(stat)
            is_pitcher = stat.get("is_pitcher", p.get("position") == "투수")

            result.append({
                "jersey":       jersey_str,
                "name":         name,
                "team":         team_name,
                "position":     p.get("position", ""),
                "bat_throw":    p.get("bat_throw", ""),
                "birthdate":    p.get("birthdate", ""),
                "age":          p.get("age"),
                "is_carry":     is_carry,
                "player_id":    stat.get("player_id"),
                "season_ops":   stat.get("ops") if not is_pitcher else None,
                "season_slg":   stat.get("slg") if not is_pitcher else None,
                "season_era":   stat.get("era") if is_pitcher else None,
                "war":          war_info.get("war"),
                "recent_games": stat.get("recent_games", []),
            })

    return result
