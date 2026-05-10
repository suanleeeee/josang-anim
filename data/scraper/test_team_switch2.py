import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

url = 'https://www.koreabaseball.com/Player/Register.aspx'
session = requests.Session()
session.headers.update({
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
})

# GET 초기 요청
resp = session.get(url, timeout=15)
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'lxml')

def get_input(s, name_kw):
    inp = s.find('input', {'name': lambda n: n and name_kw in n})
    return inp['name'], inp.get('value','') if inp else ('', '')

vstate_name, vstate_val = get_input(soup, '__VIEWSTATE')
vstategen_name, vstategen_val = get_input(soup, '__VIEWSTATEGENERATOR')
evval_name, evval_val = get_input(soup, '__EVENTVALIDATION')
team_name, team_val = get_input(soup, 'hfSearchTeam')
date_name, date_val = get_input(soup, 'hfSearchDate')

# ScriptManager 찾기 (span/input 방식)
sm_span = soup.find(lambda tag: tag.name and 'ScriptManager' in str(tag.get('id','')) and tag.name != 'script')
print('SM element:', sm_span)

# 일반 POST (Ajax 없이) - hidden field 변경해서 POST
post_data = {
    '__EVENTTARGET': team_name,
    '__EVENTARGUMENT': '',
    '__VIEWSTATE': vstate_val,
    '__VIEWSTATEGENERATOR': vstategen_val,
    '__EVENTVALIDATION': evval_val,
    team_name: 'HT',  # 기아 타이거즈
    date_name: date_val,
}

resp2 = session.post(url, data=post_data, timeout=15)
resp2.encoding = 'utf-8'
soup2 = BeautifulSoup(resp2.text, 'lxml')

tables2 = soup2.find_all('table', class_='tNData')
print(f'\n기아(HT) 팀 선택 후 Tables found: {len(tables2)}')
for i, t in enumerate(tables2[:5]):
    rows = t.find_all('tr')
    print(f'\n=== Table {i}: {len(rows)} rows ===')
    for row in rows[:4]:
        cells = row.find_all(['td','th'])
        texts = [c.get_text(strip=True) for c in cells]
        print('  ', texts)
