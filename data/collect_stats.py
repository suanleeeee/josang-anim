"""
KBO 시즌 스탯 수집 (OPS/ERA 랭킹, WAR)
- 매일 자동 실행
"""
import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "scraper"))

from kbo_scraper import build_kbo_stats_map, fetch_statiz_war
from datetime import datetime, timezone, timedelta

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

KST = timezone(timedelta(hours=9))
OUT_PATH = Path(__file__).parent / "stats.json"


def collect():
    log.info("=== KBO 탑 랭킹 수집 ===")
    stats_map = build_kbo_stats_map()
    log.info("  %d명 완료", len(stats_map))

    log.info("=== WAR 수집 ===")
    war_map = fetch_statiz_war()
    log.info("  %d명 완료", len(war_map))

    data = {
        "updated_at": datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S+09:00"),
        "stats": stats_map,
        "war": war_map,
    }
    OUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("=== 저장 완료: %s (스탯 %d명, WAR %d명) ===",
             OUT_PATH.name, len(stats_map), len(war_map))


if __name__ == "__main__":
    collect()
