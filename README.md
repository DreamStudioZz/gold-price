---
AIGC:
    Label: "1"
    ContentProducer: 001191440300708461136T1XGW3
    ProduceID: 6bf52cad6a5605a9eb9f717fe33203de_0e97223f6f6211f1aefd5254006c9bbf
    ReservedCode1: QUehKX7yAtsZsaVql0YmIA4OZoyDDYcCYLRYP38art6xBczalbXN+HBwidIg/Aqm3xEq72w4Gg48123ypgbGSUMoSvdOQl2ohhm4xsLJ6YZnruR9tXQD3wvk9Njydj41KhOpc5nwM4UJAz7TeBNFSSqJI63pvaW/N3vP+C2Tf3C3mwzr8FVcUltAF0o=
    ContentPropagator: 001191440300708461136T1XGW3
    PropagateID: 6bf52cad6a5605a9eb9f717fe33203de_0e97223f6f6211f1aefd5254006c9bbf
    ReservedCode2: QUehKX7yAtsZsaVql0YmIA4OZoyDDYcCYLRYP38art6xBczalbXN+HBwidIg/Aqm3xEq72w4Gg48123ypgbGSUMoSvdOQl2ohhm4xsLJ6YZnruR9tXQD3wvk9Njydj41KhOpc5nwM4UJAz7TeBNFSSqJI63pvaW/N3vP+C2Tf3C3mwzr8FVcUltAF0o=
---

# Gold Price Monitor · 实时金价监控

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker)](https://docs.docker.com)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

基于新浪财经实时行情的国际贵金属价格监控面板。支持黄金、白银、铂金、钯金、铑价格展示，含品牌金店足金报价和回收参考价。

**数据源**：新浪财经 `hq.sinajs.cn`（实时现货）+ MintedMetal（铑日定盘价）+ jsDelivr CDN 汇率

---

## 功能

| 模块 | 内容 |
|------|------|
| 国际金价 | XAU/USD 实时报价、涨跌额、涨跌幅 |
| 人民币估算 | 按实时汇率换算 元/克、元/盎司 |
| 贵金属面板 | 白银 XAG、铂金 XPT、钯金 XPD、铑 |
| 品牌金价 | 周大福/老凤祥/菜百等 9 大品牌足金价格 |
| 回收参考 | 黄金/铂金/18K/钯金回收价 |

---

## 项目结构

```
gold-price/
├── server.py          # Python 后端，获取行情 + 静态文件服务
├── index.html         # 前端页面（深色交易终端风格）
├── brand-prices.json  # 品牌金价数据
├── update_prices.py   # 品牌金价爬虫（手动执行：python update_prices.py）
├── Dockerfile
├── docker-compose.yml
├── requirements.txt   # 空（Python 标准库即可运行）
├── run.bat / run.sh   # 一键启动脚本
└── README.md
```

---

## 部署方式

### 方式一：本机直接运行

**要求**：Python 3.10+

```bash
# 启动
python server.py

# 浏览器访问
# http://localhost:8088
```

Windows 双击 `run.bat` 即可。

### 方式二：Docker

```bash
# 构建 + 启动
docker compose up -d

# 或手动构建
docker build -t gold-price .
docker run -d -p 8088:8088 gold-price
```

访问 `http://localhost:8088`

---

## API

| 端点 | 说明 |
|------|------|
| `GET /` | 前端页面 |
| `GET /api/live` | 实时贵金属行情 JSON |
| `GET /api/brands` | 品牌金价 JSON |

### `/api/live` 响应示例

```json
{
  "time": "2026-06-24 19:30:00",
  "rate": 7.1234,
  "gold": {
    "price": 4128.50,
    "change": -63.15,
    "change_pct": -1.51,
    "cny_per_gram": 910.5,
    "cny_per_ounce": 29400.3
  },
  "silver": { ... },
  "platinum": { ... },
  "palladium": { ... },
  "rhodium": { "price": 7900, "unit": "USD/oz" }
}
```

---

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PORT` | `8088` | 服务端口 |
| `HOST` | `0.0.0.0` | 绑定地址 |

---

## 品牌金价更新

品牌金价**不会自动刷新**。品牌（周大福/老凤祥等）调价频率低，通常数日甚至一周才变一次。按需手动执行：

```bash
python update_prices.py
```

脚本从金价查询网抓取最新数据并覆盖 `brand-prices.json`。也可以加到 cron / 计划任务中每周执行一次。

---

## 注意事项

- 铑无 24h 电子交易市场，数据来自 Umicore/Johnson Matthey 日定盘价
- 行情每 30 秒自动刷新，页面也每 30 秒轮询

---

## License

MIT
*（内容由AI生成，仅供参考）*
