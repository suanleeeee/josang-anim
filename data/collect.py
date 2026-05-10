"""
KBO 데이터 수집 스크립트
GitHub Actions에서 매일 실행 → data/2026.json 갱신
"""
import sys
import json
import time
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scraper"))

from kbo_scraper import (
    fetch_all_rosters,
    build_kbo_stats_map,
    fetch_statiz_war,
    fetch_team_detail,
    DEFAULT_HEADERS,
    TEAM_CODES,
    REGISTER_ALL_TEAM_ORDER,
)
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

KST = timezone(timedelta(hours=9))
YEAR = datetime.now(KST).year
OUT_PATH = Path(__file__).parent / f"{YEAR}.json"


def collect():
    log.info("=== 로스터 수집 ===")
    rosters_raw = fetch_all_rosters()
    log.info("  %d팀 수집 완료", len(rosters_raw))

    log.info("=== KBO 탑 랭킹 수집 ===")
    stats_map = build_kbo_stats_map()
    log.info("  %d명 수집 완료", len(stats_map))

    log.info("=== WAR 수집 ===")
    war_map = fetch_statiz_war()
    log.info("  %d명 수집 완료", len(war_map))

    log.info("=== 팀 상세(투타/생년월일) 수집 ===")
    detail_cache = {}
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    for code in REGISTER_ALL_TEAM_ORDER:
        try:
            detail_cache[code] = fetch_team_detail(code, session=session)
            log.info("  %s 완료", code)
            time.sleep(0.5)
        except Exception as e:
            log.warning("  %s 실패: %s", code, e)
            detail_cache[code] = []

    # 팀 상세 → 이름 기반 조회용 딕셔너리
    detail_by_name: dict = {}
    for code, players in detail_cache.items():
        for p in players:
            detail_by_name[p["name"]] = p

    # 로스터에 상세 정보 병합
    rosters_enriched = {}
    for team_name, players in rosters_raw.items():
        enriched = []
        for p in players:
            detail = detail_by_name.get(p["name"], {})
            enriched.append({
                "jersey":    p["jersey"],
                "name":      p["name"],
                "position":  detail.get("position", p["position"]),
                "bat_throw": detail.get("bat_throw", ""),
                "birthdate": detail.get("birthdate", ""),
                "age":       detail.get("age"),
            })
        rosters_enriched[team_name] = enriched

    updated_at = datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S+09:00")
    data = {
        "updated_at": updated_at,
        "rosters":    rosters_enriched,
        "stats":      stats_map,
        "war":        war_map,
    }

    OUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("=== 저장 완료: %s ===", OUT_PATH)

    total_players = sum(len(v) for v in rosters_enriched.values())
    log.info("  팀: %d, 선수: %d, 스탯: %d, WAR: %d",
             len(rosters_enriched), total_players, len(stats_map), len(war_map))


if __name__ == "__main__":
    collect()
