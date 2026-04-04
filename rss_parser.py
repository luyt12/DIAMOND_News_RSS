"""
DIAMOND RSS Parser
鎶撳彇 Yahoo News Japan - Diamond 棰戦亾褰撳ぉ鏂囩珷锛屾瘡绡囩嫭绔嬩繚瀛?"""
import feedparser
import requests
from bs4 import BeautifulSoup
import pytz
from datetime import datetime
import os
import time
import logging
import re
import json
import glob

# --- 閰嶇疆 ---
RSS_URL = "https://news.yahoo.co.jp/rss/media/diamond/all.xml"
OUTPUT_DIR = "dailynews"
SENT_FILE = "sent_articles.json"
MAX_DAILY = 10
TIMEZONE_TOKYO = pytz.timezone('Asia/Tokyo')
TIMEZONE_GMT = pytz.utc

# --- 鏃ュ織璁剧疆 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def load_sent():
    """鍔犺浇宸插彂閫佽褰?""
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f).get("sent", []))
        except Exception:
            pass
    return set()


def save_sent(urls):
    """淇濆瓨宸插彂閫佽褰?""
    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump({"sent": list(urls)}, f, ensure_ascii=False, indent=2)


def parse_gmt_date(parsed_struct):
    if not parsed_struct:
        return None
    try:
        import calendar
        timestamp = calendar.timegm(parsed_struct)
        dt_naive = datetime.utcfromtimestamp(timestamp)
        return TIMEZONE_GMT.localize(dt_naive)
    except Exception as e:
        logging.error(f"瑙ｆ瀽鏃ユ湡鍑洪敊: {e}")
        return None


def convert_to_tokyo(dt_gmt):
    if dt_gmt and dt_gmt.tzinfo:
        return dt_gmt.astimezone(TIMEZONE_TOKYO)
    elif dt_gmt:
        return TIMEZONE_GMT.localize(dt_gmt).astimezone(TIMEZONE_TOKYO)
    return None


def is_today_tokyo(dt_tokyo):
    if not dt_tokyo:
        return False
    now = datetime.now(TIMEZONE_TOKYO)
    return (dt_tokyo.year == now.year and
            dt_tokyo.month == now.month and
            dt_tokyo.day == now.day)


def scrape_article_content(url):
    """鎶撳彇鎸囧畾 URL 鐨勬枃绔犲畬鏁村唴瀹?""
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
                logging.error(f"  鎶撳彇澶辫触锛岀姸鎬佺爜: {resp.status_code}")
                break

            resp.encoding = resp.apparent_encoding
            soup = BeautifulSoup(resp.text, 'html.parser')

            # 瀹氫綅鏂囩珷涓讳綋
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

            # 绉婚櫎鑴氭湰銆佹牱寮忋€侀摼鎺?            for tag in article_body(['script', 'style', 'a']):
                tag.decompose()

            paragraphs = article_body.find_all('p')
            if paragraphs:
                parts = [p.get_text(strip=True) for p in paragraphs]
                page_content = '\n'.join(p for p in parts if p)
            else:
                page_content = article_body.get_text(separator='\n', strip=True)

            if page_num > 1:
                full_content += "\n\n"
            full_content += page_content

            page_num += 1
            time.sleep(0.5)

        return full_content.strip() if full_content else "鏃犳硶鎶撳彇鏂囩珷鍐呭銆?
    except Exception as e:
        logging.error(f"鎶撳彇鏂囩珷澶辫触 {url}: {e}")
        return "鏃犳硶鎶撳彇鏂囩珷鍐呭銆?


def format_single_article(article):
    """鏍煎紡鍖栧崟绡囨枃绔?""
    lines = []
    lines.append("# " + article['title'])
    lines.append("*鍙戝竷鏃堕棿: " + article['published_tokyo_str'] + "*")
    lines.append("[鍘熸枃閾炬帴](" + article['link'] + ")")
    lines.append("")
    if article['content']:
        lines.append(article['content'])
    return "\n".join(lines)


def main():
    logging.info("寮€濮嬪鐞?DIAMOND RSS...")

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    # 鍔犺浇宸插彂閫佽褰?    sent_urls = load_sent()
    logging.info(f"宸插彂閫佽褰? {len(sent_urls)} 绡?)

    # 瑙ｆ瀽 RSS
    try:
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

    today_articles = []
    for entry in feed_data.entries:
        title = entry.title
        link = entry.link.strip()

        # 鍘婚噸
        if link in sent_urls:
            logging.info(f"宸插彂閫佽繃锛岃烦杩? {title}")
            continue

        pub_parsed = entry.get('published_parsed')
        if not pub_parsed:
            continue

        dt_gmt = parse_gmt_date(pub_parsed)
        if not dt_gmt:
            continue

        dt_tokyo = convert_to_tokyo(dt_gmt)
        if not dt_tokyo:
            continue

        if not is_today_tokyo(dt_tokyo):
            continue

        logging.info(f"澶勭悊鏂囩珷: {title}")
        content = scrape_article_content(link)
        time.sleep(0.5)

        today_articles.append({
            'title': title,
            'link': link,
            'published_tokyo_str': dt_tokyo.strftime('%Y-%m-%d %H:%M:%S %Z%z'),
            'published_tokyo_dt': dt_tokyo,
            'content': content
        })

    if not today_articles:
        logging.info("浠婃棩鏃犳柊鏂囩珷")
        return

    # 鎸夊彂甯冩椂闂存帓搴忥紙鏈€鏂扮殑鍦ㄥ墠锛?    today_articles.sort(key=lambda x: x['published_tokyo_dt'], reverse=True)

    # 鍙栨渶澶?MAX_DAILY 绡?    today_articles = today_articles[:MAX_DAILY]
    today_str = today_articles[0]['published_tokyo_dt'].strftime('%Y%m%d')

    logging.info(f"浠婃棩鏂版枃绔犲叡 {len(today_articles)} 绡囷紝寮€濮嬩繚瀛?..")

    # 淇濆瓨姣忕瘒鏂囩珷涓虹嫭绔嬫枃浠?    saved_files = []
    for i, article in enumerate(today_articles):
        filename = f"{today_str}_art{i + 1}.md"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(format_single_article(article))
        logging.info(f"淇濆瓨: {filepath}")
        saved_files.append((filepath, article['link']))

    # 鍚屾椂淇濆瓨鑱氬悎鏂囦欢锛堟柟渚胯皟璇曪級
    agg_file = os.path.join(OUTPUT_DIR, f"{today_str}.md")
    with open(agg_file, "w", encoding="utf-8") as f:
        f.write(f"# DIAMOND {today_str} 鏂伴椈 ({len(today_articles)} 绡?\n\n")
        for i, article in enumerate(today_articles):
            f.write(format_single_article(article))
            f.write("\n\n---\n\n")

    logging.info(f"鍏变繚瀛?{len(saved_files)} 绡囨枃绔?)
    return saved_files


if __name__ == "__main__":
    main()
