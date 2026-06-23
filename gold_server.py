"""
实时金价监控服务器
数据源: 新浪财经 (hq.sinajs.cn) — 实时现货价格
启动: python gold_server.py
访问: http://localhost:8088
"""
import http.server
import json
import re
import ssl
import threading
import time
import urllib.request
import os

PORT = 8088
DIR = os.path.dirname(os.path.abspath(__file__))
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

HEADERS_SINA = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
HEADERS_WEB = {"User-Agent": "Mozilla/5.0"}

url_sina = "http://hq.sinajs.cn/list=hf_XAU,hf_XAG,hf_XPT,hf_XPD"
url_fx = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json"

cache = {}

def fetch_text(url, headers, decode="utf-8", use_ssl=False):
    req = urllib.request.Request(url, headers=headers)
    kwargs = {"timeout": 10}
    if use_ssl:
        kwargs["context"] = SSL_CTX
    with urllib.request.urlopen(req, **kwargs) as r:
        raw = r.read()
        return raw.decode(decode, errors="ignore")

def safe_float(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return None

def update_prices():
    global cache
    while True:
        new_cache = {}
        try:
            # 汇率
            try:
                fx_data = json.loads(fetch_text(url_fx, HEADERS_WEB, use_ssl=True))
                rate = fx_data.get("usd", {}).get("cny")
                if rate:
                    new_cache["rate"] = rate
            except Exception as e:
                print(f"汇率失败: {e}")

            rate = new_cache.get("rate", 6.78)

            # 实时价格
            data = fetch_text(url_sina, HEADERS_SINA, decode="gbk")
            for line in data.strip().split("\n"):
                line = line.strip()
                if not line:
                    continue
                m = re.search(r"hf_(\w+)=", line)
                if not m:
                    continue
                code = m.group(1)
                q1 = line.find('"') + 1
                q2 = line.rfind('"')
                vals = line[q1:q2].split(",")
                if len(vals) < 14:
                    continue

                price = safe_float(vals[0])
                prev_close = safe_float(vals[1])
                if prev_close is None and len(vals) > 7:
                    # 纽约铂金/钯金昨收为空，用昨收2 (vals[7])
                    prev_close = safe_float(vals[7])
                if price is None:
                    continue
                chg_pct = round((price - prev_close) / prev_close * 100, 2) if prev_close else None
                cny = round(price * rate / 31.1035, 1)

                key_map = {"XAU": "gold", "XAG": "silver", "XPT": "platinum", "XPD": "palladium"}
                key = key_map.get(code)
                if key:
                    new_cache[key] = price
                    new_cache[f"{key}_chg"] = chg_pct
                    new_cache[f"cny_{key}"] = cny

            new_cache["time"] = time.strftime("%H:%M:%S")
            cache = new_cache
            print(f"[{cache['time']}] 黄金={cache.get('gold')} USD/oz | "
                  f"国内={cache.get('cny_gold')}元/克 | 汇率={cache.get('rate')}")
        except Exception as e:
            print(f"更新失败: {e}")
        time.sleep(30)

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/live":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(cache, ensure_ascii=False).encode())
        elif self.path == "/api/brands":
            for fname in os.listdir(DIR):
                if fname.startswith("brand-prices") and fname.endswith(".json"):
                    with open(os.path.join(DIR, fname), encoding="utf-8") as f:
                        data = json.load(f)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
                    return
            self.send_response(404)
            self.end_headers()
        else:
            super().do_GET()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    threading.Thread(target=update_prices, daemon=True).start()
    print(f"金价监控服务已启动: http://localhost:{PORT}")
    print("数据源: 新浪财经实时行情 | 按 Ctrl+C 停止")
    http.server.HTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
