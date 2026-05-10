"""
data/roster.json + data/stats.json 에서 데이터를 읽어 제공합니다.
- roster.json: 주 1회 갱신 (팀/등번호/선수)
- stats.json:  매일 갱신 (OPS/ERA/WAR)
"""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_DATA_DIR = Path(__file__).parent.parent / "data"


def _load_json(filename: str) -> dict:
    path = _DATA_DIR / filename
    if not path.exists():
        logger.error("데이터 파일 없음: %s", path)
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    logger.info("%s 로드 완료 (갱신: %s)", filename, data.get("updated_at", "?"))
    return data


_roster_db: dict = _load_json("roster.json")
_stats_db: dict  = _load_json("stats.json")


def get_updated_at() -> dict:
    return {
        "roster": _roster_db.get("updated_at", "unknown"),
        "stats":  _stats_db.get("updated_at", "unknown"),
    }


def find_players_by_jersey(jersey: int) -> list:
    rosters   = _roster_db.get("rosters", {})
    stats_map = _stats_db.get("stats", {})
    war_map   = _stats_db.get("war", {})

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
