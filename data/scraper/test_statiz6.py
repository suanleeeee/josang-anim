import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9',
    'Referer': 'https://statiz.co.kr/'
}

# 선수 검색: 김상수
search_url = 'https://statiz.co.kr/player/?m=search&s=김상수'
resp = requests.get(search_url, headers=headers, timeout=15)
print('Search status:', resp.status_code, 'Length:', len(resp.text))
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'lxml')

# 검색 결과 테이블
tables = soup.find_all('table')
print(f'Tables: {len(tables)}')
for t in tables[:3]:
    rows = t.find_all('tr')
    print(f'\nTable ({len(rows)} rows):')
    for row in rows[:5]:
        cells = row.find_all(['td','th'])
        links = [a.get('href','') for a in row.find_all('a')]
        print('  texts:', [c.get_text(strip=True) for c in cells[:6]])
        if links:
            print('  links:', links[:3])

# 선수 검색 결과 div 확인
player_divs = soup.find_all('div', class_=lambda c: c and 'player' in str(c).lower())
print(f'\nPlayer divs: {len(player_divs)}')
for d in player_divs[:3]:
    print('  class:', d.get('class'), 'text:', d.get_text(strip=True)[:80])

# 개인 선수 페이지 (박성한 p_no=12922)
player_url = 'https://statiz.co.kr/player/?m=playerinfo&p_no=12922'
resp2 = requests.get(player_url, headers=headers, timeout=15)
print('\nPlayer page status:', resp2.status_code, 'Length:', len(resp2.text))
resp2.encoding = 'utf-8'
soup2 = BeautifulSoup(resp2.text, 'lxml')
tables2 = soup2.find_all('table')
print(f'Tables in player page: {len(tables2)}')
for i, t in enumerate(tables2[:4]):
    rows = t.find_all('tr')
    print(f'\nTable {i} ({len(rows)} rows):')
    for row in rows[:4]:
        cells = row.find_all(['td','th'])
        print('  ', [c.get_text(strip=True) for c in cells[:12]])
