import json, sys, io, subprocess, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

for jersey in ['7', '23', '36', '99']:
    print(f'\n{"="*50}')
    print(f'  등번호 {jersey}번')
    print(f'{"="*50}')
    result = subprocess.run(
        ['python', 'kbo_scraper.py', jersey],
        capture_output=True, text=True, encoding='utf-8', errors='replace'
    )
    # 마지막 JSON 파일 읽기
    import glob, os
    files = sorted(glob.glob(f'jersey_{jersey}_*.json'))
    if files:
        d = json.load(open(files[-1], encoding='utf-8'))
        print(f"총 {d['total_players']}명 / 캐리 {sum(1 for p in d['players'] if p['is_carry'])}명")
        for p in d['players']:
            carry = '★' if p['is_carry'] else ' '
            games = len(p['recent_games'])
            print(f"  {carry} {p['name']:8} ({p['team']}) ops={p['season_ops']} era={p['season_era']} war={p['war']} 최근{games}경기")
    else:
        print('결과 없음')
    time.sleep(3)
