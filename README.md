# 🇨🇳 China Watch — Intelligence Tracker

A self-updating GitHub Pages site that tracks Chinese foreign policy, politics, military, AI, economy, and more — sourced from **English and Mandarin news outlets** using **only free, no-key-required APIs**.

![GitHub Actions](https://img.shields.io/github/actions/workflow/status/YOUR_USERNAME/YOUR_REPO/fetch-news.yml?label=news%20fetch&style=flat-square)

---

## How it works

| Layer | What it does |
|---|---|
| **GDELT API** | Free, no-key global news API covering 100+ languages. Queried per category. |
| **RSS feeds** | 14 feeds from Reuters, BBC, RFA, CGTN, SCMP, 新华社, 财新, 美国之音, and more. |
| **GitHub Actions** | Runs `fetch_news.py` every 3 hours, commits `data/news.json` to the repo. |
| **GitHub Pages** | Serves `index.html` which reads `data/news.json` — zero backend needed. |

No API keys. No database. No server. Just GitHub.

---

## ⚡ Setup (5 minutes)

### 1. Create the repository

```bash
# Option A: use this repo as a template (recommended)
# Click "Use this template" on GitHub

# Option B: create new repo and push files
git init china-watch
cd china-watch
# copy all files in, then:
git add .
git commit -m "init"
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
git push -u origin main
```

### 2. Enable GitHub Pages

1. Go to your repo → **Settings → Pages**
2. Under **Source**, select **Deploy from a branch**
3. Branch: `main`, folder: `/ (root)`
4. Click **Save**

Your site will be live at: `https://YOUR_USERNAME.github.io/YOUR_REPO/`

### 3. Allow Actions to write to the repo

1. Go to **Settings → Actions → General**
2. Scroll to **Workflow permissions**
3. Select **Read and write permissions**
4. Click **Save**

### 4. Trigger the first fetch

Go to **Actions → Fetch China News → Run workflow** to populate data immediately.

After the first run, `data/news.json` will be committed and the site will show live articles.

---

## 📂 File structure

```
.
├── index.html                          # Frontend (GitHub Pages)
├── fetch_news.py                       # News fetcher (GDELT + RSS)
├── requirements.txt                    # Python deps
├── data/
│   └── news.json                       # Auto-updated by Actions
└── .github/
    └── workflows/
        └── fetch-news.yml              # Scheduled workflow (every 3h)
```

---

## 🗂 Tracked categories

| Category | Sources |
|---|---|
| 🤖 **AI & Technology** *(featured)* | GDELT · SCMP Tech · Reuters |
| 🌐 Foreign Policy & Diplomacy | GDELT · Reuters · Foreign Policy |
| 🏛️ Politics & Governance | GDELT · RFA · BBC |
| ⚔️ Military & Security | GDELT · The Diplomat |
| 📈 Economy & Trade | GDELT · Reuters · 财新 |
| 👥 Society & Culture | GDELT · RFA · 美国之音 |
| ⚓ Maritime Security | GDELT · SCMP |
| 🔒 Domestic Security | GDELT · BBC |
| 🤝 Bilateral Relations | GDELT · Reuters |
| 🏢 Multilateral & Int'l Orgs | GDELT · 新华社 |

---

## 🌐 News sources

**English:** Reuters · BBC · Global Times · RFA · The Diplomat · CGTN · Al Jazeera · Foreign Policy · SCMP · Nikkei Asia

**Mandarin (中文):** 新华社 · 财新 · 自由亚洲电台 · 美国之音中文 · 纽约时报中文版

---

## Running locally

```bash
pip install -r requirements.txt
python fetch_news.py
# Opens a browser or run a local server:
python -m http.server 8080
# Visit http://localhost:8080
```

---

## Customising

- **Add categories** — edit `CATEGORIES` dict in `fetch_news.py` and add a nav item in `index.html`
- **Add RSS feeds** — append to `RSS_FEEDS` list in `fetch_news.py`
- **Change fetch frequency** — edit the cron expression in `.github/workflows/fetch-news.yml`
- **More articles per category** — increase `max_records` in GDELT calls or the slice `[:60]` limit

---

## Notes

- GDELT API has a rate limit — the script sleeps 0.8s between queries to stay polite.
- Some RSS feeds may be geo-blocked or intermittently unavailable — the fetcher handles errors gracefully and continues.
- Chinese-language GDELT results use the `sourcelang:chi` filter.
- The site auto-refreshes from `data/news.json` every 15 minutes (client-side) in case the user keeps the tab open.
