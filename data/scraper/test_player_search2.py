import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://www.koreabaseball.com/'
}

# KBO 선수조회 - 팀별 필터 POST 방식 확인
url = 'https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx'
resp = requests.get(url, headers=headers, timeout=15)
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'lxml')

# 팀 선택 select 태그 찾기
selects = soup.find_all('select')
for sel in selects:
    print(f'select id={sel.get("id")}, name={sel.get("name")}')
    for opt in sel.find_all('option'):
        print(f'  value={opt.get("value")}, text={opt.get_text(strip=True)}')

# 투수 기록 페이지 동일 구조
url_pitch = 'https://www.koreabaseball.com/Record/Player/PitcherBasic/Basic1.aspx'
resp_p = requests.get(url_pitch, headers=headers, timeout=15)
resp_p.encoding = 'utf-8'
soup_p = BeautifulSoup(resp_p.text, 'lxml')
selects_p = soup_p.find_all('select')
print('\n--- 투수 페이지 selects ---')
for sel in selects_p:
    print(f'select id={sel.get("id")}, name={sel.get("name")}')
    for opt in sel.find_all('option'):
        print(f'  value={opt.get("value")}, text={opt.get_text(strip=True)}')
