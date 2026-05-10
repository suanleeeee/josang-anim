import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Referer': 'https://statiz.co.kr/'
}

# 스탯티즈 시즌 타자 성적
url = 'https://statiz.co.kr/stats/?opt=1&sopt=0&year=2026&ctype=0&cId=&pCode=1&pos=B&sy=2026&ey=2026&m=1&m2=1'
resp = requests.get(url, headers=headers, timeout=15)
print('Status:', resp.status_code)
print('Length:', len(resp.text))
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'lxml')

print('\nPage title:', soup.title.get_text(strip=True) if soup.title else 'None')
tables = soup.find_all('table')
print(f'Tables: {len(tables)}')

# 첫번째 테이블
if tables:
    t = tables[0]
    rows = t.find_all('tr')
    print(f'First table rows: {len(rows)}')
    for row in rows[:3]:
        cells = row.find_all(['td','th'])
        print('  ', [c.get_text(strip=True) for c in cells[:15]])

# WAR 관련 텍스트 찾기
war_elements = soup.find_all(string=lambda s: s and 'WAR' in s)
print(f'\nWAR mentions: {len(war_elements)}')
for w in war_elements[:5]:
    print(' ', str(w).strip()[:100])
