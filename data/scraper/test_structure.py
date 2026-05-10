import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Referer': 'https://www.koreabaseball.com/Player/Register.aspx'
}

url = 'https://www.koreabaseball.com/Player/Register.aspx'
session = requests.Session()
session.headers.update(headers)
resp = session.get(url, timeout=15)
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'lxml')

tables = soup.find_all('table', class_='tNData')
print(f'Tables found: {len(tables)}')

for i, t in enumerate(tables[:8]):
    rows = t.find_all('tr')
    print(f'\n=== Table {i}: {len(rows)} rows ===')
    for row in rows[:5]:
        cells = row.find_all(['td','th'])
        texts = [c.get_text(strip=True) for c in cells]
        print('  ', texts)
