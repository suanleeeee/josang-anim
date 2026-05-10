import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}

# 스탯티즈 시즌 타자 성적 페이지
url = 'https://statiz.co.kr/stat/?opt=1&sopt=0&year=2026&ctype=0&cId=&pCode=1&pos=B&sy=2026&ey=2026&m=1&m2=1'
resp = requests.get(url, headers=headers, timeout=15)
print('Status:', resp.status_code)
print('Length:', len(resp.text))
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'lxml')
print('Title:', soup.title.get_text(strip=True) if soup.title else 'None')

tables = soup.find_all('table')
print(f'Tables: {len(tables)}')

# WAR 찾기
war_els = soup.find_all(string=lambda s: s and 'WAR' in str(s))
print(f'WAR mentions: {len(war_els)}')

# 실제 선수 데이터 링크 찾기
player_links = [a for a in soup.find_all('a', href=True) if 'playerinfo' in a.get('href','') or 'p_no=' in a.get('href','')]
print(f'Player links: {len(player_links)}')
for pl in player_links[:5]:
    print('  ', pl.get('href'), pl.get_text(strip=True))

# stat 페이지 (www 없이)
url2 = 'https://statiz.co.kr/stat/?opt=1&sopt=0'
resp2 = requests.get(url2, headers=headers, timeout=15)
print('\nStat page status:', resp2.status_code, 'Length:', len(resp2.text))
resp2.encoding = 'utf-8'
soup2 = BeautifulSoup(resp2.text, 'lxml')
tables2 = soup2.find_all('table')
print(f'Tables: {len(tables2)}')
if tables2:
    rows = tables2[0].find_all('tr')
    for row in rows[:3]:
        cells = row.find_all(['td','th'])
        print('  ', [c.get_text(strip=True) for c in cells[:12]])
