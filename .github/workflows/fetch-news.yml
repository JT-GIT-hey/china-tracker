#!/usr/bin/env python3
"""
China News Tracker — News Fetcher
Uses GDELT API (no key needed) + RSS feeds to populate data/news.json
Run locally or via GitHub Actions on a schedule.
"""

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from urllib.parse import urlencode

import feedparser
import requests

# ─────────────────────────────────────────────────────────────
# GDELT CONFIG
# ─────────────────────────────────────────────────────────────
GDELT_BASE = "https://api.gdeltproject.org/api/v2/doc/doc"
TIMESPAN_MINUTES = 10080   # 7 days lookback

# ─────────────────────────────────────────────────────────────
# CATEGORIES — each has GDELT query strings for EN and ZH
# ─────────────────────────────────────────────────────────────
CATEGORIES = {
    "ai_tech": {
        "label": "AI & Technology",
        "icon": "🤖",
        "color": "#a78bfa",
        "featured": True,
        "queries_en": [
            "china artificial intelligence AI deepseek",
            "china AI chip semiconductor nvidia huawei",
            "china tech regulation ByteDance SMIC",
            "china quantum computing robotics",
        ],
        "queries_zh": [
            "中国 人工智能 DeepSeek",
            "中国 芯片 半导体 科技",
        ],
    },
    "foreign_policy": {
        "label": "Foreign Policy & Diplomacy",
        "icon": "🌐",
        "color": "#60a5fa",
        "queries_en": [
            "china foreign policy diplomacy Xi Jinping",
            "china belt road initiative BRI investment",
            "china summit meeting bilateral diplomacy",
        ],
        "queries_zh": [
            "中国 外交 外交政策 习近平",
            "一带一路 外交",
        ],
    },
    "politics": {
        "label": "Politics & Governance",
        "icon": "🏛️",
        "color": "#c084fc",
        "queries_en": [
            "china communist party CCP leadership",
            "china political reform governance policy",
            "china politburo NPC congress",
        ],
        "queries_zh": [
            "中国 共产党 政治 治理",
            "政治局 全国人大",
        ],
    },
    "military_security": {
        "label": "Military & Security",
        "icon": "⚔️",
        "color": "#f87171",
        "queries_en": [
            "china PLA military defense Taiwan strait",
            "china air force navy missile weapon",
            "china military drill exercise",
        ],
        "queries_zh": [
            "中国 解放军 军事 国防",
            "台海 军演 导弹",
        ],
    },
    "economy": {
        "label": "Economy & Trade",
        "icon": "📈",
        "color": "#34d399",
        "queries_en": [
            "china economy GDP trade growth slowdown",
            "china tariffs sanctions trade war US",
            "china yuan renminbi financial markets",
            "china property real estate debt",
        ],
        "queries_zh": [
            "中国 经济 贸易 GDP",
            "人民币 关税 贸易战",
        ],
    },
    "society": {
        "label": "Society & Culture",
        "icon": "👥",
        "color": "#fbbf24",
        "queries_en": [
            "china society culture social media censorship",
            "china human rights dissidents protest",
            "china demographics population birth rate",
        ],
        "queries_zh": [
            "中国 社会 文化 人权",
            "人口 审查 抗议",
        ],
    },
    "maritime_security": {
        "label": "Maritime Security",
        "icon": "⚓",
        "color": "#22d3ee",
        "queries_en": [
            "south china sea maritime dispute islands",
            "china coast guard navy philippines",
            "china Taiwan strait naval",
        ],
        "queries_zh": [
            "南海 争端 海洋安全",
            "中国 海警 菲律宾",
        ],
    },
    "domestic_security": {
        "label": "Domestic Security",
        "icon": "🔒",
        "color": "#fb7185",
        "queries_en": [
            "china surveillance xinjiang tibet security",
            "china police ministry state security",
            "china hong kong national security law",
        ],
        "queries_zh": [
            "中国 新疆 西藏 国内安全",
            "香港 国家安全法 公安",
        ],
    },
    "bilateral_relations": {
        "label": "Bilateral Relations",
        "icon": "🤝",
        "color": "#818cf8",
        "queries_en": [
            "china US relations tensions bilateral",
            "china russia partnership cooperation",
            "china europe EU relations trade",
            "china india japan korea relations",
        ],
        "queries_zh": [
            "中美关系 双边关系",
            "中俄 中欧 中印",
        ],
    },
    "multilateral": {
        "label": "Multilateral & Int'l Orgs",
        "icon": "🏢",
        "color": "#2dd4bf",
        "queries_en": [
            "china UN united nations security council",
            "china WTO WHO SCO BRICS international",
            "china IMF world bank global governance",
        ],
        "queries_zh": [
            "中国 联合国 多边 国际组织",
            "金砖 上合 世贸",
        ],
    },
}

# ─────────────────────────────────────────────────────────────
# RSS FEEDS (no API key needed)
# ─────────────────────────────────────────────────────────────
RSS_FEEDS = [
    # English
    {"url": "https://feeds.reuters.com/reuters/CNTopNews",             "source": "Reuters",         "lang": "en"},
    {"url": "http://feeds.bbci.co.uk/news/world/asia/china/rss.xml",   "source": "BBC",             "lang": "en"},
    {"url": "https://www.globaltimes.cn/rss/outbrain.xml",             "source": "Global Times",    "lang": "en"},
    {"url": "https://www.rfa.org/english/news/china/rss2.xml",         "source": "RFA",             "lang": "en"},
    {"url": "https://thediplomat.com/feed/",                           "source": "The Diplomat",    "lang": "en"},
    {"url": "https://www.cgtn.com/subscribe/rss/section/china.xml",    "source": "CGTN",            "lang": "en"},
    {"url": "https://www.aljazeera.com/xml/rss/all.xml",               "source": "Al Jazeera",      "lang": "en"},
    {"url": "https://foreignpolicy.com/feed/",                         "source": "Foreign Policy",  "lang": "en"},
    {"url": "https://www.scmp.com/rss/4/feed",                         "source": "SCMP",            "lang": "en"},
    {"url": "https://nikkei.com/rss/news.rss",                         "source": "Nikkei Asia",     "lang": "en"},
    # Chinese / Mandarin
    {"url": "http://www.xinhuanet.com/politics/news_politics.xml",     "source": "新华社",           "lang": "zh"},
    {"url": "https://www.caixin.com/rss/2.xml",                        "source": "财新",             "lang": "zh"},
    {"url": "https://www.rfa.org/cantonese/news/rss2.xml",             "source": "自由亚洲",         "lang": "zh"},
    {"url": "https://www.voachinese.com/api/zyvqeoivry",               "source": "美国之音中文",     "lang": "zh"},
    {"url": "https://cn.nytimes.com/rss/news.xml",                     "source": "纽约时报中文",     "lang": "zh"},
]

# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def parse_gdelt_date(s: str) -> str:
    """Convert GDELT '20260320T120000Z' → ISO-8601."""
    try:
        dt = datetime.strptime(s, "%Y%m%dT%H%M%SZ")
        return dt.replace(tzinfo=timezone.utc).isoformat()
    except Exception:
        return s or ""


def parse_struct_time(t) -> str:
    """Convert feedparser time.struct_time → ISO-8601."""
    try:
        dt = datetime(*t[:6], tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception:
        return ""


def strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text or "").strip()


def fetch_gdelt(query: str, language: str = "en", max_records: int = 20) -> list:
    q = query
    if language == "zh":
        q = f"{query} sourcelang:chi"

    params = {
        "query":      q,
        "mode":       "artlist",
        "maxrecords": max_records,
        "format":     "json",
        "TIMESPAN":   TIMESPAN_MINUTES,
        "sort":       "date",
    }
    try:
        r = requests.get(GDELT_BASE, params=params, timeout=30)
        r.raise_for_status()
        data = r.json()
        results = []
        for a in data.get("articles", []):
            results.append({
                "title":     a.get("title", "").strip(),
                "url":       a.get("url", ""),
                "source":    a.get("domain", ""),
                "language":  "zh" if language == "zh" else "en",
                "published": parse_gdelt_date(a.get("seendate", "")),
                "summary":   "",
                "via":       "gdelt",
            })
        return results
    except Exception as e:
        print(f"  [GDELT ERROR] '{query}': {e}", file=sys.stderr)
        return []


def fetch_all_rss() -> list:
    articles = []
    for feed_info in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_info["url"])
            for entry in feed.entries[:20]:
                pub = ""
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub = parse_struct_time(entry.published_parsed)
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    pub = parse_struct_time(entry.updated_parsed)

                summary = strip_html(
                    getattr(entry, "summary", "") or getattr(entry, "description", "")
                )[:400]

                articles.append({
                    "title":     strip_html(entry.get("title", "")),
                    "url":       entry.get("link", ""),
                    "source":    feed_info["source"],
                    "language":  feed_info["lang"],
                    "published": pub,
                    "summary":   summary,
                    "via":       "rss",
                })
            print(f"  [RSS] {feed_info['source']}: {len(feed.entries)} entries")
        except Exception as e:
            print(f"  [RSS ERROR] {feed_info['source']}: {e}", file=sys.stderr)
    return articles


def dedupe(articles: list) -> list:
    seen, out = set(), []
    for a in articles:
        key = a.get("url", "")
        if key and key not in seen:
            seen.add(key)
            out.append(a)
    return out


def sort_articles(articles: list) -> list:
    def sort_key(a):
        return a.get("published", "") or ""
    return sorted(articles, key=sort_key, reverse=True)


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def main():
    print(f"⏱  Fetch started: {datetime.now(timezone.utc).isoformat()}")

    all_categories: dict = {}

    for cat_key, cfg in CATEGORIES.items():
        print(f"\n📂 {cfg['label']}")
        articles = []

        for q in cfg.get("queries_en", []):
            print(f"  → GDELT EN: {q}")
            articles.extend(fetch_gdelt(q, language="en", max_records=15))
            time.sleep(0.8)

        for q in cfg.get("queries_zh", []):
            print(f"  → GDELT ZH: {q}")
            articles.extend(fetch_gdelt(q, language="zh", max_records=10))
            time.sleep(0.8)

        for a in articles:
            a["category"] = cat_key

        articles = dedupe(articles)
        articles = sort_articles(articles)

        all_categories[cat_key] = {
            "label":    cfg["label"],
            "icon":     cfg["icon"],
            "color":    cfg["color"],
            "featured": cfg.get("featured", False),
            "articles": articles[:60],
        }
        print(f"  ✓ {len(articles)} articles")

    print("\n📡 Fetching RSS feeds...")
    rss_articles = fetch_all_rss()
    rss_articles = dedupe(rss_articles)
    rss_articles = sort_articles(rss_articles)

    output = {
        "last_updated":  datetime.now(timezone.utc).isoformat(),
        "categories":    all_categories,
        "latest_rss":    rss_articles[:120],
    }

    os.makedirs("data", exist_ok=True)
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total = sum(len(v["articles"]) for v in all_categories.values())
    print(f"\n✅ Done — {total} categorized articles + {len(rss_articles)} RSS items saved to data/news.json")


if __name__ == "__main__":
    main()
