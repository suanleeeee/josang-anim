import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://statiz.co.kr/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}

# 스탯티즈 WAR 전체 랭킹 페이지 탐색
# 메인 페이지 링크에서 stats 관련 URL 찾기
main_url = 'https://statiz.co.kr/'
resp = requests.get(main_url, headers=headers, timeout=15)
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'lxml')

# 모든 링크 수집
all_links = [(a.get_text(strip=True), a.get('href','')) for a in soup.find_all('a', href=True)]
print('Stats/WAR 관련 링크:')
for text, href in all_links:
    if any(kw in href.lower() for kw in ['stats', 'stat', 'war', 'record', 'rank']) or \
       any(kw in text.lower() for kw in ['war', 'stat', '기록', '성적', '순위']):
        print(f'  [{text}] -> {href}')

# 스탯티즈 stats 페이지 접근 시도
test_urls = [
    'https://statiz.co.kr/stats/?m=main',
    'https://statiz.co.kr/stats/?m=main&year=2026',
    'https://statiz.co.kr/stats/?m=main&year=2026&sopt=0',
    'https://statiz.co.kr/stats/?m=main&year=2026&pos=B',
]
for u in test_urls:
    r = requests.get(u, headers=headers, timeout=10)
    soup_t = BeautifulSoup(r.text, 'lxml')
    tbls = soup_t.find_all('table')
    print(f'{u}: status={r.status_code}, len={len(r.text)}, tables={len(tbls)}')
