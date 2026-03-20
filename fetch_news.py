#!/usr/bin/env python3
"""
China Watch — News Fetcher v4
GDELT API + 60 RSS feeds → data/news.json
Fixes: language detection, longer summaries, image URLs
"""
import json, os, re, sys, time
from datetime import datetime, timezone
import feedparser, requests

GDELT_BASE       = "https://api.gdeltproject.org/api/v2/doc/doc"
TIMESPAN_MINUTES = 10080  # 7 days

# ── LANGUAGE DETECTION ─────────────────────────────────────
def detect_lang(text, declared="en"):
    """Override declared language if title contains CJK characters."""
    cjk = sum(1 for c in (text or "")
              if '\u4e00' <= c <= '\u9fff' or '\u3400' <= c <= '\u4dbf')
    return "zh" if cjk > 2 else declared

# ── CATEGORIES ────────────────────────────────────────────────
CATEGORIES = {
    "ai_tech": {
        "label": "AI & Technology", "icon": "🤖", "color": "#7d6be8", "featured": True,
        "queries_en": [
            "china artificial intelligence deepseek baidu",
            "china AI chip semiconductor nvidia huawei SMIC",
            "china tech regulation ByteDance Alibaba Tencent",
            "china quantum computing robotics autonomous vehicles",
            "china AI military surveillance facial recognition",
            "china 5G 6G telecom Huawei ZTE standards",
        ],
        "queries_zh": [
            "中国 人工智能 DeepSeek 大模型 文心",
            "中国 芯片 半导体 科技 华为 中芯",
            "中国 量子计算 机器人 自动驾驶",
            "中国 互联网 监管 数据安全 科技巨头",
        ],
    },
    "foreign_policy": {
        "label": "Foreign Policy & Diplomacy", "icon": "🌐", "color": "#4f8de8",
        "queries_en": [
            "china foreign policy diplomacy Xi Jinping",
            "china belt road initiative BRI investment",
            "china summit meeting diplomatic",
            "china soft power global south Africa Latin America",
            "china foreign minister Wang Yi MFA",
        ],
        "queries_zh": [
            "中国 外交 外交政策 习近平",
            "一带一路 外交 全球南方",
            "中国 外交部 王毅 峰会",
            "中国 大使馆 外交关系 双边",
        ],
    },
    "politics": {
        "label": "Politics & Governance", "icon": "🏛️", "color": "#9b6de8",
        "queries_en": [
            "china communist party CCP leadership politburo",
            "china NPC national congress standing committee",
            "china xi jinping power governance",
            "china anti-corruption campaign discipline",
        ],
        "queries_zh": [
            "中国 共产党 政治 治理 习近平",
            "政治局 全国人大 纪检委 反腐",
            "中国 政治改革 党内 权力",
            "中国 领导层 人事 政策",
        ],
    },
    "military_security": {
        "label": "Military & Security", "icon": "⚔️", "color": "#e05f5f",
        "queries_en": [
            "china PLA military Taiwan strait defense",
            "china air force navy missile hypersonic",
            "china military drill exercise",
            "china nuclear weapons arsenal",
            "china cyber warfare espionage hacking APT",
            "china space military satellite",
        ],
        "queries_zh": [
            "中国 解放军 军事 国防 台海",
            "中国 导弹 核武器 军演",
            "中国 航母 海军 歼击机",
            "中国 网络战 太空 军事现代化",
        ],
    },
    "economy": {
        "label": "Economy & Trade", "icon": "📈", "color": "#3dbd86",
        "queries_en": [
            "china economy GDP growth slowdown",
            "china trade tariffs sanctions export controls",
            "china yuan renminbi currency dollar",
            "china property real estate debt crisis",
            "china investment FDI capital outflow",
            "china supply chain decoupling exports",
        ],
        "queries_zh": [
            "中国 经济 GDP 增长 贸易",
            "人民币 关税 贸易战 出口管制",
            "中国 房地产 债务 经济下行",
            "中国 外资 供应链 去全球化",
        ],
    },
    "society": {
        "label": "Society & Culture", "icon": "👥", "color": "#d49040",
        "queries_en": [
            "china society censorship social media propaganda",
            "china human rights dissidents activists",
            "china demographics population aging birth rate",
            "china youth unemployment education",
            "china religion persecution civil society",
        ],
        "queries_zh": [
            "中国 社会 文化 人权 审查",
            "中国 人口 老龄化 生育率",
            "中国 教育 青年 失业 内卷",
            "中国 宗教 女权 维权 NGO",
        ],
    },
    "maritime_security": {
        "label": "Maritime Security", "icon": "⚓", "color": "#3ab8c5",
        "queries_en": [
            "south china sea maritime dispute reef island",
            "china coast guard Philippines Vietnam Indonesia",
            "china Taiwan strait naval warship",
            "china submarine cable maritime militia",
            "china UNCLOS EEZ fishing fleet",
        ],
        "queries_zh": [
            "南海 争端 海洋安全 岛礁 主权",
            "中国 海警 菲律宾 越南 台海",
            "中国 海上民兵 渔船 海洋权益",
            "南海 仲裁 领土主张 海域",
        ],
    },
    "domestic_security": {
        "label": "Domestic Security", "icon": "🔒", "color": "#e07070",
        "queries_en": [
            "china xinjiang uyghur surveillance repression",
            "china tibet crackdown dissent protest",
            "china hong kong national security law arrest",
            "china police state security ministry surveillance",
            "china social credit internet firewall censorship",
        ],
        "queries_zh": [
            "中国 新疆 维吾尔 压制 监控",
            "西藏 香港 国家安全法 逮捕",
            "中国 公安 国安 维稳 镇压",
            "社会信用 防火长城 网络审查",
        ],
    },
    "bilateral_relations": {
        "label": "Bilateral Relations", "icon": "🤝", "color": "#6b7de8",
        "queries_en": [
            "china US relations tensions decoupling",
            "china russia partnership axis",
            "china europe EU Germany France UK",
            "china india border LAC standoff",
            "china japan korea southeast asia",
            "china australia canada sanctions",
        ],
        "queries_zh": [
            "中美关系 中美博弈 脱钩",
            "中俄 伙伴关系 战略合作",
            "中欧 中印 中日 中韩 关系",
            "中国 澳大利亚 英国 加拿大",
        ],
    },
    "multilateral": {
        "label": "Multilateral & Int'l Orgs", "icon": "🏢", "color": "#3ab8a0",
        "queries_en": [
            "china UN security council veto resolution",
            "china WTO WHO trade dispute",
            "china SCO BRICS summit G20",
            "china IMF world bank development",
            "china ASEAN multilateral forum",
        ],
        "queries_zh": [
            "中国 联合国 安理会 否决权",
            "金砖国家 上合组织 多边 国际组织",
            "中国 世贸组织 世卫组织 亚投行",
            "中国 东盟 G20 峰会",
        ],
    },
}

# ── RSS FEEDS ─────────────────────────────────────────────────
RSS_FEEDS = [
    # English wires
    {"url":"https://feeds.reuters.com/reuters/CNTopNews","source":"Reuters","lang":"en","type":"wire"},
    {"url":"http://feeds.bbci.co.uk/news/world/asia/china/rss.xml","source":"BBC News","lang":"en","type":"broadcast"},
    {"url":"https://feeds.apnews.com/rss/apf-intlnews","source":"AP News","lang":"en","type":"wire"},
    {"url":"https://www.aljazeera.com/xml/rss/all.xml","source":"Al Jazeera","lang":"en","type":"broadcast"},
    {"url":"https://www.voanews.com/api/zyvqkpemit","source":"VOA News","lang":"en","type":"broadcast"},
    {"url":"https://www.cgtn.com/subscribe/rss/section/china.xml","source":"CGTN","lang":"en","type":"broadcast"},
    {"url":"https://rss.dw.com/xml/rss-en-world","source":"Deutsche Welle","lang":"en","type":"broadcast"},
    {"url":"https://www.rfa.org/english/news/china/rss2.xml","source":"Radio Free Asia","lang":"en","type":"broadcast"},
    # English newspapers
    {"url":"https://rss.nytimes.com/services/xml/rss/nyt/World.xml","source":"New York Times","lang":"en","type":"newspaper"},
    {"url":"https://feeds.washingtonpost.com/rss/world","source":"Washington Post","lang":"en","type":"newspaper"},
    {"url":"https://www.ft.com/rss/home/international","source":"Financial Times","lang":"en","type":"newspaper"},
    {"url":"https://www.theguardian.com/world/china/rss","source":"The Guardian","lang":"en","type":"newspaper"},
    {"url":"https://www.scmp.com/rss/4/feed","source":"SCMP","lang":"en","type":"newspaper"},
    {"url":"https://asia.nikkei.com/rss/feed/nar","source":"Nikkei Asia","lang":"en","type":"newspaper"},
    {"url":"https://www.globaltimes.cn/rss/outbrain.xml","source":"Global Times","lang":"en","type":"newspaper"},
    # English journals
    {"url":"https://thediplomat.com/feed/","source":"The Diplomat","lang":"en","type":"journal"},
    {"url":"https://foreignpolicy.com/feed/","source":"Foreign Policy","lang":"en","type":"journal"},
    {"url":"https://supchina.com/feed/","source":"SupChina","lang":"en","type":"journal"},
    {"url":"https://thewirechina.com/feed/","source":"The Wire China","lang":"en","type":"journal"},
    {"url":"https://chinadigitaltimes.net/feed/","source":"China Digital Times","lang":"en","type":"journal"},
    {"url":"https://www.asiasentinel.com/feed/","source":"Asia Sentinel","lang":"en","type":"journal"},
    {"url":"https://www.lawfaremedia.org/rss.xml","source":"Lawfare","lang":"en","type":"journal"},
    {"url":"https://www.eastasiaforum.org/feed/","source":"East Asia Forum","lang":"en","type":"journal"},
    {"url":"https://warontherocks.com/feed/","source":"War on the Rocks","lang":"en","type":"journal"},
    # English think tanks
    {"url":"https://www.brookings.edu/feed/","source":"Brookings","lang":"en","type":"thinktank"},
    {"url":"https://www.csis.org/rss.xml","source":"CSIS","lang":"en","type":"thinktank"},
    {"url":"https://www.cfr.org/rss/china","source":"CFR","lang":"en","type":"thinktank"},
    {"url":"https://www.rand.org/feed.xml","source":"RAND","lang":"en","type":"thinktank"},
    {"url":"https://merics.org/en/rss.xml","source":"MERICS","lang":"en","type":"thinktank"},
    {"url":"https://www.lowyinstitute.org/the-interpreter/rss.xml","source":"Lowy Institute","lang":"en","type":"thinktank"},
    {"url":"https://carnegieendowment.org/rss/solr.xml","source":"Carnegie Endowment","lang":"en","type":"thinktank"},
    {"url":"https://www.stimson.org/feed/","source":"Stimson Center","lang":"en","type":"thinktank"},
    {"url":"https://asiasociety.org/rss.xml","source":"Asia Society","lang":"en","type":"thinktank"},
    {"url":"https://jamestown.org/feed/","source":"Jamestown Foundation","lang":"en","type":"thinktank"},
    {"url":"https://chinapower.csis.org/feed/","source":"China Power/CSIS","lang":"en","type":"thinktank"},
    {"url":"https://macropolo.org/feed/","source":"Macro Polo","lang":"en","type":"thinktank"},
    # Chinese state media
    {"url":"http://www.xinhuanet.com/politics/news_politics.xml","source":"新华社","lang":"zh","type":"wire"},
    {"url":"https://www.cna.com.tw/rss/aall.aspx","source":"中央社","lang":"zh","type":"wire"},
    {"url":"http://www.people.com.cn/rss/politics.xml","source":"人民日报","lang":"zh","type":"newspaper"},
    {"url":"https://www.globaltimes.cn/rss/index.xml","source":"环球时报","lang":"zh","type":"newspaper"},
    {"url":"https://www.chinadaily.com.cn/rss/china_rss.xml","source":"中国日报","lang":"zh","type":"newspaper"},
    {"url":"https://www.guancha.cn/rss.xml","source":"观察者网","lang":"zh","type":"newspaper"},
    # Chinese independent / diaspora
    {"url":"https://www.caixin.com/rss/2.xml","source":"财新","lang":"zh","type":"newspaper"},
    {"url":"https://theinitium.com/feed/","source":"端传媒","lang":"zh","type":"journal"},
    {"url":"https://www.hk01.com/rss/article","source":"香港01","lang":"zh","type":"newspaper"},
    {"url":"https://www.zaobao.com.sg/rss/china","source":"联合早报","lang":"zh","type":"newspaper"},
    {"url":"https://news.mingpao.com/rss/pns/s00002.xml","source":"明报","lang":"zh","type":"newspaper"},
    {"url":"https://d.duowei.com/rss","source":"多维新闻","lang":"zh","type":"newspaper"},
    {"url":"https://www.epochtimes.com/gb/rss/china.xml","source":"大纪元中文","lang":"zh","type":"newspaper"},
    {"url":"https://udn.com/rssfeed/news/2/CNN?ch=news","source":"联合新闻网","lang":"zh","type":"newspaper"},
    {"url":"https://www.storm.mg/rss","source":"风传媒","lang":"zh","type":"newspaper"},
    # Chinese int'l broadcasters
    {"url":"https://www.rfa.org/cantonese/news/rss2.xml","source":"自由亚洲","lang":"zh","type":"broadcast"},
    {"url":"https://www.voachinese.com/api/zyvqeoivry","source":"美国之音中文","lang":"zh","type":"broadcast"},
    {"url":"https://www.bbc.com/zhongwen/simp/index.xml","source":"BBC中文","lang":"zh","type":"broadcast"},
    {"url":"https://www.dw.com/zh/rss","source":"德国之声中文","lang":"zh","type":"broadcast"},
    {"url":"https://www.rfi.fr/cn/rss","source":"法广中文","lang":"zh","type":"broadcast"},
    {"url":"https://www.ntdtv.com/gb/rss/china-news.xml","source":"新唐人","lang":"zh","type":"broadcast"},
    {"url":"https://cn.nytimes.com/rss/news.xml","source":"纽约时报中文","lang":"zh","type":"newspaper"},
    # Chinese portals
    {"url":"https://news.ifeng.com/rss/index.xml","source":"凤凰网","lang":"zh","type":"portal"},
    {"url":"https://www.163.com/rss/news.xml","source":"网易新闻","lang":"zh","type":"portal"},
]

# ── HELPERS ────────────────────────────────────────────────────
def strip_html(text):
    return re.sub(r"<[^>]+>", "", text or "").strip()

def parse_gdelt_date(s):
    try:
        return datetime.strptime(s, "%Y%m%dT%H%M%SZ").replace(tzinfo=timezone.utc).isoformat()
    except Exception:
        return s or ""

def parse_struct_time(t):
    try:
        return datetime(*t[:6], tzinfo=timezone.utc).isoformat()
    except Exception:
        return ""

def get_image(entry):
    """Try to extract thumbnail image URL from RSS entry."""
    for attr in ["media_thumbnail", "media_content"]:
        media = getattr(entry, attr, None)
        if media and isinstance(media, list):
            url = media[0].get("url", "")
            if url:
                return url
    # Try enclosures
    for enc in getattr(entry, "enclosures", []):
        if enc.get("type", "").startswith("image"):
            return enc.get("url", "")
    return ""

def get_summary(entry):
    """Extract best available summary text, up to 1000 chars."""
    # Try full content first (some feeds include full articles)
    if hasattr(entry, "content") and entry.content:
        full = strip_html(entry.content[0].get("value", ""))
        if len(full) > 100:
            return full[:1000]
    # Fall back to summary/description
    raw = getattr(entry, "summary", "") or getattr(entry, "description", "")
    return strip_html(raw)[:1000]

def fetch_gdelt(query, language="en", max_records=15):
    q = f"{query} sourcelang:chi" if language == "zh" else query
    params = {"query": q, "mode": "artlist", "maxrecords": max_records,
              "format": "json", "TIMESPAN": TIMESPAN_MINUTES, "sort": "date"}
    try:
        r = requests.get(GDELT_BASE, params=params, timeout=30)
        r.raise_for_status()
        articles = []
        for a in r.json().get("articles", []):
            title = a.get("title", "").strip()
            lang = detect_lang(title, "zh" if language == "zh" else "en")
            articles.append({
                "title":     title,
                "url":       a.get("url", ""),
                "source":    a.get("domain", ""),
                "language":  lang,
                "type":      "wire",
                "published": parse_gdelt_date(a.get("seendate", "")),
                "summary":   "",
                "image":     "",
                "via":       "gdelt",
            })
        return articles
    except Exception as e:
        print(f"  [GDELT ✗] {query}: {e}", file=sys.stderr)
        return []

def fetch_rss(feed_info):
    try:
        feed = feedparser.parse(feed_info["url"])
        articles = []
        for entry in feed.entries[:25]:
            pub = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                pub = parse_struct_time(entry.published_parsed)
            elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                pub = parse_struct_time(entry.updated_parsed)

            title = strip_html(entry.get("title", "")).strip()
            if not title:
                continue

            summary = get_summary(entry)
            image   = get_image(entry)
            # Fix language based on actual content
            lang = detect_lang(title, feed_info["lang"])

            articles.append({
                "title":     title,
                "url":       entry.get("link", ""),
                "source":    feed_info["source"],
                "language":  lang,
                "type":      feed_info.get("type", ""),
                "published": pub,
                "summary":   summary,
                "image":     image,
                "via":       "rss",
            })
        print(f"  [RSS ✓] {feed_info['source']:24s} {len(articles):3d} articles")
        return articles
    except Exception as e:
        print(f"  [RSS ✗] {feed_info['source']:24s} {e}", file=sys.stderr)
        return []

def dedupe(articles):
    seen, out = set(), []
    for a in articles:
        k = a.get("url", "")
        if k and k not in seen:
            seen.add(k); out.append(a)
    return out

def sort_by_date(articles):
    return sorted(articles, key=lambda a: a.get("published", "") or "", reverse=True)

# ── MAIN ───────────────────────────────────────────────────────
def main():
    print(f"\n⏱  Started: {datetime.now(timezone.utc).isoformat()}")

    en_feeds = [f for f in RSS_FEEDS if f["lang"] == "en"]
    zh_feeds = [f for f in RSS_FEEDS if f["lang"] == "zh"]
    print(f"\n📡 RSS: {len(en_feeds)} EN + {len(zh_feeds)} ZH feeds")

    all_rss = []
    for fi in RSS_FEEDS:
        all_rss.extend(fetch_rss(fi))
        time.sleep(0.3)
    all_rss = sort_by_date(dedupe(all_rss))
    print(f"  → {len(all_rss)} unique RSS articles")

    print("\n📂 GDELT by category…")
    all_cats = {}
    for key, cfg in CATEGORIES.items():
        print(f"\n  [{cfg['label']}]")
        arts = []
        for q in cfg.get("queries_en", []):
            arts.extend(fetch_gdelt(q, "en", 15)); time.sleep(0.8)
        for q in cfg.get("queries_zh", []):
            arts.extend(fetch_gdelt(q, "zh", 10)); time.sleep(0.8)
        for a in arts:
            a["category"] = key
        arts = sort_by_date(dedupe(arts))
        all_cats[key] = {
            "label": cfg["label"], "icon": cfg["icon"],
            "color": cfg["color"], "featured": cfg.get("featured", False),
            "articles": arts[:80],
        }
        print(f"  → {len(arts)} articles")

    output = {
        "last_updated":  datetime.now(timezone.utc).isoformat(),
        "source_counts": {"en": len(en_feeds), "zh": len(zh_feeds)},
        "categories":    all_cats,
        "latest_rss":    all_rss[:200],
    }
    os.makedirs("data", exist_ok=True)
    with open("data/news.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    total = sum(len(v["articles"]) for v in all_cats.values())
    print(f"\n✅ Done — {total} categorised + {len(all_rss)} RSS → data/news.json")

if __name__ == "__main__":
    main()
