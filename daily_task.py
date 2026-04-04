"""
DIAMOND 姣忔棩浠诲姟鍏ュ彛
鎶撳彇褰撳ぉ鏂囩珷 鈫?鍘婚噸锛堟渶澶?0绡囷級鈫?鎻愮偧瑕佺偣+缈昏瘧 鈫?姣忕瘒鐙珛鍙戦€侀偖浠?"""
import os
import glob
import json
from datetime import datetime
import pytz

tz_tokyo = pytz.timezone("Asia/Tokyo")
today_str = datetime.now(tz_tokyo).strftime("%Y%m%d")

SENT_FILE = "sent_articles.json"


def load_sent():
    if os.path.exists(SENT_FILE):
        try:
            with open(SENT_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f).get("sent", []))
        except Exception:
            pass
    return set()


def save_sent(urls):
    with open(SENT_FILE, "w", encoding="utf-8") as f:
        json.dump({"sent": list(urls)}, f, ensure_ascii=False, indent=2)


# Step 1: 鎶撳彇褰撳ぉ鏂囩珷锛堝凡鍖呭惈鍘婚噸+鏈€澶?0绡囷紝杩斿洖 [(filepath, url), ...]锛?print("Step 1: 鎶撳彇褰撳ぉ鏂囩珷...")
import rss_parser
saved = rss_parser.main()

if not saved:
    print("浠婃棩鏃犳柊鏂囩珷锛岄€€鍑?)
    exit(0)

print(f"鎶撳彇鍒?{len(saved)} 绡囨柊鏂囩珷")

# Step 2: 鍔犺浇宸插彂閫佽褰曪紝骞惰拷鍔犱粖鏃?URL
sent_urls = load_sent()
for _, url in saved:
    sent_urls.add(url)

# Step 3: 鎵惧埌浠婃棩鏂囩珷鏂囦欢锛堢敱 rss_parser 淇濆瓨鐨勶級
today_files = sorted(glob.glob(os.path.join("dailynews", today_str + "_art*.md")))
if not today_files:
    print("鏈壘鍒颁粖鏃ユ枃绔犳枃浠?)
    exit(1)

print(f"寮€濮嬪鐞?{len(today_files)} 绡囨枃绔?..")

# Step 4: 鎻愮偧+缈昏瘧锛屾瘡绡囧彂閫侀偖浠?import translate_news
import send_email

success_count = 0
for filepath in today_files:
    print(f"\n澶勭悊: {os.path.basename(filepath)}")

    # 鎻愮偧+缈昏瘧
    ok = translate_news.translate_file(filepath)
    if not ok:
        print(f"  缈昏瘧澶辫触")
        continue

    # 缈昏瘧缁撴灉璺緞
    basename = os.path.basename(filepath)
    translated_file = os.path.join("translate", basename)

    if not os.path.exists(translated_file):
        print(f"  缈昏瘧鏂囦欢涓嶅瓨鍦? {translated_file}")
        continue

    # 鍙戦€侀偖浠?    try:
        send_email.main(translated_file)
        print(f"  閭欢宸插彂閫?)
        success_count += 1
    except Exception as e:
        print(f"  閭欢鍙戦€佸け璐? {e}")

    # 鍒犻櫎缈昏瘧涓存椂鏂囦欢
    try:
        os.remove(translated_file)
    except Exception:
        pass

# Step 5: 淇濆瓨宸插彂閫佽褰?save_sent(sent_urls)
print(f"\n瀹屾垚锛氭垚鍔熷彂閫?{success_count}/{len(today_files)} 灏侀偖浠?)
