"""
品牌金价数据更新脚本
从 pinpaijinjia.html（品牌金价汇总页）抓取最新价格，更新 brand-prices.json
用法: python update_prices.py
"""
import json
import re
import urllib.request
from datetime import date
import os

URL = "http://www.huangjinjiage.cn/pinpaijinjia.html"
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}


def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        return r.read().decode("gbk", errors="ignore")


def parse(html):
    brands = []
    seen = set()

    # 品牌金价：品牌名 | 黄金价格/足金xxx | 价格元/克（排除回收价行）
    for m in re.finditer(
        r'<td>([^<]+)</td>\s*'
        r'<td>(?!.*回收)(?:黄金价格|足金[^<]*)</td>\s*'
        r'<td>(\d+)元/克</td>',
        html,
    ):
        name = m.group(1).strip()
        price = int(m.group(2))
        if name != "水贝黄金" and name not in seen:
            seen.add(name)
            brands.append({"name": name, "price": price})

    # 投资金条
    inv = re.search(r'金条价格</td>\s*<td>(\d+)元/克</td>', html)
    if inv:
        brands.append({"name": "投资金条", "price": int(inv.group(1))})

    # 回收价
    recovery = {}
    name_map = {"黄金": "gold", "铂金": "platinum", "18K金": "k18", "钯金": "palladium"}
    for m in re.finditer(
        r'<td>([^<]*)回收价格</td>\s*<td>(\d+)元/克</td>',
        html,
    ):
        key = re.sub(r"<[^>]+>", "", m.group(1)).strip()
        if key in name_map:
            recovery[name_map[key]] = int(m.group(2))

    return brands, recovery


def main():
    html = fetch(URL)
    date_match = re.search(r"(\d{4})年(\d{2})月(\d{2})日", html)
    page_date = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}" if date_match else "未知"

    brands, recovery = parse(html)

    if not brands:
        print(f"未解析到品牌数据 (页面日期: {page_date})")
        return

    data = {
        "date": date.today().isoformat(),
        "source": "金价查询网(huangjinjiage.cn)",
        "unit": "元/克",
        "brands": brands,
        "recovery": recovery,
    }

    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "brand-prices.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"已更新 {len(brands)} 个品牌, {len(recovery)} 种回收价 ({data['date']})")
    for b in brands:
        print(f"  {b['name']}: {b['price']} 元/克")
    for k, v in recovery.items():
        print(f"  回收 {k}: {v} 元/克")


if __name__ == "__main__":
    main()
