"""
전체 번호 배치 테스트 - 로스터/스탯 1회 수집 후 모든 번호 순회
"""
import sys
import time
import logging
logging.disable(logging.CRITICAL)

sys.path.insert(0, 'data/scraper')
sys.path.insert(0, 'backend')

from kbo_scraper import (
    fetch_all_rosters, build_kbo_stats_map, fetch_statiz_war,
    fetch_recent_games, _calc_iso, JERSEY_MIN, JERSEY_MAX,
    DEFAULT_HEADERS, TEAM_CODES,
)
from recommend import build_recommendation, _score_player
import requests

print("=== 데이터 수집 중... ===")
all_rosters = fetch_all_rosters()
print(f"  로스터: {sum(len(v) for v in all_rosters.values())}명")

stats_map = build_kbo_stats_map()
print(f"  탑랭킹: {len(stats_map)}명")

war_data = fetch_statiz_war()
print(f"  WAR: {len(war_data)}명")

# 팀 상세 캐시 (투타/생년월일)
from kbo_scraper import fetch_team_detail, REGISTER_TEAM_NAMES, REGISTER_ALL_TEAM_ORDER
team_detail_cache = {}
detail_session = requests.Session()
detail_session.headers.update(DEFAULT_HEADERS)
for code in REGISTER_ALL_TEAM_ORDER:
    try:
        team_detail_cache[code] = fetch_team_detail(code, session=detail_session)
        time.sleep(0.3)
    except Exception:
        team_detail_cache[code] = []
print(f"  팀상세 캐시 완료\n")

def make_players(jersey_str):
    matched = [
        {**p, "team": team_name}
        for team_name, players in all_rosters.items()
        for p in players
        if p["jersey"] == jersey_str
    ]
    result = []
    for basic in matched:
        team_full = basic["team"]
        player_name = basic["name"]
        position = basic["position"]
        team_code = next(
            (code for full, code in TEAM_CODES.items() if full == team_full), ""
        )
        detail_info = next(
            (p for p in team_detail_cache.get(team_code, []) if p["name"] == player_name),
            {}
        )
        stat_info = stats_map.get(player_name, {})
        is_carry = bool(stat_info)
        player_id = stat_info.get("player_id")
        is_pitcher = stat_info.get("is_pitcher", position == "투수")

        recent_games = []
        if is_carry and player_id:
            try:
                recent_games = fetch_recent_games(player_id, is_pitcher=is_pitcher, n=5)
                time.sleep(0.3)
            except Exception:
                pass

        war_info = war_data.get(player_name, {})
        result.append({
            "jersey": jersey_str,
            "name": player_name,
            "team": team_full,
            "team_code": team_code,
            "position": detail_info.get("position", position),
            "bat_throw": detail_info.get("bat_throw", ""),
            "birthdate": detail_info.get("birthdate", ""),
            "age": detail_info.get("age"),
            "is_carry": is_carry,
            "player_id": player_id,
            "season_ops": stat_info.get("ops") if not is_pitcher else None,
            "season_era": stat_info.get("era") if is_pitcher else None,
            "season_iso": _calc_iso(stat_info.get("slg"), stat_info.get("avg")) if not is_pitcher else None,
            "war": war_info.get("war"),
            "recent_games": recent_games,
        })
    return result

# 전체 순회
print("번호  팀수  carry  1위팀점수  팬타입")
print("-" * 60)

type_counter = {}
empty = []
all_carry_counts = []
all_top_scores = []

for n in range(JERSEY_MIN, JERSEY_MAX + 1):
    players = make_players(str(n))
    if not players:
        empty.append(n)
        continue

    result = build_recommendation(players)
    carry_n = sum(1 for p in players if p["is_carry"])
    top_score = result["teams"][0]["fan_index"] if result["teams"] else 0
    fan_types = result["fan_types"]
    top_team = result["teams"][0]["team"] if result["teams"] else "-"

    all_carry_counts.append(carry_n)
    all_top_scores.append(top_score)

    for t in fan_types:
        type_counter[t] = type_counter.get(t, 0) + 1

    types_str = "+".join(fan_types) if fan_types else "(없음)"
    print(f"{n:3}번  {len(players)}팀  carry={carry_n}  1위={top_score}점  {types_str}")

print("\n=== 요약 ===")
print(f"번호 없음: {empty}")
print(f"평균 carry 수: {sum(all_carry_counts)/len(all_carry_counts):.2f}")
print(f"평균 1위 점수: {sum(all_top_scores)/len(all_top_scores):.1f}")
print(f"최고 1위 점수: {max(all_top_scores)}")
print(f"1위 점수 분포: 15점={all_top_scores.count(15)} / 16~50={sum(1 for s in all_top_scores if 16<=s<=50)} / 51~={sum(1 for s in all_top_scores if s>=51)}")
print(f"\n팬 타입 등장 횟수:")
for t, c in sorted(type_counter.items(), key=lambda x: -x[1]):
    print(f"  {t}: {c}번")
