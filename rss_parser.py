"""
DIAMOND RSS Parser
Fetch today articles, dedup, save each separately.
新特性：当日无文章时，自动回退到历史未处理文章。
"""
import feedparser, requests, pytz, json, time, logging, os
from bs4 import BeautifulSoup
from datetime import datetime

RSS_URL = "https://news.yahoo.co.jp/rss/media/diamond/all.xml"
OUTPUT_DIR = "dailynews"
SENT_FILE = "sent_articles.json"
MAX_DAILY = 10
TZ_TOKYO = pytz.timezone("Asia/Tokyo")
TZ_GMT = pytz.utc

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def load_sent():
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f).get("sent", []))
        except Exception:
            pass
    return set()


def parse_gmt(ps):
    if not ps:
        return None
    try:
        import calendar
        return TZ_GMT.localize(datetime.utcfromtimestamp(calendar.timegm(ps)))
    except Exception:
        return None


def is_today(dt):
    if not dt:
        return False
    now = datetime.now(TZ_TOKYO)
    return dt.year == now.year and dt.month == now.month and dt.day == now.day


def fetch_content(url):
    try:
        base = url.replace("?source=rss", "")
        full = ""
        page = 1
        while True:
            page_url = "%s?page=%s" % (base, page)
            logging.info("Fetching page %s: %s", page, page_url)
            resp = requests.get(page_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
            if resp.status_code == 404:
                logging.info("Page %s not found, done", page)
                break
            if resp.status_code != 200:
                logging.error("Fetch failed: %s", resp.status_code)
                break
            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, "html.parser")
            body = (
                soup.find("div", class_=lambda x: x and "article_body" in x.lower()) or
                soup.find("article") or
                soup.find("div", id="uamods-pickup") or
                soup.find("div", class_="articleBody")
            )
            if not body:
                if page == 1:
                    txt = soup.body.get_text(separator="\n", strip=True) if soup.body else ""
                    return (txt[:2000] + "...") if txt else "Could not extract"
                break
            for tag in body(["script", "style", "a"]):
                tag.decompose()
            paras = body.find_all("p")
            content = "\n".join(p.get_text(strip=True) for p in paras if p.get_text(strip=True)) if paras else body.get_text(separator="\n", strip=True)
            if page > 1:
                full += "\n\n"
            full += content
            page += 1
            time.sleep(0.5)
        return full.strip() if full else "Could not fetch content"
    except Exception as e:
        logging.error("Fetch failed %s: %s", url, e)
        return "Could not fetch content"


def main():
    logging.info("Starting DIAMOND RSS...")
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    sent_urls = load_sent()
    logging.info("Already sent: %s articles", len(sent_urls))

    try:
        feed_data = feedparser.parse(RSS_URL)
    except Exception as e:
        logging.error("Failed to get RSS: %s", e)
        return

    if feed_data.bozo:
        logging.warning("RSS format warning: %s", feed_data.bozo_exception)
    if not feed_data.entries:
        logging.info("RSS has no entries")
        return

    logging.info("RSS total: %s entries", len(feed_data.entries))

    # 解析所有文章
    all_articles = []
    for entry in feed_data.entries:
        link = entry.link.strip()
        ps = entry.get("published_parsed")
        if not ps:
            continue
        dt_gmt = parse_gmt(ps)
        if not dt_gmt:
            continue
        dt_tokyo = dt_gmt.astimezone(TZ_TOKYO)
        all_articles.append({
            "title": entry.title,
            "link": link,
            "pub_str": dt_tokyo.strftime("%Y-%m-%d %H:%M:%S"),
            "pub_dt": dt_tokyo,
            "is_today": is_today(dt_tokyo)
        })

    logging.info("RSS 共 %s 篇文章", len(all_articles))

    # 优先今日文章，无则回退到历史未处理
    today_articles = [a for a in all_articles if a["is_today"] and a["link"] not in sent_urls]
    logging.info("今日新文章: %s 篇", len(today_articles))

    if today_articles:
        candidates = today_articles
        logging.info("→ 使用今日文章: %s 篇", len(candidates))
    else:
        # 回退到历史未处理文章
        historical = [a for a in all_articles if a["link"] not in sent_urls]
        logging.info("→ 今日无文章，回退到历史未处理: %s 篇", len(historical))
        candidates = historical

    if not candidates:
        logging.info("无新文章")
        return None

    candidates.sort(key=lambda x: x["pub_dt"], reverse=True)
    top = candidates[:MAX_DAILY]
    logging.info("Candidates: %s, limited to top %s", len(candidates), len(top))

    today_str = top[0]["pub_dt"].strftime("%Y%m%d")
    saved = []

    for i, article in enumerate(top):
        logging.info("Fetching article (%s/%s): %s", i + 1, len(top), article["title"])
        article["content"] = fetch_content(article["link"])
        time.sleep(0.5)

        fname = "%s_art%s.md" % (today_str, i + 1)
        fpath = os.path.join(OUTPUT_DIR, fname)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write("# " + article["title"] + "\n\n")
            f.write("*Published: " + article["pub_str"] + "*\n")
            f.write("[Source](" + article["link"] + ")\n\n")
            f.write(article.get("content", "") + "\n")
        logging.info("Saved: %s", fpath)
        saved.append((fpath, article["link"]))

    agg = os.path.join(OUTPUT_DIR, today_str + ".md")
    with open(agg, "w", encoding="utf-8") as f:
        f.write("# DIAMOND %s (%s articles)\n\n---\n\n" % (today_str, len(top)))
        for article in top:
            f.write("## " + article["title"] + "\n\n")
            f.write("*Published: " + article["pub_str"] + "*\n")
            f.write("[Source](" + article["link"] + ")\n\n")
            f.write(article.get("content", "") + "\n\n---\n\n")

    logging.info("Done, saved %s articles", len(saved))
    return saved


if __name__ == "__main__":
    main()
