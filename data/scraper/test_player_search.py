import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://www.koreabaseball.com/'
}

# KBO 타자 전체 목록 (페이지별)
url = 'https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx'
resp = requests.get(url, headers=headers, timeout=15)
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'lxml')

# 페이지네이션 확인
pager = soup.find(class_=lambda c: c and 'pager' in str(c).lower())
print('Pager:', pager.get_text(strip=True)[:200] if pager else 'None')

# 총 데이터 건수
total_info = soup.find(class_=lambda c: c and ('total' in str(c).lower() or 'count' in str(c).lower()))
print('Total info:', total_info.get_text(strip=True)[:100] if total_info else 'None')

# 선수 목록 파싱
table = soup.find('table')
rows = table.find_all('tr')
print(f'\n총 선수 수 (현재 페이지): {len(rows)-1}')
print('헤더:', [th.get_text(strip=True) for th in rows[0].find_all(['th','td'])])

# 선수 데이터와 playerId 수집
players = []
for row in rows[1:]:
    cells = row.find_all(['td','th'])
    link = row.find('a', href=True)
    if link and 'playerId=' in link.get('href',''):
        player_id = link.get('href','').split('playerId=')[-1]
        player_name = link.get_text(strip=True)
        team = cells[2].get_text(strip=True) if len(cells) > 2 else ''
        players.append({'id': player_id, 'name': player_name, 'team': team})

print(f'\n파싱된 선수 수: {len(players)}')
for p in players[:5]:
    print(' ', p)

# 페이지 2 확인 (POST)
viewstate = soup.find('input', {'name': '__VIEWSTATE'})
viewstategen = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
eventval = soup.find('input', {'name': '__EVENTVALIDATION'})

if viewstate:
    post_data = {
        '__EVENTTARGET': 'ctl00$ctl00$ctl00$cphContents$cphContents$cphContents$ucPager$btnNo2',
        '__EVENTARGUMENT': '',
        '__VIEWSTATE': viewstate['value'],
        '__VIEWSTATEGENERATOR': viewstategen['value'],
        '__EVENTVALIDATION': eventval['value'],
    }
    resp2 = requests.post(url, headers={**headers, 'Content-Type': 'application/x-www-form-urlencoded'}, data=post_data, timeout=15)
    resp2.encoding = 'utf-8'
    soup2 = BeautifulSoup(resp2.text, 'lxml')
    table2 = soup2.find('table')
    if table2:
        rows2 = table2.find_all('tr')
        print(f'\n페이지 2 선수 수: {len(rows2)-1}')
        for row in rows2[1:3]:
            cells = row.find_all(['td'])
            link = row.find('a', href=True)
            if link:
                print(' ', link.get_text(strip=True), link.get('href','').split('playerId=')[-1])
