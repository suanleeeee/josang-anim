import sys
sys.path.insert(0, 'data/scraper')
sys.path.insert(0, 'backend')

from kbo_scraper import find_players_by_jersey
from recommend import build_recommendation, _score_player

jersey = sys.argv[1] if len(sys.argv) > 1 else "7"

players = find_players_by_jersey(jersey)
result = build_recommendation(players)

print(f"\n=== {jersey}번 팀 순위 ===")
for t in result["teams"]:
    print(f"  {t['rank']}위: {t['team']} / {t['fan_index']}점")

print(f"\n=== 팬 타입 ===")
print(f"  no_carry={result.get('no_carry')} / {result['fan_types']} / probs={result.get('fan_type_probs', {})}")

print(f"\n=== 선수별 원점수 ===")
for p in players:
    score = _score_player(p)
    carry = "carry" if p["is_carry"] else "비carry"
    war = p["war"]
    ops = p.get("season_ops")
    era = p.get("season_era")
    age = p.get("age")
    pos = p.get("position", "")
    print(f"  [{p['team']}] {p['name']} {pos} {age}세 ({carry}) WAR={war} OPS={ops} ERA={era} / {score:.1f}점")
