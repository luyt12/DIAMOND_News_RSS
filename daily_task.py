"""
DIAMOND 每日任务入口脚本
每天只翻译当天最新的 3 篇文章，避免单次翻译内容过长
"""
import os
import re
from datetime import datetime
import pytz

tz_est = pytz.timezone('America/New_York')
today = datetime.now(tz_est).strftime("%Y%m%d")

# Step 1: 抓取新闻
print("Step 1: 抓取新闻...")
import rss_parser
rss_parser.main()

# Step 2: 只翻译今日最新的 3 篇文章
print("Step 2: 翻译今日最新 3 篇文章...")
dailynews_file = os.path.join("dailynews", f"{today}.md")

if not os.path.exists(dailynews_file):
    print(f"No today's news file: {dailynews_file}")
    # 列出可用的文件
    import glob
    files = sorted(glob.glob("dailynews/*.md"))
    print(f"Available: {files[-5:]}")
else:
    import translate_news

    with open(dailynews_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # 按分隔符分割文章
    raw_articles = content.split('---')

    # 过滤出有效的文章块
    articles = []
    for raw in raw_articles:
        raw = raw.strip()
        if not raw:
            continue
        # 提取发布日期来验证是今天的
        m = re.search(r'(\d{4}-\d{2}-\d{2})', raw)
        if m:
            articles.append((m.group(1), raw))
        elif raw.startswith('#') or len(raw) > 100:
            # 没有日期但有内容的也保留
            articles.append(('unknown', raw))

    print(f"Total articles parsed: {len(articles)}")

    # 取最新的 3 篇
    top3 = articles[-3:]
    print(f"Translating latest {len(top3)} articles")
    for date, _ in top3:
        title_m = re.search(r'# (.+)', _)
        title = title_m.group(1)[:40] if title_m else 'unknown'
        print(f"  - [{date}] {title}...")

    combined = '\n\n---\n\n'.join(a for _, a in top3)
    temp_file = os.path.join("dailynews", f"{today}_top3.md")
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(combined)
    print(f"Written temp file: {temp_file}")

    success = translate_news.translate_file(temp_file)

    # 翻译结果写入 translate/{today}.md
    translate_dir = "translate"
    os.makedirs(translate_dir, exist_ok=True)
    translate_output = os.path.join(translate_dir, f"{today}.md")
    translated_temp = os.path.join(translate_dir, f"{today}_top3.md")

    if success and os.path.exists(translated_temp):
        with open(translated_temp, 'r', encoding='utf-8') as f:
            new_content = f.read()

        # 追加模式
        if os.path.exists(translate_output):
            with open(translate_output, 'r', encoding='utf-8') as f:
                existing = f.read()
            combined_trans = existing + '\n\n---\n\n' + new_content
        else:
            combined_trans = new_content

        with open(translate_output, 'w', encoding='utf-8') as f:
            f.write(combined_trans)
        print(f"[OK] Translated saved: {translate_output}")

        os.remove(translated_temp)
    else:
        print("[ERR] Translation failed")

    os.remove(temp_file)

# Step 3: 发送今日邮件
print("Step 3: 发送今日邮件...")
translate_path = os.path.join("translate", f"{today}.md")
if os.path.exists(translate_path):
    import send_email
    send_email.main(translate_path)
else:
    print(f"No translated file for today: {translate_path}")

print("Done!")
