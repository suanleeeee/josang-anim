import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
d = json.load(open('jersey_2_20260506_130512.json', encoding='utf-8'))
print(f"총 {d['total_players']}명\n")
for p in d['players']:
    carry = '★캐리' if p['is_carry'] else '    '
    print(f"{carry} {p['name']:8} ({p['team']}) ops={p['season_ops']} war={p['war']}")
