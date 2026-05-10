"""
KBO 로스터 수집 (팀/등번호/선수 배정)
- 주 1회 자동 실행 또는 트레이드/외국인 영입 시 수동 실행
"""
import sys
import json
import time
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scraper"))

from kbo_scraper import (
    fetch_all_rosters,
    fetch_team_detail,
    DEFAULT_HEADERS,
    REGISTER_ALL_TEAM_ORDER,
)
import requests
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

KST = timezone(timedelta(hours=9))
OUT_PATH = Path(__file__).parent / "roster.json"


def collect():
    log.info("=== 로스터 수집 ===")
    rosters_raw = fetch_all_rosters()
    log.info("  %d팀 수집 완료", len(rosters_raw))

    log.info("=== 팀 상세(투타/생년월일) 수집 ===")
    detail_by_name: dict = {}
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    for code in REGISTER_ALL_TEAM_ORDER:
        try:
            players = fetch_team_detail(code, session=session)
            for p in players:
                detail_by_name[p["name"]] = p
            log.info("  %s 완료", code)
            time.sleep(0.5)
        except Exception as e:
            log.warning("  %s 실패: %s", code, e)

    rosters_enriched = {}
    for team_name, players in rosters_raw.items():
        rosters_enriched[team_name] = [
            {
                "jersey":    p["jersey"],
                "name":      p["name"],
                "position":  detail_by_name.get(p["name"], {}).get("position", p["position"]),
                "bat_throw": detail_by_name.get(p["name"], {}).get("bat_throw", ""),
                "birthdate": detail_by_name.get(p["name"], {}).get("birthdate", ""),
                "age":       detail_by_name.get(p["name"], {}).get("age"),
            }
            for p in players
        ]

    data = {
        "updated_at": datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "rosters": rosters_enriched,
    }
    OUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(v) for v in rosters_enriched.values())
    log.info("=== 저장 완료: %s (%d팀 %d명) ===", OUT_PATH.name, len(rosters_enriched), total)


if __name__ == "__main__":
    collect()
