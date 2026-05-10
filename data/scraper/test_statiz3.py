import requests, sys, io
from bs4 import BeautifulSoup
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9',
}

# 기본 스탯티즈 메인 페이지 테스트
url = 'https://statiz.co.kr/'
resp = requests.get(url, headers=headers, timeout=15)
print('Status:', resp.status_code)
print('Length:', len(resp.text))
print('Content-Type:', resp.headers.get('Content-Type',''))
resp.encoding = 'utf-8'
soup = BeautifulSoup(resp.text, 'lxml')
print('Title:', soup.title.get_text(strip=True) if soup.title else 'None')
print('Body text (first 300):', soup.get_text(strip=True)[:300])
