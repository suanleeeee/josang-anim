import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

url = 'https://www.koreabaseball.com/Player/RegisterAll.aspx'
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

resp = session.get(url, timeout=15)
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'lxml')

# 팀 구분 헤더 찾기
h3_tags = soup.find_all('h3')
print(f'h3 tags: {len(h3_tags)}')
for h in h3_tags[:5]:
    print(' ', h.get_text(strip=True))

# 테이블 구조
tables = soup.find_all('table')
print(f'\nTotal tables: {len(tables)}')
for i, t in enumerate(tables[:3]):
    print(f'\nTable {i} class={t.get("class")}:')
    rows = t.find_all('tr')
    for row in rows[:5]:
        cells = row.find_all(['td','th'])
        print('  ', [c.get_text(strip=True) for c in cells])

# 팀명 포함 div 찾기
team_divs = soup.find_all(['div','section'], class_=lambda c: c and ('team' in str(c).lower() or 'wrap' in str(c).lower()))
print(f'\nTeam-related divs: {len(team_divs)}')
for d in team_divs[:3]:
    print(f'  class={d.get("class")}, text={d.get_text(strip=True)[:60]}')

# 선수 이름이 들어있는 span 등 찾기
player_items = soup.find_all('li')
print(f'\nList items: {len(player_items)}')
for li in player_items[:10]:
    print(' ', li.get_text(strip=True)[:80])
