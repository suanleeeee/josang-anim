import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.koreabaseball.com/Player/Register.aspx',
    'Content-Type': 'application/x-www-form-urlencoded'
}

url = 'https://www.koreabaseball.com/Player/Register.aspx'
session = requests.Session()
session.headers.update({'User-Agent': headers['User-Agent']})

# 1단계: GET으로 초기 VIEWSTATE 등 획득
resp = session.get(url, timeout=15)
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'lxml')

viewstate = soup.find('input', {'name': '__VIEWSTATE'})['value']
viewstategen = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})['value']
eventval = soup.find('input', {'name': '__EVENTVALIDATION'})['value']
date_input = soup.find('input', {'name': lambda n: n and 'hfSearchDate' in n})
team_input = soup.find('input', {'name': lambda n: n and 'hfSearchTeam' in n})

date_name = date_input['name']
team_name = team_input['name']
current_date = date_input['value']

print(f'Team input name: {team_name}')
print(f'Date input name: {date_name}')
print(f'Current date: {current_date}')

# ScriptManager 이름 찾기
sm = soup.find('input', {'id': lambda i: i and 'ScriptManager' in str(i)})
print('SM:', sm)

# ScriptManager 헤더로 Ajax 요청 (팀 변경: HT = 기아)
ajax_headers = {
    'User-Agent': headers['User-Agent'],
    'Referer': url,
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'X-MicrosoftAjax': 'Delta=true',
    'X-Requested-With': 'XMLHttpRequest'
}

# UpdatePanel 이름 찾기
update_panels = soup.find_all('div', id=lambda i: i and 'UpdatePanel' in str(i))
for up in update_panels:
    print('UpdatePanel id:', up.get('id'))
