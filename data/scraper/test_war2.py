import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://statiz.co.kr/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
}

# 스탯티즈 WAR 메인 확인
main_url = 'https://statiz.co.kr/'
resp = requests.get(main_url, headers=headers, timeout=15)
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'lxml')

# WAR TOP 10 테이블 찾기
war_tables = soup.find_all('table')
print(f'메인 페이지 Tables: {len(war_tables)}')
for i, t in enumerate(war_tables):
    text = t.get_text(strip=True)
    if 'WAR' in text or '박성한' in text:
        print(f'\n=== WAR 테이블 {i} ===')
        rows = t.find_all('tr')
        for row in rows[:12]:
            cells = row.find_all(['td','th'])
            print('  ', [c.get_text(strip=True) for c in cells[:10]])

# WAR 섹션 div 찾기
war_divs = soup.find_all(string=lambda s: s and 'WAR' in str(s))
for w in war_divs[:3]:
    parent = w.parent
    print(f'\nWAR element: tag={parent.name}, class={parent.get("class")}')
    # 상위 테이블 찾기
    table = parent.find_parent('table')
    if table:
        rows = table.find_all('tr')
        for row in rows[:12]:
            cells = row.find_all(['td','th'])
            print('  ', [c.get_text(strip=True) for c in cells[:10]])
            links = [a.get('href','') for a in row.find_all('a')]
            if links:
                print('    links:', links[:2])
