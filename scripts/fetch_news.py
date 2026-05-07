"""
French Cloud Computing News Tracker
Fetches news from Google News RSS feeds and generates a self-contained HTML dashboard.
"""
import hashlib
import html
import json
import os
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

import feedparser
from dateutil import parser as dateparser

from config import (
    QUERIES, CATEGORY_LABELS, PROVIDER_COLORS,
    IMPORTANCE_LABELS, IMPORTANCE_STARS, IMPORTANCE_COLORS,
    EVENT_TYPES, build_rss_url,
)


# ── Classification helpers (v2) ──

# Keyword sets for importance classification
HIGH_KEYWORDS = [
    "annonce", "lancement", "nouveau service", "nouvelle région",
    "acquisition", "fusion", "rachat",
    "investissement", "milliard", "million d'euros",
    "partenariat stratégique", "alliance stratégique",
    "ouverture", "inaugure", "révolutionnaire",
    "secnumcloud", "qualifié", "certifié",
    "premier", "première", "inédit",
]

MEDIUM_KEYWORDS = [
    "partenariat", "collaboration", "croissance",
    "extension", "certification", "recrute", "nomination",
    "nouveau", "nouvelle", "lance",
]

# Keyword sets for event type classification (checked in order)
EVENT_PATTERNS = [
    ("product", [
        "lancement", "nouveau service", "nouvelle offre", "nouvelle fonctionnalité",
        "sortie", "dévoile", "disponible", "présentation",
        "nouvelle version", "introduit", "annonce le lancement",
    ]),
    ("partnership", [
        "partenariat", "collaboration", "alliance", "signé", "contrat",
        "client", "accord", "consortium", "signature", "s'associe",
    ]),
    ("ma_finance", [
        "acquisition", "fusion", "rachat", "levée de fonds",
        "investissement", "financement", "licenciement", "suppression d'emploi",
        "restructuration", "nomination", "recrute", "recrutement",
        "prise de participation",
    ]),
    ("financial", [
        "chiffre d'affaires", "résultat", "résultats", "croissance",
        "revenu", "bénéfice", "perte", "trimestre", "exercice",
        "résultats financiers", "marge", "rentabilité",
    ]),
    ("policy", [
        "réglementation", "loi", "décret", "anssi", "cnil",
        "secnumcloud", "gouvernement", "certification", "conformité",
        "régulation", "souveraineté", "directive", "règlement",
        "label", "qualification", "ministère",
    ]),
]


def classify_importance(title, summary):
    """Classify article importance based on keyword signals in title + summary."""
    text = (title + " " + summary).lower()

    # Check HIGH keywords first
    for kw in HIGH_KEYWORDS:
        if kw in text:
            return "high"

    # Then MEDIUM
    for kw in MEDIUM_KEYWORDS:
        if kw in text:
            return "medium"

    return "low"


def classify_event_type(title, summary):
    """Classify article event type based on keyword matching."""
    text = (title + " " + summary).lower()

    for event_type, keywords in EVENT_PATTERNS:
        for kw in keywords:
            if kw in text:
                return event_type

    return "general"


# ── Parsing helpers ──

def extract_article(entry, query_config):
    """Convert a feedparser entry into our article dict."""
    title = entry.get("title", "").strip()
    link = entry.get("link", "")
    source = entry.get("source", {}).get("title", "Unknown Source")
    published_str = entry.get("published", "")
    summary_raw = entry.get("summary", entry.get("description", ""))

    # Parse date
    published_dt = None
    if published_str:
        try:
            published_dt = dateparser.parse(published_str)
        except Exception:
            pass

    # Clean summary: strip HTML tags, truncate
    summary = re.sub(r"<[^>]+>", " ", summary_raw)
    summary = re.sub(r"\s+", " ", summary).strip()
    if len(summary) > 250:
        summary = summary[:250].rsplit(" ", 1)[0] + "…"

    # Stable ID from title + source
    id_raw = f"{title}|{source}"
    article_id = hashlib.md5(id_raw.encode("utf-8")).hexdigest()[:12]

    importance = classify_importance(title, summary)
    event_type = classify_event_type(title, summary)

    return {
        "id": article_id,
        "title": title,
        "url": link,
        "source": source,
        "published": published_dt.isoformat() if published_dt else "",
        "published_display": format_date_display(published_dt) if published_dt else "",
        "published_date_short": published_dt.strftime("%Y-%m-%d") if published_dt else "",
        "category": query_config["category"],
        "provider": query_config.get("provider"),
        "summary": summary,
        "importance": importance,
        "importance_stars": IMPORTANCE_STARS[importance],
        "importance_label": IMPORTANCE_LABELS[importance],
        "event_type": event_type,
        "event_type_label": EVENT_TYPES[event_type]["label"],
    }


def format_date_display(dt):
    """Format datetime for display: relative or absolute."""
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = now - dt

    if diff < timedelta(hours=1):
        mins = max(1, int(diff.total_seconds() / 60))
        return f"Il y a {mins} min"
    elif diff < timedelta(hours=24):
        hrs = int(diff.total_seconds() / 3600)
        return f"Il y a {hrs}h"
    elif diff < timedelta(days=7):
        days = diff.days
        return f"Il y a {days}j"
    else:
        return dt.strftime("%Y-%m-%d")


def normalize_title(title):
    """Normalize title for dedup comparison."""
    t = title.lower()
    t = re.sub(r"^exclusif\s*[:：]\s*", "", t)
    t = re.sub(r"^vidéo\s*[:：]\s*", "", t)
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def deduplicate(articles):
    """Two-pass dedup: URL exact match, then normalized title match."""
    seen_urls = set()
    seen_titles = set()
    unique = []

    for a in articles:
        url = a["url"]
        if url in seen_urls:
            continue
        title_norm = normalize_title(a["title"])
        if title_norm in seen_titles:
            continue
        seen_urls.add(url)
        seen_titles.add(title_norm)
        unique.append(a)

    return unique


# ── Main pipeline ──

def fetch_all():
    """Fetch all RSS feeds and return deduplicated, sorted articles."""
    all_articles = []
    total_queries = len(QUERIES)

    for i, q in enumerate(QUERIES):
        url = build_rss_url(q)
        label = q.get("provider") or q["category"]
        print(f"[{i+1}/{total_queries}] Fetching: {label}...", end=" ", flush=True)

        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                print(f"[WARN] error: {feed.bozo_exception}")
                continue

            count = 0
            for entry in feed.entries:
                article = extract_article(entry, q)
                all_articles.append(article)
                count += 1

            print(f"OK ({count} articles)")

        except Exception as e:
            print(f"[FAIL] {e}")

        # Be polite to Google News
        if i < total_queries - 1:
            time.sleep(1.5)

    print(f"\nTotal raw articles: {len(all_articles)}")

    # Deduplicate
    unique = deduplicate(all_articles)
    print(f"After dedup: {len(unique)}")

    # Sort by published date descending
    unique.sort(key=lambda a: a["published"], reverse=True)

    return unique


# ── HTML Generation ──

def escape_for_script(json_str):
    """Escape JSON string for safe embedding in <script> tags."""
    # Prevent </script> from closing the script tag
    return json_str.replace("</", "<\\/")


def generate_html(articles):
    """Generate a complete self-contained HTML dashboard page."""
    generated_at = datetime.now().isoformat()
    articles_json = escape_for_script(json.dumps(articles, ensure_ascii=False))

    # Counts by category
    counts = {"public_cloud": 0, "private_cloud": 0, "policy": 0}
    for a in articles:
        counts[a["category"]] = counts.get(a["category"], 0) + 1

    provider_colors_json = json.dumps(PROVIDER_COLORS, ensure_ascii=False)
    category_labels_json = json.dumps(CATEGORY_LABELS, ensure_ascii=False)
    event_types_json = escape_for_script(json.dumps(EVENT_TYPES, ensure_ascii=False))
    importance_colors_json = json.dumps(IMPORTANCE_COLORS, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>法国云计算市场动态追踪</title>
<style>
/* ── Reset & Variables ── */
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
:root {{
    --bg: #0f172a;
    --bg-card: #1e293b;
    --bg-hover: #273449;
    --text: #e2e8f0;
    --text-secondary: #94a3b8;
    --text-muted: #64748b;
    --border: #334155;
    --accent: #38bdf8;
    --radius: 10px;
    --radius-sm: 6px;
}}
body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Noto Sans SC", sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    min-height: 100vh;
}}

/* ── Header ── */
.header {{
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-bottom: 1px solid var(--border);
    padding: 28px 24px 22px;
    text-align: center;
    position: sticky;
    top: 0;
    z-index: 10;
}}
.header h1 {{
    font-size: 22px;
    font-weight: 700;
    letter-spacing: -0.3px;
    background: linear-gradient(135deg, #38bdf8, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}}
.header .sub {{
    font-size: 13px;
    color: var(--text-muted);
    margin-top: 4px;
}}
.header .refresh-hint {{
    font-size: 11px;
    color: #475569;
    margin-top: 6px;
    font-family: "SF Mono", "Fira Code", monospace;
}}

/* ── Container ── */
.container {{ max-width: 960px; margin: 0 auto; padding: 20px 16px; }}

/* ── Stats Bar ── */
.stats-bar {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-bottom: 18px;
}}
.stat-pill {{
    padding: 7px 16px;
    border-radius: 20px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    border: 2px solid transparent;
    transition: all 0.2s;
    user-select: none;
}}
.stat-pill.public {{ background: rgba(59, 130, 246, 0.18); color: #60a5fa; border-color: rgba(59, 130, 246, 0.35); }}
.stat-pill.private {{ background: rgba(168, 85, 247, 0.18); color: #c084fc; border-color: rgba(168, 85, 247, 0.35); }}
.stat-pill.policy {{ background: rgba(52, 211, 153, 0.18); color: #34d399; border-color: rgba(52, 211, 153, 0.35); }}
.stat-pill:hover {{ filter: brightness(1.2); }}
.stat-pill.active {{ filter: brightness(1.3); box-shadow: 0 0 12px rgba(56, 189, 248, 0.25); }}
.stat-pill.inactive {{ opacity: 0.4; }}

/* ── Date Filter Bar (v2) ── */
.date-filters {{
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-bottom: 12px;
}}
.date-chip {{
    padding: 6px 14px;
    border-radius: 16px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    border: 1.5px solid var(--border);
    background: var(--bg-card);
    color: var(--text-secondary);
    transition: all 0.2s;
    user-select: none;
    white-space: nowrap;
}}
.date-chip:hover {{ border-color: var(--accent); color: var(--text); }}
.date-chip.active {{ background: rgba(56, 189, 248, 0.18); border-color: var(--accent); color: var(--accent); }}

/* ── Event Type Filter Bar (v2) ── */
.event-type-filters {{
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    margin-bottom: 12px;
}}
.event-chip {{
    padding: 5px 12px;
    border-radius: 14px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    border: 1.5px solid transparent;
    transition: all 0.2s;
    user-select: none;
    white-space: nowrap;
}}
.event-chip:hover {{ filter: brightness(1.2); }}
.event-chip.active {{ box-shadow: 0 0 10px rgba(56, 189, 248, 0.3); }}
.event-chip.inactive {{ opacity: 0.3; }}

/* ── Importance Filter (v2) ── */
.importance-filters {{
    display: flex;
    gap: 6px;
    margin-bottom: 12px;
}}
.imp-chip {{
    padding: 4px 10px;
    border-radius: 12px;
    font-size: 11px;
    font-weight: 700;
    cursor: pointer;
    border: 1.5px solid transparent;
    transition: all 0.2s;
    user-select: none;
}}
.imp-chip:hover {{ filter: brightness(1.2); }}
.imp-chip.active {{ box-shadow: 0 0 8px rgba(56, 189, 248, 0.3); }}
.imp-chip.inactive {{ opacity: 0.3; }}

/* ── Filters ── */
.filters {{
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    align-items: center;
    margin-bottom: 20px;
}}
.search-input {{
    flex: 1;
    min-width: 200px;
    padding: 9px 14px;
    border-radius: var(--radius-sm);
    border: 1px solid var(--border);
    background: var(--bg-card);
    color: var(--text);
    font-size: 14px;
    outline: none;
    transition: border-color 0.2s;
}}
.search-input:focus {{ border-color: var(--accent); }}
.search-input::placeholder {{ color: var(--text-muted); }}

.provider-filters {{
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
}}
.provider-chip {{
    padding: 5px 12px;
    border-radius: 14px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    border: 1.5px solid transparent;
    transition: all 0.2s;
    user-select: none;
    white-space: nowrap;
}}
.provider-chip:hover {{ filter: brightness(1.2); }}
.provider-chip.active {{ box-shadow: 0 0 10px rgba(56, 189, 248, 0.3); }}
.provider-chip.inactive {{ opacity: 0.3; }}

/* ── News Feed ── */
.category-section {{ margin-bottom: 28px; }}
.category-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
}}
.category-header h2 {{
    font-size: 17px;
    font-weight: 700;
    color: var(--text);
}}
.category-count {{
    font-size: 12px;
    color: var(--text-muted);
    background: var(--bg-card);
    padding: 3px 10px;
    border-radius: 10px;
}}

/* ── News Card ── */
.news-card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 18px;
    margin-bottom: 8px;
    transition: background 0.2s, border-color 0.2s;
}}
.news-card:hover {{
    background: var(--bg-hover);
    border-color: #475569;
}}
.news-card .card-title {{
    font-size: 15px;
    font-weight: 600;
    line-height: 1.5;
    margin-bottom: 6px;
}}
.news-card .card-title a {{
    color: var(--text);
    text-decoration: none;
    transition: color 0.2s;
}}
.news-card .card-title a:hover {{ color: var(--accent); }}
.news-card .card-meta {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 12px;
    color: var(--text-muted);
    margin-bottom: 6px;
    flex-wrap: wrap;
}}
.news-card .card-source {{
    color: var(--text-secondary);
    font-weight: 500;
}}
.news-card .card-date {{ color: var(--text-muted); }}
.provider-badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 700;
    color: #fff;
    white-space: nowrap;
}}
.news-card .card-summary {{
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.5;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
}}
.news-card.card-importance-high {{
    border-left: 3px solid #F59E0B;
}}
.news-card.card-importance-medium {{
    border-left: 3px solid #6B7280;
}}
.importance-stars {{
    font-size: 12px;
    letter-spacing: 2px;
    cursor: default;
}}
.event-type-badge {{
    display: inline-block;
    padding: 2px 10px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 700;
    color: #fff;
    white-space: nowrap;
}}
.card-badges {{
    display: flex;
    gap: 6px;
    align-items: center;
    margin-bottom: 6px;
    flex-wrap: wrap;
}}
.card-date-absolute {{
    color: var(--accent);
    font-weight: 500;
    font-size: 12px;
}}

/* ── Empty State ── */
.empty-state {{
    text-align: center;
    padding: 60px 20px;
    color: var(--text-muted);
}}
.empty-state .empty-icon {{ font-size: 48px; margin-bottom: 16px; }}
.empty-state p {{ font-size: 15px; }}

/* ── Footer ── */
.footer {{
    text-align: center;
    padding: 28px 16px;
    color: var(--text-muted);
    font-size: 12px;
    border-top: 1px solid var(--border);
    margin-top: 32px;
}}

/* ── Responsive ── */
@media (max-width: 640px) {{
    .header h1 {{ font-size: 18px; }}
    .filters {{ flex-direction: column; align-items: stretch; }}
    .search-input {{ min-width: auto; }}
    .news-card {{ padding: 12px 14px; }}
    .news-card .card-title {{ font-size: 14px; }}
}}
</style>
</head>
<body>

<header class="header">
    <h1>🇫🇷 法国云计算市场动态追踪</h1>
    <div class="sub" id="updateTime">Dernière mise à jour : chargement…</div>
    <div class="refresh-hint">🔄 更新数据请运行：python scripts/fetch_news.py</div>
</header>

<div class="container">
    <!-- Stats Bar -->
    <div class="stats-bar">
        <div class="stat-pill public active" data-cat="public_cloud" onclick="toggleCategory('public_cloud')">
            ☁️ 公有云 <span id="count-public">0</span>
        </div>
        <div class="stat-pill private active" data-cat="private_cloud" onclick="toggleCategory('private_cloud')">
            🖥️ 私有云 <span id="count-private">0</span>
        </div>
        <div class="stat-pill policy active" data-cat="policy" onclick="toggleCategory('policy')">
            📋 政策监管 <span id="count-policy">0</span>
        </div>
    </div>

    <!-- Filters -->
    <div class="filters">
        <input type="text" class="search-input" id="searchInput"
               placeholder="🔍 搜索标题、摘要…" oninput="onSearch()">
        <div class="provider-filters" id="providerFilters"></div>
    </div>

    <!-- Date Filter Bar (v2) -->
    <div class="date-filters" id="dateFilters">
        <span class="date-chip active" data-range="all" onclick="selectDateRange('all')">全部时间</span>
        <span class="date-chip" data-range="today" onclick="selectDateRange('today')">今天</span>
        <span class="date-chip" data-range="week" onclick="selectDateRange('week')">本周</span>
        <span class="date-chip" data-range="month" onclick="selectDateRange('month')">本月</span>
        <span class="date-chip" data-range="2026" onclick="selectDateRange('2026')">2026 年</span>
    </div>

    <!-- Event Type Filter Bar (v2) -->
    <div class="event-type-filters" id="eventTypeFilters"></div>

    <!-- Importance Filter (v2) -->
    <div class="importance-filters" id="importanceFilters"></div>

    <!-- News Feed -->
    <div id="newsFeed"></div>
</div>

<footer class="footer">
    Données fournies par Google News · Filtrées sur la France uniquement · Rafraîchi manuellement
</footer>

<script>
// ── Data ──
const ALL_ARTICLES = {articles_json};
const PROVIDER_COLORS = {provider_colors_json};
const CATEGORY_LABELS = {category_labels_json};
const EVENT_TYPES = {event_types_json};
const IMPORTANCE_COLORS = {importance_colors_json};
const GENERATED_AT = "{generated_at}";

// ── State ──
let activeCategories = new Set(["public_cloud", "private_cloud", "policy"]);
let activeProvider = null;  // null = show all, otherwise single provider string
let activeDateRange = "all";  // "all" | "today" | "week" | "month" | "2026"
let activeEventType = null;  // null = show all
let activeImportance = null;  // null = show all, "high" | "medium" | "low"
let searchText = "";

// ── Init ──
function init() {{
    // Update time
    const dt = new Date(GENERATED_AT);
    document.getElementById("updateTime").textContent =
        "Dernière mise à jour : " + dt.toLocaleString("fr-FR", {{ dateStyle: "full", timeStyle: "short" }});

    // Update counts
    updateCounts();
    // Render filters
    renderProviderFilters();
    renderEventTypeFilters();
    renderImportanceFilters();
    // Render feed
    renderFeed();
}}

function updateCounts() {{
    const counts = {{ public_cloud: 0, private_cloud: 0, policy: 0 }};
    ALL_ARTICLES.forEach(a => {{ counts[a.category] = (counts[a.category] || 0) + 1; }});
    document.getElementById("count-public").textContent = counts.public_cloud;
    document.getElementById("count-private").textContent = counts.private_cloud;
    document.getElementById("count-policy").textContent = counts.policy;
}}

// ── Category Toggle ──
function toggleCategory(cat) {{
    if (activeCategories.has(cat)) {{
        activeCategories.delete(cat);
    }} else {{
        activeCategories.add(cat);
    }}
    // Update pill visuals
    document.querySelectorAll(".stat-pill").forEach(pill => {{
        const c = pill.dataset.cat;
        if (activeCategories.has(c)) {{
            pill.classList.add("active");
            pill.classList.remove("inactive");
        }} else {{
            pill.classList.remove("active");
            pill.classList.add("inactive");
        }}
    }});
    renderFeed();
}}

// ── Provider Filters (single-select) ──
function renderProviderFilters() {{
    const providers = new Set();
    ALL_ARTICLES.forEach(a => {{ if (a.provider) providers.add(a.provider); }});

    const container = document.getElementById("providerFilters");
    container.innerHTML = "";

    // "All" chip
    const allChip = document.createElement("span");
    allChip.className = "provider-chip active";
    allChip.textContent = "全部";
    allChip.dataset.provider = "__all__";
    allChip.onclick = () => selectProvider(null);
    container.appendChild(allChip);

    [...providers].sort().forEach(p => {{
        const chip = document.createElement("span");
        const color = PROVIDER_COLORS[p] || "#6B7280";
        chip.className = "provider-chip active";
        chip.textContent = p;
        chip.style.backgroundColor = color + "33";
        chip.style.borderColor = color;
        chip.style.color = color;
        chip.dataset.provider = p;
        chip.onclick = () => selectProvider(p);
        container.appendChild(chip);
    }});
}}

function selectProvider(provider) {{
    activeProvider = provider;
    // Update chip visuals
    document.querySelectorAll(".provider-chip").forEach(c => {{
        const p = c.dataset.provider;
        if (provider === null) {{
            // "全部" mode: all chips active
            c.classList.add("active");
            c.classList.remove("inactive");
        }} else if (p === provider) {{
            c.classList.add("active");
            c.classList.remove("inactive");
        }} else if (p === "__all__") {{
            c.classList.remove("active");
            c.classList.add("inactive");
        }} else {{
            c.classList.remove("active");
            c.classList.add("inactive");
        }}
    }});
    renderFeed();
}}

// ── Date Range Filter (v2) ──
function selectDateRange(range) {{
    activeDateRange = range;
    document.querySelectorAll(".date-chip").forEach(c => {{
        c.classList.toggle("active", c.dataset.range === range);
    }});
    renderFeed();
}}

function passesDateFilter(article) {{
    if (activeDateRange === "all") return true;
    const pubDate = article.published_date_short;  // YYYY-MM-DD
    if (!pubDate) return true;

    const now = new Date();
    const pub = new Date(pubDate + "T00:00:00");

    switch (activeDateRange) {{
        case "today":
            return pubDate === now.toISOString().slice(0, 10);
        case "week": {{
            const weekAgo = new Date(now);
            weekAgo.setDate(weekAgo.getDate() - 7);
            return pub >= weekAgo;
        }}
        case "month": {{
            const monthAgo = new Date(now);
            monthAgo.setDate(monthAgo.getDate() - 30);
            return pub >= monthAgo;
        }}
        case "2026":
            return pubDate >= "2026-01-01" && pubDate < "2027-01-01";
        default:
            return true;
    }}
}}

// ── Event Type Filter (v2) ──
function renderEventTypeFilters() {{
    const container = document.getElementById("eventTypeFilters");
    container.innerHTML = "";

    // "All" chip
    const allChip = document.createElement("span");
    allChip.className = "event-chip active";
    allChip.textContent = "全部类型";
    allChip.style.backgroundColor = "#374151";
    allChip.style.borderColor = "#4B5563";
    allChip.style.color = "#D1D5DB";
    allChip.onclick = () => selectEventType(null);
    container.appendChild(allChip);

    Object.entries(EVENT_TYPES).forEach(([key, info]) => {{
        const chip = document.createElement("span");
        chip.className = "event-chip active";
        chip.textContent = info.icon + " " + info.label;
        chip.style.backgroundColor = info.color + "33";
        chip.style.borderColor = info.color;
        chip.style.color = info.color;
        chip.dataset.etype = key;
        chip.onclick = () => selectEventType(key);
        container.appendChild(chip);
    }});
}}

function selectEventType(etype) {{
    activeEventType = etype;
    document.querySelectorAll(".event-chip").forEach(c => {{
        if (etype === null) {{
            c.classList.add("active");
            c.classList.remove("inactive");
        }} else if (c.dataset.etype === etype) {{
            c.classList.add("active");
            c.classList.remove("inactive");
        }} else {{
            c.classList.remove("active");
            c.classList.add("inactive");
        }}
    }});
    renderFeed();
}}

// ── Importance Filter (v2) ──
function renderImportanceFilters() {{
    const container = document.getElementById("importanceFilters");
    container.innerHTML = "";

    const items = [
        {{ key: null, label: "全部重要度", color: "#D1D5DB", bg: "#374151" }},
        {{ key: "high", label: "★★★ 重要", color: IMPORTANCE_COLORS.high, bg: IMPORTANCE_COLORS.high + "33" }},
        {{ key: "medium", label: "★★ 一般", color: IMPORTANCE_COLORS.medium, bg: IMPORTANCE_COLORS.medium + "33" }},
        {{ key: "low", label: "★ 低", color: IMPORTANCE_COLORS.low, bg: IMPORTANCE_COLORS.low + "33" }},
    ];

    items.forEach(item => {{
        const chip = document.createElement("span");
        chip.className = "imp-chip active";
        chip.textContent = item.label;
        chip.style.backgroundColor = item.bg;
        chip.style.color = item.color;
        chip.style.borderColor = item.color + "66";
        chip.dataset.imp = item.key === null ? "__all__" : item.key;
        chip.onclick = () => selectImportance(item.key);
        container.appendChild(chip);
    }});
}}

function selectImportance(imp) {{
    activeImportance = imp;
    document.querySelectorAll(".imp-chip").forEach(c => {{
        if (imp === null) {{
            c.classList.add("active");
            c.classList.remove("inactive");
        }} else if (c.dataset.imp === imp) {{
            c.classList.add("active");
            c.classList.remove("inactive");
        }} else {{
            c.classList.remove("active");
            c.classList.add("inactive");
        }}
    }});
    renderFeed();
}}

// ── Search ──
function onSearch() {{
    searchText = document.getElementById("searchInput").value.toLowerCase().trim();
    renderFeed();
}}

// ── Render ──
function renderFeed() {{
    let filtered = ALL_ARTICLES.filter(a => {{
        if (!activeCategories.has(a.category)) return false;
        if (activeProvider !== null) {{
            if (!a.provider || a.provider !== activeProvider) return false;
        }}
        if (activeEventType !== null && a.event_type !== activeEventType) return false;
        if (activeImportance !== null && a.importance !== activeImportance) return false;
        if (!passesDateFilter(a)) return false;
        if (searchText) {{
            const haystack = (a.title + " " + a.summary + " " + a.source).toLowerCase();
            if (!haystack.includes(searchText)) return false;
        }}
        return true;
    }});

    // Group by category
    const groups = {{ public_cloud: [], private_cloud: [], policy: [] }};
    filtered.forEach(a => {{
        if (groups[a.category]) groups[a.category].push(a);
    }});

    const feed = document.getElementById("newsFeed");
    if (filtered.length === 0) {{
        feed.innerHTML = `<div class="empty-state">
            <div class="empty-icon">📭</div>
            <p>Aucun article trouvé avec ces filtres</p>
        </div>`;
        return;
    }}

    const catOrder = ["public_cloud", "private_cloud", "policy"];
    let html = "";

    catOrder.forEach(cat => {{
        const articles = groups[cat];
        if (!articles || articles.length === 0) return;

        html += `<div class="category-section">
            <div class="category-header">
                <h2>${{cat === "public_cloud" ? "☁️" : cat === "private_cloud" ? "🖥️" : "📋"}} ${{CATEGORY_LABELS[cat]}}</h2>
                <span class="category-count">${{articles.length}} articles</span>
            </div>`;

        articles.forEach(a => {{
            // Event type info
            const etInfo = EVENT_TYPES[a.event_type] || EVENT_TYPES.general;
            const eventTypeBadge = `<span class="event-type-badge" style="background:${{etInfo.color}}">${{etInfo.icon}} ${{etInfo.label}}</span>`;

            // Importance stars
            const impColor = IMPORTANCE_COLORS[a.importance] || "#6B7280";
            const impStars = `<span class="importance-stars" style="color:${{impColor}}" title="${{a.importance_label}}">${{a.importance_stars}}</span>`;

            // Provider badge
            const providerHtml = a.provider
                ? `<span class="provider-badge" style="background:${{PROVIDER_COLORS[a.provider] || "#6B7280"}}">${{a.provider}}</span>`
                : "";

            // Date
            const dateDisplay = a.published_display || "";
            const dateShort = a.published_date_short || "";

            // Escape
            const titleEscaped = a.title.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
            const summaryEscaped = a.summary.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
            const sourceEscaped = a.source.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");

            const cardClass = a.importance === "high" ? "news-card card-importance-high" : a.importance === "medium" ? "news-card card-importance-medium" : "news-card";

            html += `<div class="${{cardClass}}">
                <div class="card-badges">
                    ${{impStars}}
                    ${{eventTypeBadge}}
                    ${{providerHtml}}
                </div>
                <div class="card-title">
                    <a href="${{a.url}}" target="_blank" rel="noopener noreferrer">${{titleEscaped}}</a>
                </div>
                <div class="card-meta">
                    <span class="card-source">${{sourceEscaped}}</span>
                    <span class="card-date-absolute">${{dateShort}}</span>
                    <span class="card-date">${{dateDisplay}}</span>
                </div>
                <div class="card-summary">${{summaryEscaped}}</div>
            </div>`;
        }});

        html += "</div>";
    }});

    feed.innerHTML = html;
}}

// ── Boot ──
init();
</script>
</body>
</html>"""


# ── Output ──

def write_output(articles, output_path):
    """Generate HTML and write to output path."""
    html_content = generate_html(articles)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\n[OK] HTML written to: {output_path}")
    print(f"  Total articles: {len(articles)}")

    # Category breakdown
    cats = {}
    for a in articles:
        cats[a["category"]] = cats.get(a["category"], 0) + 1
    for k, v in cats.items():
        print(f"  {CATEGORY_LABELS.get(k, k)}: {v}")


def main():
    output_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "docs",
        "index.html",
    )

    print("=" * 56)
    print("  French Cloud Computing News Tracker")
    print("=" * 56)
    print()

    articles = fetch_all()
    write_output(articles, output_path)


if __name__ == "__main__":
    main()
