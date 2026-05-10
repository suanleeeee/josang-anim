import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://www.koreabaseball.com/'
}

# KBO 공식 타자 기록
url = 'https://www.koreabaseball.com/Record/Player/HitterBasic/Basic1.aspx'
resp = requests.get(url, headers=headers, timeout=15)
print('Status:', resp.status_code, 'Length:', len(resp.text))
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'lxml')

tables = soup.find_all('table')
print(f'Tables: {len(tables)}')
for i, t in enumerate(tables[:2]):
    rows = t.find_all('tr')
    print(f'\nTable {i} ({len(rows)} rows):')
    for row in rows[:5]:
        cells = row.find_all(['td','th'])
        texts = [c.get_text(strip=True) for c in cells]
        print('  ', texts[:15])
        links = [a.get('href','') for a in row.find_all('a') if a.get('href')]
        if links:
            print('  links:', links[:2])

# 투수 기록
url2 = 'https://www.koreabaseball.com/Record/Player/PitcherBasic/Basic1.aspx'
resp2 = requests.get(url2, headers=headers, timeout=15)
print('\n--- 투수 기록 ---')
print('Status:', resp2.status_code, 'Length:', len(resp2.text))
resp2.encoding = 'utf-8'
soup2 = BeautifulSoup(resp2.text, 'lxml')
tables2 = soup2.find_all('table')
print(f'Tables: {len(tables2)}')
for i, t in enumerate(tables2[:1]):
    rows = t.find_all('tr')
    for row in rows[:4]:
        cells = row.find_all(['td','th'])
        print('  ', [c.get_text(strip=True) for c in cells[:15]])
