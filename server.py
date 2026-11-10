"""
한국주식 분석기 로컬 서버
실행: python server.py
접속: http://localhost:8080
"""
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.request
import urllib.parse
import os

PORT = int(os.environ.get('PORT', 8181))

class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass  # 로그 조용히

    def do_GET(self):
        # /api/005930.KS?interval=1d&range=6mo  → Yahoo Finance 대리 요청
        if self.path.startswith('/api/'):
            ticker_query = self.path[5:]  # '/api/' 제거
            yf_url = f'https://query1.finance.yahoo.com/v8/finance/chart/{ticker_query}'
            try:
                req = urllib.request.Request(
                    yf_url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json',
                    }
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = resp.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(f'{{"error":"{e}"}}'.encode())

        # /investor/005930 → 네이버 금융 투자자별 매매동향
        elif self.path.startswith('/investor/'):
            import re as _re, json as _json
            code = self.path[10:].split('?')[0].strip()
            if not _re.match(r'^\d{6}$', code):
                self.send_response(400)
                self.send_header('Content-Type','application/json')
                self.send_header('Access-Control-Allow-Origin','*')
                self.end_headers()
                self.wfile.write(b'{"error":"invalid code"}')
                return
            url = f'https://finance.naver.com/item/sise_investor.naver?code={code}'
            try:
                req = urllib.request.Request(url, headers={
                    'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept':'text/html,application/xhtml+xml',
                    'Accept-Language':'ko-KR,ko;q=0.9',
                    'Referer':'https://finance.naver.com/',
                })
                with urllib.request.urlopen(req, timeout=10) as resp:
                    html = resp.read().decode('euc-kr', errors='replace')
                # 첫 번째 날짜 행 파싱
                rows = _re.findall(
                    r'<td[^>]*class="[^"]*date[^"]*"[^>]*>\s*(\d{4}\.\d{2}\.\d{2})\s*</td>(.*?)</tr>',
                    html, _re.DOTALL
                )
                result = {'error': 'no data'}
                if rows:
                    date_str, cells = rows[0]
                    nums = _re.findall(r'[>]\s*([+\-]?[\d,]+)\s*[<]', cells)
                    vals = []
                    for n in nums:
                        n = n.strip()
                        if _re.match(r'^[+\-]?\d[\d,]*$', n):
                            try: vals.append(int(n.replace(',','')))
                            except: pass
                    if len(vals) >= 3:
                        result = {
                            'date': date_str,
                            'individual': vals[0],
                            'foreign': vals[1],
                            'institution': vals[2],
                            'pension': vals[9] if len(vals) > 9 else 0,
                        }
                self.send_response(200)
                self.send_header('Content-Type','application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin','*')
                self.end_headers()
                self.wfile.write(_json.dumps(result, ensure_ascii=False).encode())
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type','application/json')
                self.send_header('Access-Control-Allow-Origin','*')
                self.end_headers()
                self.wfile.write(f'{{"error":"{e}"}}'.encode())

        # /stocks → scan-universe.json 반환
        elif self.path == '/stocks':
            try:
                with open('scan-universe.json', 'rb') as f:
                    data = f.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(f'{{"error":"{e}"}}'.encode())

        # /search/query → Yahoo Finance 종목 검색
        elif self.path.startswith('/search/'):
            raw = self.path[8:]
            query = urllib.parse.unquote(raw.split('?')[0])
            search_url = f'https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(query)}&lang=ko-KR&region=KR&quotesCount=8&newsCount=0'
            try:
                req = urllib.request.Request(
                    search_url,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json',
                    }
                )
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = resp.read()
                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(f'{{"error":"{e}"}}'.encode())

        # 정적 파일 서빙
        else:
            path = self.path.lstrip('/')
            if not path or path == '/':
                path = 'index.html'
            path = path.split('?')[0]
            try:
                with open(path, 'rb') as f:
                    content = f.read()
                ext = path.rsplit('.', 1)[-1].lower()
                ct = {'html':'text/html','js':'application/javascript',
                      'css':'text/css','json':'application/json'}.get(ext,'text/plain')
                self.send_response(200)
                self.send_header('Content-Type', f'{ct}; charset=utf-8')
                self.end_headers()
                self.wfile.write(content)
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()

if __name__ == '__main__':
    import sys
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    httpd = HTTPServer(('0.0.0.0', PORT), Handler)
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    print(f'[OK] Server running -> http://localhost:{PORT}')
    print('   Open the above URL in your browser')
    print('   Stop: Ctrl+C')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped')
