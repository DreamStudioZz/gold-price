"""
Gold Price Monitor — Server
Data: Sina Finance (real-time spot) + MintedMetal (rhodium fallback)
"""
import http.server
import json
import os
import re
import ssl
import threading
import time
import urllib.request

PORT = int(os.environ.get("PORT", 8088))
HOST = os.environ.get("HOST", "0.0.0.0")
DIR = os.path.dirname(os.path.abspath(__file__))
BRANDS_FILE = os.path.join(DIR, "brand-prices.json")

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

URL_SINA = "http://hq.sinajs.cn/list=hf_XAU,hf_XAG,hf_XPT,hf_XPD"
URL_FX = "https://cdn.jsdelivr.net/npm/@fawazahmed0/currency-api@latest/v1/currencies/usd.json"
URL_RHODIUM = "https://mintedmetal.com/api/prices.json"

HEADERS_SINA = {"User-Agent": "Mozilla/5.0", "Referer": "https://finance.sina.com.cn/"}
HEADERS_JSON = {"User-Agent": "Mozilla/5.0"}

cache = {}


def fetch_text(url, headers, decode="utf-8", ssl_ctx=None):
    req = urllib.request.Request(url, headers=headers)
    ctx = {"context": ssl_ctx} if ssl_ctx else {}
    with urllib.request.urlopen(req, timeout=10, **ctx) as r:
        return r.read().decode(decode, errors="ignore")


def safe_float(s):
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


def update_prices():
    global cache
    while True:
        try:
            # parallel: FX + Sina + Rhodium
            rate = 6.80
            try:
                fx = json.loads(fetch_text(URL_FX, HEADERS_JSON, ssl_ctx=SSL_CTX))
                rate = fx.get("usd", {}).get("cny", rate)
            except Exception:
                pass

            data = fetch_text(URL_SINA, HEADERS_SINA, decode="gbk")
            gold = silver = platinum = palladium = None

            for line in data.strip().split("\n"):
                m = re.search(r'hf_(\w+)="([^"]*)"', line)
                if not m:
                    continue
                code, vals = m.group(1), m.group(2).split(",")
                if len(vals) < 14:
                    continue

                price = safe_float(vals[0])
                prev_close = safe_float(vals[1])
                if prev_close is None and len(vals) > 7:
                    prev_close = safe_float(vals[7])
                if price is None or prev_close is None:
                    continue

                chg = price - prev_close
                chg_pct = round(chg / prev_close * 100, 2)
                item = {
                    "price": price,
                    "change": round(chg, 2),
                    "change_pct": chg_pct,
                    "cny_per_gram": round(price * rate / 31.1035, 1),
                    "cny_per_ounce": round(price * rate, 1),
                }

                if code == "XAU":
                    gold = item
                elif code == "XAG":
                    silver = item
                elif code == "XPT":
                    platinum = item
                elif code == "XPD":
                    palladium = item

            # rhodium (daily fix from mintedmetal)
            rhodium = None
            try:
                mr = json.loads(fetch_text(URL_RHODIUM, HEADERS_JSON, ssl_ctx=SSL_CTX))
                rh = mr.get("metals", {}).get("rhodium", {})
                if rh.get("price"):
                    rhodium = {"price": rh["price"], "unit": "USD/oz"}
            except Exception:
                pass

            # recovery prices: gold = live - 10, others from live spot
            recovery = {}
            if gold:
                gr = gold["cny_per_gram"]
                recovery["gold"] = round(gr - 10, 1)
                recovery["k18"] = round((gr - 10) * 0.75, 1)
            if platinum:
                recovery["platinum"] = round(platinum["cny_per_gram"], 1)
            if palladium:
                recovery["palladium"] = round(palladium["cny_per_gram"], 1)

            cache = {
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "rate": round(rate, 4),
                "gold": gold,
                "silver": silver,
                "platinum": platinum,
                "palladium": palladium,
                "rhodium": rhodium,
                "recovery": recovery,
            }
            print(f"[{cache['time']}] XAU={gold['price'] if gold else 'N/A'} | "
                  f"CNY={gold['cny_per_gram'] if gold else 'N/A'}元/克 | rate={rate:.4f}")

        except Exception as e:
            print(f"update error: {e}")
        time.sleep(30)


class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/live":
            self._json(cache)
        elif self.path == "/api/brands":
            try:
                with open(BRANDS_FILE, encoding="utf-8") as f:
                    self._json(json.load(f))
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
        else:
            super().do_GET()

    def _json(self, data):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIR, **kwargs)

    def log_message(self, fmt, *args):
        pass


if __name__ == "__main__":
    threading.Thread(target=update_prices, daemon=True).start()
    print(f"Gold Price Monitor → http://{HOST}:{PORT}")
    http.server.HTTPServer((HOST, PORT), Handler).serve_forever()
