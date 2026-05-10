import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://www.koreabaseball.com/'
}

# 박성한 상세 페이지 (타자)
url = 'https://www.koreabaseball.com/Record/Player/HitterDetail/Basic.aspx?playerId=67893'
resp = requests.get(url, headers=headers, timeout=15)
print('Status:', resp.status_code, 'Length:', len(resp.text))
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'lxml')

tables = soup.find_all('table')
print(f'Tables: {len(tables)}')
for i, t in enumerate(tables):
    rows = t.find_all('tr')
    print(f'\nTable {i} ({len(rows)} rows):')
    for row in rows[:5]:
        cells = row.find_all(['td','th'])
        print('  ', [c.get_text(strip=True) for c in cells[:12]])

# 최근 경기 관련 섹션
h2_h3 = soup.find_all(['h2','h3','h4'])
for h in h2_h3:
    print('Heading:', h.get_text(strip=True))
