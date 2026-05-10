import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}

# 스탯티즈 메인에서 링크 모두 수집
url = 'https://statiz.co.kr/'
resp = requests.get(url, headers=headers, timeout=15)
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'lxml')

# stats/ 또는 stat/ 포함 링크 수집
stats_links = [a.get('href','') for a in soup.find_all('a', href=True) 
               if 'stat' in a.get('href','').lower() or 'player' in a.get('href','').lower()]
print('Stats/player links:')
for link in sorted(set(stats_links))[:20]:
    print(' ', link)

# player search form 확인
forms = soup.find_all('form')
print(f'\nForms: {len(forms)}')
for f in forms[:3]:
    print('  action:', f.get('action',''), 'method:', f.get('method',''))
    for inp in f.find_all('input'):
        print('    input:', inp.get('name',''), inp.get('type',''), inp.get('value','')[:20])
