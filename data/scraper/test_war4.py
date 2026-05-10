import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://statiz.co.kr/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}

# 응답 내용 직접 확인
url = 'https://statiz.co.kr/stats/?m=main'
resp = requests.get(url, headers=headers, timeout=15)
print('Status:', resp.status_code)
print('Content-Type:', resp.headers.get('Content-Type',''))
print('Redirect history:', [r.url for r in resp.history])
print('Final URL:', resp.url)
print('RAW TEXT:')
print(repr(resp.text[:500]))

# stats 페이지 응답이 JSON인지 확인
print('\n\nJSON 시도:')
try:
    import json
    data = json.loads(resp.text)
    print('JSON 성공:', type(data))
except:
    print('JSON 실패 - HTML/text 응답')
    
# 리다이렉션 확인
print('\n리다이렉션 없이 최종:')
print(resp.text[:300])
