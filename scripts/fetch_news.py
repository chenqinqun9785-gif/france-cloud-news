"""
French Cloud Ecosystem Tracker — Core Script (v3)
Fetches RSS → classifies → scores → deduplicates → merges history → generates HTML → sends Telegram.
"""
import hashlib
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
    QUERIES, CATEGORIES, CATEGORY_COMPAT, CATEGORY_LABELS,
    ENTITIES, ENTITY_LOOKUP,
    EVENT_TYPES, EVENT_KEYWORDS,
    IMPORTANCE_LABELS, IMPORTANCE_STARS, IMPORTANCE_COLORS, importance_level,
    ENTITY_SCORE_BONUS, FRANCE_KEYWORDS, INDUSTRY_SECTORS,
    STRATEGIC_KEYWORDS, CREDIBLE_SOURCES,
    PROVIDER_COLORS, build_rss_url,
)


# ═══════════════════════════════════════════════════════════
# 0. UTILITY HELPERS
# ═══════════════════════════════════════════════════════════

def build_google_translate_url(original_url):
    """Build a Google Translate link for full-page Chinese translation."""
    if not original_url:
        return ""
    return f"https://translate.google.com/translate?sl=auto&tl=zh-CN&u={quote(original_url, safe='')}"

# ═══════════════════════════════════════════════════════════
# 0b. TRANSLATION UTILITIES
# ═══════════════════════════════════════════════════════════

def translate_text_to_zh(text):
    """Translate a single text string to Chinese using Google Translate API."""
    if not text or not text.strip():
        return text
    import urllib.request
    import urllib.parse

    url = "https://translate.googleapis.com/translate_a/single"
    params = {"client": "gtx", "sl": "auto", "tl": "zh-CN", "dt": "t", "q": text}
    full_url = url + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)

    try:
        req = urllib.request.Request(full_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and data[0]:
                return "".join([part[0] for part in data[0] if part[0] is not None])
    except Exception:
        pass
    return text


def translate_article(article):
    """Fill in title_zh and summary_zh for an article. Returns the article."""
    if not article.get("title_zh") or article.get("translation_status") == "fallback_original":
        try:
            article["title_zh"] = translate_text_to_zh(article.get("title_original", article.get("title", "")))
            article["translation_status"] = "translated"
        except Exception:
            article["title_zh"] = article.get("title_original", article.get("title", ""))
            article["translation_status"] = "fallback_original"

    if not article.get("summary_zh") or article.get("translation_status") == "fallback_original":
        try:
            article["summary_zh"] = translate_text_to_zh(article.get("summary_original", article.get("summary", "")))
        except Exception:
            article["summary_zh"] = article.get("summary_original", article.get("summary", ""))

    return article


def ensure_translation_fields(article):
    """Fill missing translation fields for backward compatibility."""
    defaults = {
        "title_original": article.get("title", ""),
        "title_zh": article.get("title_zh") or article.get("title", ""),
        "summary_original": article.get("summary", ""),
        "summary_zh": article.get("summary_zh") or article.get("summary", ""),
        "translated_url": article.get("translated_url") or build_google_translate_url(article.get("url", "")),
        "translation_status": article.get("translation_status", "fallback_original"),
        "translation_provider": article.get("translation_provider", "google_translate_link"),
    }
    for k, v in defaults.items():
        if k not in article or article[k] is None:
            article[k] = v
    return article

# ═══════════════════════════════════════════════════════════
# 1. CLASSIFICATION
# ═══════════════════════════════════════════════════════════

def normalize_title(title):
    """Normalize title for dedup comparison."""
    t = title.lower()
    t = re.sub(r"^exclusif\s*[:：]\s*", "", t)
    t = re.sub(r"^vidéo\s*[:：]\s*", "", t)
    t = re.sub(r"[^\w\s]", "", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def format_relative_date(dt):
    """Format datetime for relative display."""
    if not dt:
        return ""
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
        return f"Il y a {diff.days}j"
    else:
        return dt.strftime("%Y-%m-%d")


def stable_id(title, source):
    """Generate stable article ID."""
    return hashlib.md5(f"{normalize_title(title)}|{source}".encode("utf-8")).hexdigest()[:16]


# ═══════════════════════════════════════════════════════════
# 1. CLASSIFICATION
# ═══════════════════════════════════════════════════════════

def classify_primary_category(query_category, title, summary):
    """
    Determine primary category.
    First uses query's configured category, then refines by content keywords.
    """
    # Start with the query's configured category (using compat mapping)
    cat = CATEGORY_COMPAT.get(query_category, query_category)

    text = (title + " " + summary).lower()

    # Refine based on content signals
    sovereignty_signals = ["secnumcloud", "cloud de confiance", "cloud souverain",
                           "souveraineté", "données sensibles", "qualifié"]
    partner_signals = ["capgemini", "orange business", "accenture", "devoteam",
                       "sopra steria", "atos", "eviden", "inetum", "cgi", "wavestone",
                       "deloitte", "pwc", "kpmg"]
    ai_dc_signals = ["gpu", "h100", "b200", "ai cloud", "ai infrastructure",
                     "mistral ai", "data center", "datacenter", "centre de données"]
    industry_signals = ["banque", "assurance", "santé", "hôpital", "hds",
                        "marché public", "industrie", "énergie", "retail"]

    # If query category is broad, refine
    if cat == "policy_regulation":
        if any(s in text for s in sovereignty_signals):
            cat = "sovereign_trusted"
        elif any(s in text for s in partner_signals):
            cat = "ecosystem_partners"
        elif any(s in text for s in ai_dc_signals):
            cat = "ai_datacenter"
        elif any(s in text for s in industry_signals):
            cat = "industry_cloud"

    return cat


def classify_event_type(title, summary):
    """Classify article event type based on keyword matching."""
    text = (title + " " + summary).lower()
    for event_type, keywords in EVENT_KEYWORDS:
        for kw in keywords:
            if kw.lower() in text:
                return event_type
    return "general"


def extract_entities(title, summary):
    """Extract all mentioned entities from title + summary."""
    text = (title + " " + summary).lower()
    found = {}

    for alias, (display_name, color, group) in ENTITY_LOOKUP.items():
        if alias in text:
            # Ensure alias is matched as a word boundary to avoid partial matches
            # e.g., "AWS" should match "AWS" but not "LAWS"
            pattern = r'\b' + re.escape(alias) + r'\b'
            if re.search(pattern, text):
                if display_name not in found:
                    found[display_name] = {"display": display_name, "color": color, "group": group}

    return list(found.values())


def score_importance(title, summary, event_type, entities, source):
    """
    Score importance 0–100 based on multiple dimensions.
    """
    score = 0
    text = (title + " " + summary).lower()

    # 1. Event type base score
    et_info = EVENT_TYPES.get(event_type, EVENT_TYPES["general"])
    score += et_info.get("score_bonus", 10)

    # 2. Entity bonuses
    entity_names = [e["display"] for e in entities]
    for name in entity_names:
        bonus = ENTITY_SCORE_BONUS.get(name, ENTITY_SCORE_BONUS.get("_default", 3))
        score += bonus

    # 3. France relevance
    france_count = sum(1 for kw in FRANCE_KEYWORDS if kw in text)
    score += min(france_count * 3, 9)

    # 4. Industry relevance
    for sector_name, sector_info in INDUSTRY_SECTORS.items():
        if any(kw in text for kw in sector_info["keywords"]):
            score += sector_info["bonus"]
            break  # Only apply highest industry bonus

    # 5. Strategic keywords
    for strategy_name, strategy_info in STRATEGIC_KEYWORDS.items():
        if any(kw.lower() in text for kw in strategy_info["keywords"]):
            score += strategy_info["bonus"]

    # 6. Source credibility
    source_lower = source.lower()
    if any(cs in source_lower for cs in CREDIBLE_SOURCES):
        score += 5

    # 7. Title specificity bonus (longer, more specific titles are usually more important)
    if len(title) > 50:
        score += 3

    return min(score, 100)


# ═══════════════════════════════════════════════════════════
# 2. ARTICLE EXTRACTION
# ═══════════════════════════════════════════════════════════

def extract_article(entry, query_config):
    """Convert a feedparser entry into our article dict with full classification."""
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

    # Clean summary
    summary = re.sub(r"<[^>]+>", " ", summary_raw)
    summary = re.sub(r"\s+", " ", summary).strip()
    if len(summary) > 500:
        summary = summary[:500].rsplit(" ", 1)[0] + "…"

    # Classification
    query_cat = query_config.get("category", "policy_regulation")
    primary_category = classify_primary_category(query_cat, title, summary)
    event_type = classify_event_type(title, summary)
    entities = extract_entities(title, summary)
    score = score_importance(title, summary, event_type, entities, source)
    level = importance_level(score)

    # Published dates
    date_short = published_dt.strftime("%Y-%m-%d") if published_dt else ""
    published_iso = published_dt.isoformat() if published_dt else ""

    # Translation URL
    translated_url = build_google_translate_url(link)

    return {
        "id": stable_id(title, source),
        "title": title,
        "url": link,
        "source": source,
        "published": published_iso,
        "published_display": format_relative_date(published_dt) if published_dt else "",
        "published_date_short": date_short,
        "category": primary_category,
        "category_label": CATEGORIES.get(primary_category, {}).get("label", primary_category),
        "provider": query_config.get("provider"),
        "summary": summary,
        "event_type": event_type,
        "event_type_label": EVENT_TYPES.get(event_type, {}).get("label", "综合动态"),
        "event_type_icon": EVENT_TYPES.get(event_type, {}).get("icon", ""),
        "entities": entities,
        "importance": level,
        "importance_stars": IMPORTANCE_STARS.get(level, "★"),
        "importance_score": score,
        "importance_label": IMPORTANCE_LABELS.get(level, "低"),
        "first_seen_at": datetime.now(timezone.utc).isoformat(),
        # Translation fields (v3.1)
        "title_original": title,
        "title_zh": "",  # filled later by translate_article()
        "summary_original": summary,
        "summary_zh": "",  # filled later by translate_article()
        "translated_url": translated_url,
        "translation_status": "not_translated",
        "translation_provider": "google_translate_link",
    }


# ═══════════════════════════════════════════════════════════
# 3. DEDUPLICATION & HISTORY
# ═══════════════════════════════════════════════════════════

def deduplicate(articles):
    """Two-pass dedup: URL → normalized title."""
    seen_urls = set()
    seen_titles = set()
    unique = []

    for a in articles:
        url = a.get("url", "")
        if url and url in seen_urls:
            continue
        title_norm = normalize_title(a.get("title", ""))
        if title_norm and title_norm in seen_titles:
            continue
        if url:
            seen_urls.add(url)
        if title_norm:
            seen_titles.add(title_norm)
        unique.append(a)

    return unique


def load_history(history_path):
    """Load previous article history."""
    if not os.path.exists(history_path):
        return {}
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {a["id"]: a for a in data.get("articles", [])}
    except Exception:
        return {}


def save_history(articles, history_path):
    """Save articles to history (keep last 90 days)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    recent = []
    for a in articles:
        pub = a.get("published", "")
        if pub:
            try:
                pub_dt = dateparser.parse(pub)
                if pub_dt and pub_dt < cutoff:
                    continue
            except Exception:
                pass
        recent.append(a)

    os.makedirs(os.path.dirname(history_path), exist_ok=True)
    with open(history_path, "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.now(timezone.utc).isoformat(),
                    "total": len(recent), "articles": recent},
                  f, ensure_ascii=False, indent=2)


def merge_with_history(new_articles, history):
    """Merge new articles with history, preserving first_seen and translations."""
    merged = {}
    # Add history first
    for aid, a in history.items():
        a["_from_history"] = True
        # Ensure compatibility for old history articles
        a = ensure_translation_fields(a)
        merged[aid] = a

    # Add/update new articles
    for a in new_articles:
        aid = a["id"]
        if aid in merged:
            old = merged[aid]
            # Preserve existing translations from history
            for field in ["title_zh", "summary_zh", "translation_status", "translation_provider"]:
                if old.get(field) and old[field] != "fallback_original" and old[field] != "not_translated":
                    a[field] = old[field]
            # Preserve first_seen and translated_url
            a["first_seen_at"] = old.get("first_seen_at", a["first_seen_at"])
            a["translated_url"] = old.get("translated_url") or a.get("translated_url", "")
            old["_from_history"] = False
            old["last_seen_at"] = datetime.now(timezone.utc).isoformat()
            merged[aid] = a
        else:
            merged[aid] = a

    return list(merged.values())


def translate_new_articles(articles, max_translations=50):
    """Translate titles/summaries for articles missing translations. Capped per run."""
    to_translate = [a for a in articles
                    if not a.get("title_zh") or a.get("translation_status") in ("not_translated", "fallback_original")]
    to_translate = to_translate[:max_translations]

    if not to_translate:
        return

    print(f"  Translating {len(to_translate)} new articles...")
    for i, a in enumerate(to_translate):
        a = translate_article(a)
        if i < len(to_translate) - 1:
            time.sleep(0.3)
    print(f"  Translation complete")


# ═══════════════════════════════════════════════════════════
# 4. RSS FETCHING
# ═══════════════════════════════════════════════════════════

def fetch_all():
    """Fetch all RSS feeds and return deduplicated, sorted articles."""
    all_articles = []
    total_queries = len(QUERIES)

    for i, q in enumerate(QUERIES):
        url = build_rss_url(q)
        label = q.get("provider") or q.get("name", q["category"])
        print(f"[{i+1}/{total_queries}] {label}...", end=" ", flush=True)

        try:
            feed = feedparser.parse(url)
            if feed.bozo and not feed.entries:
                print(f"[WARN] {feed.bozo_exception}")
                continue

            count = 0
            for entry in feed.entries:
                article = extract_article(entry, q)
                all_articles.append(article)
                count += 1

            print(f"OK ({count})")
        except Exception as e:
            print(f"[FAIL] {e}")

        if i < total_queries - 1:
            time.sleep(1.2)

    print(f"\nTotal raw: {len(all_articles)}")
    unique = deduplicate(all_articles)
    print(f"After dedup: {len(unique)}")

    # Sort: importance_score desc, then date desc
    unique.sort(key=lambda a: (-a.get("importance_score", 0), a.get("published", "")), reverse=False)
    # Actually: highest score first
    unique.sort(key=lambda a: (-a.get("importance_score", 0), str(a.get("published", ""))), reverse=False)

    return unique


# ═══════════════════════════════════════════════════════════
# 5. TELEGRAM NOTIFICATION
# ═══════════════════════════════════════════════════════════

def translate_to_chinese(text):
    """Translate text to Chinese using Google Translate."""
    import urllib.request
    import urllib.parse

    url = "https://translate.googleapis.com/translate_a/single"
    params = {"client": "gtx", "sl": "auto", "tl": "zh-CN", "dt": "t", "q": text}
    full_url = url + "?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)

    try:
        req = urllib.request.Request(full_url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and data[0]:
                return "".join([part[0] for part in data[0] if part[0] is not None])
    except Exception:
        pass
    return text


def send_telegram_digest(articles, bot_token, chat_id):
    """Send daily digest grouped by category, score>=75 only."""
    if not bot_token or not chat_id:
        print("[INFO] Telegram credentials not set, skipping notification")
        return

    # Filter: score >= 60, last 24h (with 48h fallback if too few)
    cutoff_24 = datetime.now(timezone.utc) - timedelta(hours=24)
    cutoff_48 = datetime.now(timezone.utc) - timedelta(hours=48)

    in_24h = []
    in_48h = []
    for a in articles:
        if a.get("importance_score", 0) < 60:
            continue
        pub_str = a.get("published", "")
        if not pub_str:
            in_24h.append(a)
            continue
        try:
            pub_dt = dateparser.parse(pub_str)
            if pub_dt and pub_dt >= cutoff_24:
                in_24h.append(a)
            elif pub_dt and pub_dt >= cutoff_48:
                in_48h.append(a)
        except Exception:
            in_24h.append(a)

    use_48h = False
    if len(in_24h) < 3 and in_48h:
        in_24h = in_24h + in_48h[:20]
        use_48h = True

    if not in_24h:
        print("[INFO] No qualifying articles, skipping Telegram")
        return

    top = in_24h[:20]

    # Ensure all have Chinese titles
    for a in top:
        if not a.get("title_zh") or a.get("translation_status") in ("not_translated", "fallback_original"):
            a["title_zh"] = translate_text_to_zh(a.get("title_original", a.get("title", "")))
        if not a.get("translated_url"):
            a["translated_url"] = build_google_translate_url(a.get("url", ""))

    # Group by category
    groups = {}
    for a in top:
        cat = a.get("category", "policy_regulation")
        groups.setdefault(cat, []).append(a)

    cat_order = ["sovereign_trusted", "policy_regulation", "ecosystem_partners",
                 "ai_datacenter", "public_cloud", "private_hybrid", "industry_cloud"]

    time_label = "近48小时" if use_48h else "近24小时"

    lines = [
        "\U0001F1EB\U0001F1F7 *法国云计算市场动态追踪*",
        f"\U0001F4C5 {datetime.now().strftime('%Y-%m-%d')}",
        f"✨ {time_label}高重要性动态: {len(top)} 条",
        "",
    ]

    cat_emoji = {k: v["icon"] for k, v in CATEGORIES.items()}
    cat_labels = {k: v["label"] for k, v in CATEGORIES.items()}

    for cat in cat_order:
        items = groups.get(cat, [])
        if not items:
            continue
        lines.append(f"*{cat_emoji.get(cat, '')} {cat_labels.get(cat, cat)}*")

        for a in items:
            cn_title = a.get("title_zh") or a.get("title_cn") or a.get("title_original") or a["title"]
            et_label = a.get("event_type_label", "")
            et_icon = a.get("event_type_icon", "")
            score = a.get("importance_score", 0)

            # Top entities
            entity_names = [e["display"] for e in a.get("entities", [])[:3]]
            entity_str = "｜".join(entity_names) if entity_names else ""

            source = a.get("source", "")
            t_url = a.get("translated_url") or build_google_translate_url(a.get("url", ""))

            lines.append(f"[{score}] [{cn_title}]({t_url})")
            lines.append(f"    [{a.get('title_original','')[:60]}]({a['url']})")
            tag_line = f"    {et_icon}{et_label}"
            if entity_str:
                tag_line += f"｜{entity_str}"
            tag_line += f"｜{source}"
            lines.append(tag_line)

    body = "\n".join(lines)
    if len(body) > 4000:
        body = body[:4000] + "\n\n...(truncated)"

    body += f"\n\n\U0001F310 [查看全部](https://chenqinqun9785-gif.github.io/france-cloud-news/)"

    try:
        import urllib.request
        api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = json.dumps({
            "chat_id": chat_id, "text": body,
            "parse_mode": "Markdown", "disable_web_page_preview": True,
        }).encode("utf-8")
        req = urllib.request.Request(api_url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                print(f"[OK] Telegram digest sent: {len(top)} articles")
            else:
                print(f"[WARN] Telegram send failed: {result}")
    except Exception as e:
        print(f"[WARN] Telegram error: {e}")


# ═══════════════════════════════════════════════════════════
# 6. HTML GENERATION
# ═══════════════════════════════════════════════════════════

def escape_for_script(json_str):
    return json_str.replace("</", "<\\/")


def generate_html(articles):
    """Generate complete self-contained HTML dashboard (v3.1)."""
    generated_at = datetime.now().isoformat()

    # Trim to essential fields only (reduce HTML size by ~15%)
    KEEP = ["id","title","title_original","title_zh","url","translated_url",
            "source","published","published_display","published_date_short",
            "category","provider","summary","summary_original","summary_zh",
            "event_type","event_type_label","event_type_icon","entities",
            "importance","importance_stars","importance_score"]
    articles_json = json.dumps([{k:a.get(k) for k in KEEP if k in a} for a in articles], ensure_ascii=False)

    categories_json = escape_for_script(json.dumps(CATEGORIES, ensure_ascii=False))
    event_types_json = escape_for_script(json.dumps(EVENT_TYPES, ensure_ascii=False))
    provider_colors_json = json.dumps(PROVIDER_COLORS, ensure_ascii=False)
    importance_colors_json = json.dumps(IMPORTANCE_COLORS, ensure_ascii=False)

    # Compute summary counts
    now_ts = datetime.now().isoformat()
    count_all = len(articles)
    count_high = sum(1 for a in articles if a.get("importance") == "high")
    count_today = sum(1 for a in articles if a.get("published_date_short", "") == datetime.now().strftime("%Y-%m-%d"))
    count_sovereign = sum(1 for a in articles if a.get("category") == "sovereign_trusted")
    count_partner = sum(1 for a in articles if a.get("category") == "ecosystem_partners")
    count_ai_dc = sum(1 for a in articles if a.get("category") == "ai_datacenter")

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>法国云计算市场动态追踪</title>
<meta name="theme-color" content="#0f172a">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="法国云动态">
<link rel="manifest" href="manifest.json">
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='0.9em' font-size='90'>🇫🇷</text></svg>">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{--bg:#0f172a;--bg-card:#1e293b;--bg-hover:#273449;--text:#e2e8f0;--text-secondary:#94a3b8;--text-muted:#64748b;--border:#334155;--accent:#38bdf8;--radius:10px;--radius-sm:6px}}
body{{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Helvetica Neue",Arial,"Noto Sans SC",sans-serif;background:var(--bg);color:var(--text);line-height:1.6;min-height:100vh}}

.header{{background:linear-gradient(135deg,#1e293b 0%,#0f172a 100%);border-bottom:1px solid var(--border);padding:24px 16px 18px;text-align:center;position:sticky;top:0;z-index:10}}
.header h1{{font-size:20px;font-weight:700;background:linear-gradient(135deg,#38bdf8,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}}
.header .sub{{font-size:12px;color:var(--text-muted);margin-top:4px}}
.header .refresh-hint{{font-size:11px;color:#475569;margin-top:4px;font-family:monospace}}

.container{{max-width:1000px;margin:0 auto;padding:16px}}

/* Summary Cards */
.summary-cards{{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}}
.summary-card{{flex:1;min-width:100px;background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius-sm);padding:10px 14px;text-align:center;cursor:default}}
.summary-card .card-num{{font-size:22px;font-weight:700;color:var(--accent)}}
.summary-card .card-label{{font-size:11px;color:var(--text-muted);margin-top:2px}}

/* Filter Bars */
.filter-row{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px;align-items:center}}
.filter-chip{{padding:5px 12px;border-radius:14px;font-size:11px;font-weight:600;cursor:pointer;border:1.5px solid transparent;transition:all 0.2s;user-select:none;white-space:nowrap}}
.filter-chip:hover{{filter:brightness(1.2)}}
.filter-chip.active{{box-shadow:0 0 10px rgba(56,189,248,0.3)}}
.filter-chip.inactive{{opacity:0.3}}
.search-input{{flex:1;min-width:180px;padding:8px 12px;border-radius:var(--radius-sm);border:1px solid var(--border);background:var(--bg-card);color:var(--text);font-size:13px;outline:none}}
.search-input:focus{{border-color:var(--accent)}}
.search-input::placeholder{{color:var(--text-muted)}}

.category-section{{margin-bottom:24px}}
.category-header{{display:flex;align-items:center;gap:8px;margin-bottom:10px;padding-bottom:6px;border-bottom:1px solid var(--border)}}
.category-header h2{{font-size:16px;font-weight:700;color:var(--text)}}
.category-count{{font-size:11px;color:var(--text-muted);background:var(--bg-card);padding:2px 8px;border-radius:8px}}

.news-card{{background:var(--bg-card);border:1px solid var(--border);border-radius:var(--radius);padding:12px 16px;margin-bottom:7px;transition:background 0.2s}}
.news-card:hover{{background:var(--bg-hover)}}
.news-card.card-high{{border-left:3px solid #F59E0B}}
.news-card.card-medium{{border-left:3px solid #6B7280}}

.card-badges{{display:flex;gap:5px;align-items:center;margin-bottom:5px;flex-wrap:wrap}}
.importance-stars{{font-size:12px;letter-spacing:1px}}
.entity-tag{{display:inline-block;padding:1px 8px;border-radius:8px;font-size:10px;font-weight:700;color:#fff;white-space:nowrap}}
.event-type-badge{{display:inline-block;padding:1px 8px;border-radius:8px;font-size:10px;font-weight:700;color:#fff;white-space:nowrap}}
.provider-badge{{display:inline-block;padding:1px 8px;border-radius:8px;font-size:10px;font-weight:700;color:#fff;white-space:nowrap}}
.score-badge{{font-size:10px;color:var(--text-muted);font-weight:600;margin-left:auto}}

.card-title{{font-size:14px;font-weight:600;line-height:1.4;margin-bottom:4px}}
.card-title a{{color:var(--text);text-decoration:none;transition:color 0.2s}}
.card-title a:hover{{color:var(--accent)}}
.card-meta{{display:flex;align-items:center;gap:8px;font-size:11px;color:var(--text-muted);flex-wrap:wrap}}
.card-summary{{font-size:12px;color:var(--text-secondary);line-height:1.5;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden}}

/* Card: Chinese title */
.card-title-zh{{font-size:14px;font-weight:600;line-height:1.4;margin-bottom:4px;color:var(--text)}}

/* Card: action buttons */
.card-actions{{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;align-items:center}}
.btn{{display:inline-block;padding:6px 14px;border-radius:16px;font-size:11px;font-weight:600;text-decoration:none;cursor:pointer;transition:all 0.2s;border:1px solid transparent;white-space:nowrap}}
.btn-translate{{background:#2563EB;color:#fff;border-color:#2563EB}}
.btn-translate:hover{{background:#1D4ED8}}
.btn-translate:active{{background:#1E40AF}}
.btn-original{{background:var(--bg-card);color:var(--text-secondary);border-color:var(--border)}}
.btn-original:hover{{background:var(--bg-hover);color:var(--text)}}
.btn:disabled{{opacity:0.4;cursor:default}}

/* Pagination */
.pagination{{display:flex;align-items:center;justify-content:center;gap:6px;padding:20px 0;flex-wrap:wrap}}
.page-info{{text-align:center;color:var(--text);font-size:13px;font-weight:600;padding:8px 0;background:var(--bg-card);border-radius:var(--radius-sm);margin-bottom:12px}}
.card-details-inline{{margin-top:6px;font-size:11px;color:var(--text-muted)}}
.card-details-inline summary{{cursor:pointer;padding:2px 0;user-select:none;list-style:none}}
.card-details-inline summary::-webkit-details-marker{{display:none}}
.card-details-inline summary:hover{{color:var(--text)}}
.card-details{{margin-top:8px;font-size:11px;color:var(--text-muted)}}
.card-details summary{{cursor:pointer;padding:4px 0;user-select:none;list-style:none}}
.card-details summary::-webkit-details-marker{{display:none}}
.card-details summary:hover{{color:var(--text)}}
.card-details .orig-title{{font-size:13px;color:var(--text-secondary);font-weight:500;margin:6px 0 4px;padding:8px 12px;background:rgba(0,0,0,0.2);border-radius:var(--radius-sm);border-left:2px solid var(--border)}}
.card-details .orig-summary{{font-size:11px;color:var(--text-muted);line-height:1.5;margin:4px 0;padding-left:12px}}

.empty-state{{text-align:center;padding:60px 20px;color:var(--text-muted)}}
.empty-state .empty-icon{{font-size:48px;margin-bottom:12px}}
.footer{{text-align:center;padding:24px 16px;color:var(--text-muted);font-size:11px;border-top:1px solid var(--border);margin-top:28px}}

@media(max-width:640px){{
.header h1{{font-size:17px}}
.summary-card{{min-width:70px;padding:8px 10px}}
.summary-card .card-num{{font-size:18px}}
.news-card{{padding:10px 12px}}
}}
</style>
</head>
<body>

<header class="header">
    <h1>🇫🇷 法国云计算市场动态追踪</h1>
    <div class="sub" id="updateTime">Dernière mise à jour : chargement...</div>
    <div class="refresh-hint">🔄 python scripts/fetch_news.py</div>
</header>

<div class="container">

    <!-- Summary Cards -->
    <div class="summary-cards">
        <div class="summary-card"><div class="card-num" id="sum-total">{count_all}</div><div class="card-label">总文章</div></div>
        <div class="summary-card"><div class="card-num" id="sum-today">{count_today}</div><div class="card-label">今日新增</div></div>
        <div class="summary-card"><div class="card-num" id="sum-high">{count_high}</div><div class="card-label">高重要性</div></div>
        <div class="summary-card"><div class="card-num">{count_sovereign}</div><div class="card-label">主权云</div></div>
        <div class="summary-card"><div class="card-num">{count_partner}</div><div class="card-label">合作伙伴</div></div>
        <div class="summary-card"><div class="card-num">{count_ai_dc}</div><div class="card-label">AI/数据中心</div></div>
    </div>

    <!-- Category Filter -->
    <div class="filter-row" id="catFilters"></div>

    <!-- Date + Search -->
    <div class="filter-row">
        <span class="filter-chip" data-range="all" onclick="selectDateRange('all')">全部</span>
        <span class="filter-chip" data-range="today" onclick="selectDateRange('today')">今天</span>
        <span class="filter-chip" data-range="7d" onclick="selectDateRange('7d')">7天</span>
        <span class="filter-chip active" data-range="30d" onclick="selectDateRange('30d')">30天</span>
        <span class="filter-chip" data-range="2026" onclick="selectDateRange('2026')">2026年</span>
        <input type="text" class="search-input" id="searchInput" placeholder="🔍 搜索..." oninput="onSearch()">
    </div>

    <!-- Event Type + Importance -->
    <div class="filter-row" id="eventTypeFilters"></div>
    <div class="filter-row" id="importanceFilters"></div>

    <!-- News Feed -->
    <div id="newsFeed"></div>
</div>

<footer class="footer">
    Donnees fournies par Google News · Filtees sur la France · Mise a jour quotidienne · v3
</footer>

<script id="articles-data" type="application/json">{articles_json}</script>
<script>
let ALL_ARTICLES = [];
const CATEGORIES = {categories_json};
const EVENT_TYPES = {event_types_json};
const PROVIDER_COLORS = {provider_colors_json};
const IMPORTANCE_COLORS = {importance_colors_json};
const GENERATED_AT = "{generated_at}";

let activeCategories = new Set(Object.keys(CATEGORIES));
let activeEventType = null;
let activeImportance = null;
let activeDateRange = "30d";
let searchText = "";
let filteredArticles = [];
let currentPage = 1;
let pageSize = 30;
let searchTimer = null;

function init() {{
    const dt = new Date(GENERATED_AT);
    document.getElementById("updateTime").textContent = "Derniere mise a jour : " + dt.toLocaleString("fr-FR", {{dateStyle:"full",timeStyle:"short"}});
    renderCatFilters();
    renderEventTypeFilters();
    renderImpFilters();
    applyFilters();
}}

// ── Category Filters ──
function renderCatFilters() {{
    const container = document.getElementById("catFilters");
    container.innerHTML = "";
    Object.entries(CATEGORIES).forEach(([key, info]) => {{
        const chip = document.createElement("span");
        chip.className = "filter-chip active";
        chip.textContent = info.icon + " " + info.label;
        chip.style.backgroundColor = info.color + "22";
        chip.style.borderColor = info.color;
        chip.style.color = info.color;
        chip.dataset.cat = key;
        chip.onclick = () => toggleCategory(key);
        container.appendChild(chip);
    }});
}}

function passesDateFilter(a) {{
    if (activeDateRange === "all") return true;
    const pd = a.published_date_short; if (!pd) return true;
    const pub = new Date(pd + "T00:00:00");
    const now = new Date();
    switch (activeDateRange) {{
        case "today": return pd === now.toISOString().slice(0,10);
        case "7d": pub.setDate(pub.getDate()+7); return pub >= now;
        case "30d": pub.setDate(pub.getDate()+30); return pub >= now;
        case "2026": return pd >= "2026-01-01" && pd < "2027-01-01";
        default: return true;
    }}
}}

// ── Event Type ──
function renderEventTypeFilters() {{
    const container = document.getElementById("eventTypeFilters");
    container.innerHTML = '<span class="filter-chip active" onclick="selectEventType(null)">全部类型</span>';
    Object.entries(EVENT_TYPES).forEach(([key, info]) => {{
        const chip = document.createElement("span");
        chip.className = "filter-chip active";
        chip.textContent = info.icon + " " + info.label;
        chip.style.backgroundColor = info.color + "33";
        chip.style.borderColor = info.color;
        chip.style.color = info.color;
        chip.dataset.etype = key;
        chip.onclick = () => selectEventType(key);
        container.appendChild(chip);
    }});
}}

// ── Importance ──
function renderImpFilters() {{
    const container = document.getElementById("importanceFilters");
    container.innerHTML = '<span class="filter-chip active" onclick="selectImportance(null)">全部重要度</span>';
    [{{level:"high",label:"★★★ 重要(>=75)",color:IMPORTANCE_COLORS.high}},
     {{level:"medium",label:"★★ 一般(45-74)",color:IMPORTANCE_COLORS.medium}},
     {{level:"low",label:"★ 低(<45)",color:IMPORTANCE_COLORS.low}}].forEach(item => {{
        const chip = document.createElement("span");
        chip.className = "filter-chip active";
        chip.textContent = item.label;
        chip.style.backgroundColor = item.color + "33";
        chip.style.borderColor = item.color + "66";
        chip.style.color = item.color;
        chip.dataset.imp = item.level;
        chip.onclick = () => selectImportance(item.level);
        container.appendChild(chip);
    }});
}}

// ── Search (debounced) ──
function onSearch() {{
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {{
        searchText = document.getElementById("searchInput").value.toLowerCase().trim();
        applyFilters();
    }}, 300);
}}

// ── Filters trigger applyFilters ──
function selectDateRange(range) {{
    activeDateRange = range;
    document.querySelectorAll("[data-range]").forEach(c => c.classList.toggle("active", c.dataset.range === range));
    applyFilters();
}}
function toggleCategory(cat) {{
    if (activeCategories.has(cat)) activeCategories.delete(cat); else activeCategories.add(cat);
    document.querySelectorAll("#catFilters .filter-chip").forEach(c => {{
        c.classList.toggle("active", activeCategories.has(c.dataset.cat));
        c.classList.toggle("inactive", !activeCategories.has(c.dataset.cat));
    }});
    applyFilters();
}}
function selectEventType(etype) {{
    activeEventType = etype;
    document.querySelectorAll("#eventTypeFilters .filter-chip").forEach(c => {{
        if (etype === null) {{ c.classList.add("active"); c.classList.remove("inactive"); }}
        else if (c.dataset.etype === etype) {{ c.classList.add("active"); c.classList.remove("inactive"); }}
        else {{ c.classList.remove("active"); c.classList.add("inactive"); }}
    }});
    applyFilters();
}}
function selectImportance(imp) {{
    activeImportance = imp;
    document.querySelectorAll("#importanceFilters .filter-chip").forEach(c => {{
        if (imp === null) {{ c.classList.add("active"); c.classList.remove("inactive"); }}
        else if (c.dataset.imp === imp) {{ c.classList.add("active"); c.classList.remove("inactive"); }}
        else {{ c.classList.remove("active"); c.classList.add("inactive"); }}
    }});
    applyFilters();
}}

// ── Apply Filters + Paginate ──
function applyFilters() {{
    filteredArticles = ALL_ARTICLES.filter(a => {{
        if (!activeCategories.has(a.category)) return false;
        if (activeEventType !== null && a.event_type !== activeEventType) return false;
        if (activeImportance !== null && a.importance !== activeImportance) return false;
        if (!passesDateFilter(a)) return false;
        if (searchText) {{
            var h = (a.title + " " + (a.summary||"") + " " + (a.source||"") + " " + ((a.entities||[]).map(function(e){{return e.display}}).join(" "))).toLowerCase();
            if (h.indexOf(searchText) === -1) return false;
        }}
        return true;
    }});
    currentPage = 1;
    renderPage();
}}

function esc(s) {{ return (s||"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;"); }}

function renderPage() {{
    var total = filteredArticles.length;
    var totalPages = Math.ceil(total / pageSize) || 1;
    if (currentPage > totalPages) currentPage = totalPages;
    var start = (currentPage - 1) * pageSize;
    var end = Math.min(start + pageSize, total);
    var pageArticles = filteredArticles.slice(start, end);

    var feed = document.getElementById("newsFeed");
    if (total === 0) {{
        feed.innerHTML = '<div class="empty-state"><div class="empty-icon">📭</div><p>Aucun article trouve</p></div>';
        return;
    }}

    var groups = {{}};
    Object.keys(CATEGORIES).forEach(function(k){{ groups[k] = []; }});
    pageArticles.forEach(function(a){{ if (groups[a.category]) groups[a.category].push(a); }});

    var html = '<div class="page-info">共 ' + total + ' 条，第 ' + currentPage + '/' + totalPages + ' 页</div>';

    Object.entries(CATEGORIES).forEach(function(entry) {{
        var cat = entry[0], catInfo = entry[1];
        var arts = groups[cat];
        if (!arts || arts.length === 0) return;

        html += '<div class="category-section">';
        html += '<div class="category-header"><h2>' + catInfo.icon + ' ' + catInfo.label + '</h2></div>';

        arts.forEach(function(a) {{
            var cardClass = a.importance === "high" ? "news-card card-high" : a.importance === "medium" ? "news-card card-medium" : "news-card";
            var cnTitle = a.title_zh || a.title_original || a.title || "";
            var cnSummary = a.summary_zh || a.summary_original || a.summary || "";
            var origTitle = a.title_original || a.title || "";
            var origSummary = a.summary_original || a.summary || "";
            var tUrl = a.translated_url || "";
            var etInfo = EVENT_TYPES[a.event_type] || EVENT_TYPES.general;

            html += '<div class="' + cardClass + '">';
            // Badges
            html += '<div class="card-badges">';
            html += '<span class="importance-stars" style="color:' + (IMPORTANCE_COLORS[a.importance]||"#6B7280") + '">' + (a.importance_stars||"★") + '</span>';
            html += '<span class="event-type-badge" style="background:' + etInfo.color + '">' + etInfo.icon + ' ' + etInfo.label + '</span>';
            if (a.provider) html += '<span class="provider-badge" style="background:' + (PROVIDER_COLORS[a.provider]||"#6B7280") + '">' + a.provider + '</span>';
            if (a.entities) a.entities.slice(0,2).forEach(function(e){{ html += '<span class="entity-tag" style="background:' + e.color + '">' + e.display + '</span>'; }});
            html += '<span class="score-badge">[' + (a.importance_score||0) + ']</span>';
            html += '</div>';

            // CN title
            html += '<div class="card-title-zh">' + esc(cnTitle) + '</div>';
            // Meta
            html += '<div class="card-meta"><span>' + esc(a.source||"") + '</span><span>' + (a.published_date_short||"") + '</span></div>';
            // CN summary
            if (cnSummary) html += '<div class="card-summary">' + esc(cnSummary) + '</div>';

            // 3 buttons
            html += '<div class="card-actions">';
            // 1. 中文速览 - inline expand
            html += '<details class="card-details-inline"><summary>📋 中文速览</summary>';
            html += '<div class="orig-title">' + esc(cnTitle) + '</div>';
            if (cnSummary) html += '<div class="orig-summary">' + esc(cnSummary) + '</div>';
            html += '</details>';
            // 2. 机翻原文
            if (tUrl) html += '<a href="' + tUrl + '" target="_blank" rel="noopener noreferrer" class="btn btn-translate">🌐 机翻原文</a>';
            // 3. 查看原文
            if (a.url) html += '<a href="' + a.url + '" target="_blank" rel="noopener noreferrer" class="btn btn-original">📄 查看原文</a>';
            html += '</div>';

            // Original title/summary expandable
            html += '<details class="card-details"><summary>📋 原文标题/摘要</summary>';
            html += '<div class="orig-title">' + esc(origTitle) + '</div>';
            if (origSummary) html += '<div class="orig-summary">' + esc(origSummary) + '</div>';
            html += '</details>';

            html += '</div>';
        }});
        html += '</div>';
    }});

    // Pagination controls
    html += '<div class="pagination">';
    html += '<button class="btn btn-original" onclick="changePage(1)" ' + (currentPage<=1?'disabled':'') + '>首页</button>';
    html += '<button class="btn btn-original" onclick="changePage(' + (currentPage-1) + ')" ' + (currentPage<=1?'disabled':'') + '>上一页</button>';
    html += '<span style="color:var(--text-muted);margin:0 8px">第 ' + currentPage + '/' + totalPages + ' 页</span>';
    html += '<button class="btn btn-original" onclick="changePage(' + (currentPage+1) + ')" ' + (currentPage>=totalPages?'disabled':'') + '>下一页</button>';
    html += '<button class="btn btn-original" onclick="changePage(' + totalPages + ')" ' + (currentPage>=totalPages?'disabled':'') + '>末页</button>';
    html += '<select onchange="changePageSize(this.value)" style="margin-left:12px;background:var(--bg-card);color:var(--text);border:1px solid var(--border);border-radius:6px;padding:4px 8px;font-size:12px">';
    [20,30,50,100].forEach(function(n){{ html += '<option value="' + n + '"' + (n===pageSize?' selected':'') + '>' + n + '条/页</option>'; }});
    html += '</select>';
    html += '</div>';

    feed.innerHTML = html;
    window.scrollTo(0,0);
}}

function changePage(n) {{ currentPage = n; renderPage(); }}
function changePageSize(n) {{ pageSize = parseInt(n); currentPage = 1; renderPage(); }}

// ── Boot ──
(function loadData() {{
    var dataEl = document.getElementById('articles-data');
    if (dataEl && dataEl.textContent && dataEl.textContent.trim()) {{
        ALL_ARTICLES = JSON.parse(dataEl.textContent);
        init();
    }} else {{
        fetch('data.json').then(r => r.json()).then(data => {{
            ALL_ARTICLES = data;
            init();
        }}).catch(e => {{
            document.getElementById('newsFeed').innerHTML = '<div class=\"empty-state\"><div class=\"empty-icon\">⚠️</div><p>Chargement echoue.</p></div>';
        }});
    }}
}})();

if ('serviceWorker' in navigator) {{
    navigator.serviceWorker.register('sw.js').then(r => console.log('SW:', r.scope)).catch(e => console.log('SW fail:', e));
}}
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════
# 7. OUTPUT
# ═══════════════════════════════════════════════════════════

def write_output(articles, output_path):
    data_dir = os.path.dirname(output_path)
    # Write data.json for fetch-based loading
    data_json_path = os.path.join(data_dir, "data.json")
    os.makedirs(data_dir, exist_ok=True)
    with open(data_json_path, "w", encoding="utf-8") as f:
        json.dump(articles, f, ensure_ascii=False)

    html_content = generate_html(articles)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"\n[OK] HTML written to: {output_path}")
    print(f"[OK] Data JSON: {data_json_path}")
    print(f"  Total: {len(articles)}")

    cats = {}
    for a in articles:
        cats[a["category"]] = cats.get(a["category"], 0) + 1
    for k, v in sorted(cats.items()):
        label = CATEGORIES.get(k, {}).get("label", k)
        print(f"  {label}: {v}")


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_path = os.path.join(base_dir, "docs", "index.html")
    history_path = os.path.join(base_dir, "data", "news_history.json")

    print("=" * 56)
    print("  French Cloud Ecosystem Tracker v3")
    print("=" * 56)
    print()

    # 1. Fetch
    articles = fetch_all()

    # 2. Merge with history
    history = load_history(history_path)
    articles = merge_with_history(articles, history)
    print(f"After history merge: {len(articles)}")

    # 3. Translate new articles (capped per run to avoid rate limits)
    translate_new_articles(articles, max_translations=50)

    # 4. Ensure all articles have translation fields (backward compat)
    for a in articles:
        ensure_translation_fields(a)

    # 6. Write output
    write_output(articles, output_path)

    # 7. Save history
    save_history(articles, history_path)
    print(f"[OK] History saved to: {history_path}")

    # 8. Telegram
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if bot_token and chat_id:
        send_telegram_digest(articles, bot_token, chat_id)


if __name__ == "__main__":
    main()
