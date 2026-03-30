"""
DIAMOND 每日任务入口脚本
每天只翻译当天最新的 3 篇文章标题+摘要，避免内容过长
"""
import os
import re
import glob
from datetime import datetime
import pytz

tz_est = pytz.timezone("America/New_York")
today = datetime.now(tz_est).strftime("%Y%m%d")

# Step 1: 抓取新闻
print("Step 1: 抓取新闻...")
import rss_parser
rss_parser.main()

# Step 2: 只翻译今日最新 3 篇文章（仅标题+摘要，不含全文）
print("Step 2: 翻译今日最新 3 篇文章（标题+摘要）...")
dailynews_file = os.path.join("dailynews", today + ".md")

import translate_news

if not os.path.exists(dailynews_file):
    print("No today file: " + dailynews_file)
    files = sorted(glob.glob("dailynews/*.md"))
    print("Available: " + str(files[-5:]))
else:
    with open(dailynews_file, "r", encoding="utf-8") as f:
        content = f.read()

    # 按文章分割（每篇文章以 "## 文章" 或 "标题：" 开头）
    # DIAMOND rss_parser 格式：每篇文章之间用 "---" 分隔
    raw_articles = content.split("---")
    articles = []
    for raw in raw_articles:
        raw = raw.strip()
        if not raw or len(raw) < 50:
            continue
        articles.append(raw)

    print("Total articles: " + str(len(articles)))

    # 取最新的 3 篇
    top3 = articles[-3:]
    print("Using latest " + str(len(top3)) + " articles")

    # 只保留每篇文章的前 500 字符（标题+摘要），去掉全文
    truncated = []
    for art in top3:
        lines = art.split("\n")
        # 取前 10 行或 500 字符，以较小者为准
        short = "\n".join(lines[:10])
        if len(short) > 500:
            short = short[:500] + "..."
        truncated.append(short)

    combined = "\n\n---\n\n".join(truncated)
    print("Combined length: " + str(len(combined)) + " chars")

    temp_file = os.path.join("dailynews", today + "_top3.md")
    with open(temp_file, "w", encoding="utf-8") as f:
        f.write(combined)

    success = translate_news.translate_file(temp_file)

    # 翻译结果写入 translate/{today}.md
    os.makedirs("translate", exist_ok=True)
    translate_output = os.path.join("translate", today + ".md")
    translated_temp = os.path.join("translate", today + "_top3.md")

    if success and os.path.exists(translated_temp):
        with open(translated_temp, "r", encoding="utf-8") as f:
            new_content = f.read()
        if os.path.exists(translate_output):
            with open(translate_output, "r", encoding="utf-8") as f:
                existing = f.read()
            combined_trans = existing + "\n\n---\n\n" + new_content
        else:
            combined_trans = new_content
        with open(translate_output, "w", encoding="utf-8") as f:
            f.write(combined_trans)
        print("Translated saved: " + translate_output)
        os.remove(translated_temp)
    else:
        print("Translation failed")

    if os.path.exists(temp_file):
        os.remove(temp_file)

# Step 3: 发送今日邮件
print("Step 3: 发送今日邮件...")
translate_path = os.path.join("translate", today + ".md")
if not os.path.exists(translate_path):
    t_files = sorted(glob.glob("translate/*.md"))
    if t_files:
        translate_path = t_files[-1]
        print("Using latest: " + translate_path)
    else:
        translate_path = None

if translate_path and os.path.exists(translate_path):
    import send_email
    send_email.main(translate_path)
else:
    print("No translate file, skip email")

print("Done!")
