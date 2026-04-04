"""
DIAMOND 姣忔棩浠诲姟鍏ュ彛鑴氭湰
姣忓ぉ鎶撳彇鏂伴椈锛岀炕璇戝綋澶╂渶鏂扮殑3绡囨枃绔狅紝姣忕瘒鍗曠嫭鍙戦€佷竴灏侀偖浠?"""
import os
import re
import glob
from datetime import datetime
import pytz

tz_est = pytz.timezone("America/New_York")
today = datetime.now(tz_est).strftime("%Y%m%d")

# Step 1: 鎶撳彇鏂伴椈
print("Step 1: 鎶撳彇鏂伴椈...")
import rss_parser
rss_parser.main()

# Step 2: 璇诲彇褰撳ぉ鏂伴椈锛屾媶鍒嗘垚3绡囩嫭绔嬫枃浠讹紝鍒嗗埆缈昏瘧锛屾瘡绡囧彂涓€灏侀偖浠?print("Step 2: 缈昏瘧骞跺彂閫佸綋鏃?绡囨枃绔?..")
dailynews_file = os.path.join("dailynews", today + ".md")

import translate_news

if not os.path.exists(dailynews_file):
    files = sorted(glob.glob("dailynews/*.md"))
    if not files:
        print("No dailynews file found at all")
    else:
        dailynews_file = files[-1]
        print("Using latest: " + dailynews_file)

if os.path.exists(dailynews_file):
    with open(dailynews_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 鎸?"---" 鍒嗛殧鎴愮嫭绔嬫枃绔?    raw_articles = content.split("---")
    articles = []
    for raw in raw_articles:
        raw = raw.strip()
        if not raw or len(raw) < 50:
            continue
        articles.append(raw)

    print("Total articles: " + str(len(articles)))

    # 鍙栨渶鏂?绡囷紙鏁扮粍鏈熬3涓級
    top3 = articles[-3:] if len(articles) >= 3 else articles
    print("Translating " + str(len(top3)) + " articles")

    import send_email

    success_count = 0
    for i, art in enumerate(top3):
        art_num = i + 1
        # 淇濆瓨涓虹嫭绔嬫枃浠讹紙鍙惈杩欎竴绡囷級
        single_file = os.path.join("dailynews", today + "_art" + str(art_num) + ".md")
        with open(single_file, "w", encoding="utf-8") as f:
            f.write(art)
        print("Saved article " + str(art_num) + ": " + single_file)

        # 缈昏瘧
        ok = translate_news.translate_file(single_file)
        if not ok:
            print("Translation failed for article " + str(art_num))
            # 娓呯悊涓存椂鏂囦欢
            if os.path.exists(single_file):
                os.remove(single_file)
            continue

        # 缈昏瘧缁撴灉璺緞
        translated_file = os.path.join("translate", today + "_art" + str(art_num) + ".md")

        # 娓呯悊鍘熷涓存椂鏂囦欢
        if os.path.exists(single_file):
            os.remove(single_file)

        # 鍙戦€侀偖浠?        if os.path.exists(translated_file):
            try:
                send_email.main(translated_file)
                print("Email sent for article " + str(art_num))
                success_count += 1
            except Exception as e:
                print("Email send error: " + str(e))
            # 缈昏瘧鍚庣殑涓存椂鏂囦欢涔熸竻鐞?            try:
                os.remove(translated_file)
            except Exception:
                pass
        else:
            print("Translated file not found: " + translated_file)

    print("Successfully sent " + str(success_count) + "/" + str(len(top3)) + " emails")
else:
    print("No dailynews file found: " + dailynews_file)

print("Done!")
