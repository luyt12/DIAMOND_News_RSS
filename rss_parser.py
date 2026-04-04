"""
DIAMOND RSS Parser
鎶撳彇 Yahoo News Japan - Diamond 棰戦亾褰撳ぉ鏂囩珷锛屾瘡绡囩嫭绔嬩繚瀛?娴佺▼锛氬姞杞藉凡鍙戣褰?鈫?鍙彇褰撳ぉ鍊欓€?鈫?鍙栧墠N绡?鈫?鎶撳彇鍐呭 鈫?淇濆瓨
"""
import feedparser
import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime
import os
import time
import logging
import json

# --- 閰嶇疆 ---
RSS_URL = "https://news.yahoo.co.jp/rss/media/diamond/all.xml"
OUTPUT_DIR = "dailynews"
SENT_FILE = "sent_articles.json"
MAX_DAILY = 10
TIMEZONE_TOKYO = pytz.timezone('Asia/Tokyo')
TIMEZONE_GMT = pytz.utc

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_sent():
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f).get("sent", []))
        except Exception:
            pass
    return set()


def parse_gmt_date(parsed_struct):
    if not parsed_struct:
        return None
    try:
        import calendar
        timestamp = calendar.timegm(parsed_struct)
        return TIMEZONE_GMT.localize(datetime.utcfromtimestamp(timestamp))
    except Exception as e:
        logging.error(f"瑙ｆ瀽鏃ユ湡鍑洪敊: {e}")
        return None


def is_today_tokyo(dt_tokyo):
    if not dt_tokyo:
        return False
    now = datetime.now(TIMEZONE_TOKYO)
    return (dt_tokyo.year == now.year and
            dt_tokyo.month == now.month and
            dt_tokyo.day == now.day)


def scrape_article_content(url):
    """鎶撳彇鍗曠瘒鏂囩珷瀹屾暣鍐呭锛堝彧鎶撲竴绡囷級"""
    try:
        base_url = url.replace("?source=rss", "")
        full_content = ""
        page_num = 1

        while True:
            page_url = f"{base_url}?page={page_num}"
            logging.info(f"  鎶撳彇绗瑊page_num}椤? {page_url}")
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            resp = requests.get(page_url, headers=headers, timeout=15)

            if resp.status_code == 404:
                logging.info(f"  绗瑊page_num}椤典笉瀛樺湪锛岀粨鏉熷垎椤?)
                break
            if resp.status_code != 200:
                logging.error(f"  鎶撳彇澶辫触: {resp.status_code}")
                break

            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, 'html.parser')

            article_body = (
                soup.find('div', class_=lambda x: x and 'article_body' in x.lower()) or
                soup.find('article') or
                soup.find('div', id='uamods-pickup') or
                soup.find('div', class_='articleBody')
            )

            if not article_body:
                if page_num == 1:
                    body_text = soup.body.get_text(separator='\n', strip=True) if soup.body else ""
                    return (body_text[:2000] + "...") if body_text else "鏃犳硶鎻愬彇鍐呭"
                break

            for tag in article_body(['script', 'style', 'a']):
                tag.decompose()

            paragraphs = article_body.find_all('p')
            page_content = '\n'.join(p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)) if paragraphs else article_body.get_text(separator='\n', strip=True)

            if page_num > 1:
                full_content += "\n\n"
            full_content += page_content

            page_num += 1
            time.sleep(0.5)

        return full_content.strip() if full_content else "鏃犳硶鎶撳彇鏂囩珷鍐呭銆?
    except Exception as e:
        logging.error(f"鎶撳彇澶辫触 {url}: {e}")
        return "鏃犳硶鎶撳彇鏂囩珷鍐呭銆?


def main():
    logging.info("寮€濮嬪鐞?DIAMOND RSS...")

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    sent_urls = load_sent()
    logging.info(f"宸插彂閫佽褰? {len(sent_urls)} 绡?)

    # Step 1: 瑙ｆ瀽 RSS锛岃幏鍙栧綋澶╁€欓€夛紙涓嶆姄鍐呭锛屽彧鍙栧厓鏁版嵁锛?    try:
        feed_data = feedparser.parse(RSS_URL)
    except Exception as e:
        logging.error(f"鑾峰彇 RSS 澶辫触: {e}")
        return

    if feed_data.bozo:
        logging.warning(f"RSS 鏍煎紡寮傚父: {feed_data.bozo_exception}")

    if not feed_data.entries:
        logging.info("RSS 涓棤鏉＄洰")
        return

    logging.info(f"RSS 鍏?{len(feed_data.entries)} 鏉?)

    candidates = []
    for entry in feed_data.entries:
        link = entry.link.strip()

        # 鍘婚噸
        if link in sent_urls:
            logging.info(f"宸插彂閫佽繃锛岃烦杩? {entry.title}")
            continue

        pub_parsed = entry.get('published_parsed')
        if not pub_parsed:
            continue

        dt_gmt = parse_gmt_date(pub_parsed)
        if not dt_gmt:
            continue

        dt_tokyo = dt_gmt.astimezone(TIMEZONE_TOKYO)
        if not is_today_tokyo(dt_tokyo):
            continue

        candidates.append({
            'title': entry.title,
            'link': link,
            'published_tokyo_str': dt_tokyo.strftime('%Y-%m-%d %H:%M:%S'),
            'published_tokyo_dt': dt_tokyo,
        })

    if not candidates:
        logging.info("浠婃棩鏃犳柊鏂囩珷")
        return None

    # Step 2: 鎸夊彂甯冩椂闂存帓搴忥紙鏈€鏂扮殑鍦ㄥ墠锛?    candidates.sort(key=lambda x: x['published_tokyo_dt'], reverse=True)

    # Step 3: 鎴彇鏁伴噺涓婇檺
    top = candidates[:MAX_DAILY]
    logging.info(f"鍊欓€夋枃绔?{len(candidates)} 绡囷紝鎴彇鍓?{len(top)} 绡?)

    # Step 4: 鍙姄杩?top 绡囩殑鍐呭
    today_str = top[0]['published_tokyo_dt'].strftime('%Y%m%d')
    saved_files = []

    for i, article in enumerate(top):
        logging.info(f"鎶撳彇鏂囩珷 ({i+1}/{len(top)}): {article['title']}")
        article['content'] = scrape_article_content(article['link'])
        time.sleep(0.5)

        # 淇濆瓨鐙珛鏂囦欢
        filename = f"{today_str}_art{i + 1}.md"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("# " + article['title'] + "\n\n")
            f.write(f"*鍙戝竷鏃堕棿: {article['published_tokyo_str']}*\n")
            f.write(f"[鍘熸枃閾炬帴]({article['link']})\n\n")
            f.write(article['content'] + "\n")

        logging.info(f"淇濆瓨: {filepath}")
        saved_files.append((filepath, article['link']))

    # 淇濆瓨鑱氬悎鏂囦欢锛堟柟渚胯皟璇曪級
    agg_file = os.path.join(OUTPUT_DIR, f"{today_str}.md")
    with open(agg_file, "w", encoding="utf-8") as f:
        f.write(f"# DIAMOND {today_str} 鏂伴椈 ({len(top)} 绡?\n\n---\n\n")
        for article in top:
            f.write(f"## {article['title']}\n\n")
            f.write(f"*鍙戝竷鏃堕棿: {article['published_tokyo_str']}*\n")
            f.write(f"[鍘熸枃閾炬帴]({article['link']})\n\n")
            f.write(f"{article['content']}\n\n---\n\n")

    logging.info(f"瀹屾垚锛屽叡淇濆瓨 {len(saved_files)} 绡囨枃绔?)
    return saved_files


if __name__ == "__main__":
    main()
