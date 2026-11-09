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
