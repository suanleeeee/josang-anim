import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://statiz.co.kr/'
}

# 스탯티즈 선수 검색 - 선수명으로 ID 찾기
# 예: 박성한
search_url = 'https://statiz.co.kr/player/?m=search&s=박성한'
resp = requests.get(search_url, headers=headers, timeout=15)
print('Status:', resp.status_code)
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'lxml')

# 검색 결과 확인
tables = soup.find_all('table')
print(f'Tables: {len(tables)}')
for t in tables[:2]:
    rows = t.find_all('tr')
    for row in rows[:5]:
        cells = row.find_all(['td','th'])
        texts = [c.get_text(strip=True) for c in cells]
        links = [a.get('href','') for a in row.find_all('a') if a.get('href')]
        print('  texts:', texts[:6], 'links:', links[:2])

# 다른 방법: 직접 player URL 패턴 테스트
player_url = 'https://statiz.co.kr/player/?m=playerinfo&p_no=67893'  # 박성한
resp2 = requests.get(player_url, headers=headers, timeout=15)
resp2.encoding = 'utf-8'
soup2 = BeautifulSoup(resp2.text, 'lxml')
print('\n--- 선수 개인 페이지 ---')
tables2 = soup2.find_all('table')
print(f'Tables: {len(tables2)}')
title = soup2.find('h3') or soup2.find('h2') or soup2.find('h1')
if title:
    print('Title:', title.get_text(strip=True))
# 최근 5경기 테이블 찾기
for t in tables2[:3]:
    rows = t.find_all('tr')
    print(f'\nTable: {len(rows)} rows')
    for row in rows[:4]:
        cells = row.find_all(['td','th'])
        print('  ', [c.get_text(strip=True) for c in cells[:10]])
