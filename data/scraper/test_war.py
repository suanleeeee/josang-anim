import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://www.koreabaseball.com/'
}

# 스탯티즈 WAR 순위 페이지 (메인에서 WAR TOP10 확인됨)
# stats/ -> 리다이렉트 확인
url = 'https://statiz.co.kr/stats/'
resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
print('Status:', resp.status_code, 'URL:', resp.url, 'Length:', len(resp.text))

# www 버전 시도
url2 = 'https://www.statiz.co.kr/stats/'
resp2 = requests.get(url2, headers=headers, timeout=15, allow_redirects=True)
print('www Status:', resp2.status_code, 'URL:', resp2.url, 'Length:', len(resp2.text))
resp2.encoding = 'utf-8'
soup = BeautifulSoup(resp2.text, 'lxml')
print('Title:', soup.title.get_text(strip=True) if soup.title else 'None')
tables = soup.find_all('table')
print(f'Tables: {len(tables)}')
if tables:
    for row in tables[0].find_all('tr')[:4]:
        cells = row.find_all(['td','th'])
        print('  ', [c.get_text(strip=True) for c in cells[:12]])

# WAR 언급 확인
war_els = soup.find_all(string=lambda s: s and 'WAR' in str(s))
print(f'\nWAR mentions: {len(war_els)}')
for w in war_els[:3]:
    print(' ', str(w).strip()[:100])
