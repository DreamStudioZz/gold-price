"""
品牌金价数据更新脚本
从金价查询网抓取最新品牌金店价格，更新 brand-prices.json
用法: python update_prices.py
"""
import json
import re
import urllib.request
from datetime import date

BASE = "http://www.huangjinjiage.cn"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("utf-8", errors="ignore")

def find_latest_url(html):
    m = re.search(r'href="(/jinjia/\d+/\d+\.html)"', html)
    return BASE + m.group(1) if m else None

def parse_detail(html):
    brands = []
    recovery = {}
    for m in re.finditer(r'<td>([\u4e00-\u9fa5·]{2,8}(?:珠宝|黄金|首饰|金店)?)</td>\s*<td>足金[^<]*</td>\s*<td>(\d+)</td>', html):
        name = m.group(1).strip()
        if name not in [b['name'] for b in brands]:
            brands.append({"name": name, "price": int(m.group(2))})
    for pat, key in [
        (r'黄金回收价格[^\d]*(\d+)', 'gold'),
        (r'铂金回收价格[^\d]*(\d+)', 'platinum'),
        (r'18K金回收价格[^\d]*(\d+)', 'k18'),
        (r'钯金回收价格[^\d]*(\d+)', 'palladium'),
    ]:
        m = re.search(pat, html)
        if m: recovery[key] = int(m.group(1))
    return brands, recovery

html = fetch(BASE)
url = find_latest_url(html)
if not url:
    print("未找到今日详情页链接")
    exit(1)

print(f"抓取: {url}")
detail = fetch(url)
brands, recovery = parse_detail(detail)

if not brands:
    print("未解析到品牌数据")
    exit(1)

data = {
    "date": date.today().isoformat(),
    "source": "金价查询网(huangjinjiage.cn)",
    "unit": "元/克",
    "brands": brands,
    "recovery": recovery
}

import os
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brand-prices.json")
with open(out, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"已更新 {len(brands)} 个品牌 ({data['date']})")
for b in brands:
    print(f"  {b['name']}: {b['price']} 元/克")
