"""
DIAMOND 财经邮件发送脚本
"""
import os
import sys
import smtplib
import ssl
import glob
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# 直接从环境变量读取
EMAIL_TO = os.getenv("EMAIL_TO", "HZ-lu2007@outlook.com")
EMAIL_FROM = os.getenv("EMAIL_FROM", "kimberagent@163.com")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.163.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER", "kimberagent@163.com")
SMTP_PASS = os.getenv("SMTP_PASS", "")

TRANSLATE_DIR = "translate"
MAX_ARTICLES = 10


def read_translate_file(filepath):
    """读取翻译后的 Markdown 文件"""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception:
        return None


def format_email_html(content, date_str):
    """格式化为 HTML 邮件"""
    # 简单解析 Markdown
    sections = content.split('---')
    articles_html = []

    for i, section in enumerate(sections):
        section = section.strip()
        if not section:
            continue

        lines = section.split('\n')
        title = ""
        link = ""
        body_lines = []

        for line in lines:
            line = line.strip()
            if line.startswith('## '):
                title = line[3:].strip()
            elif line.startswith('标题：') or line.startswith('# '):
                title = line.lstrip('# 标题：').strip()
            elif line.startswith('链接：') or line.startswith('https://'):
                if line.startswith('链接：'):
                    link = line[3:].strip()
                else:
                    link = line.strip()
            elif line and not line.startswith('-'):
                body_lines.append(line)

        body = '\n\n'.join(body_lines)
        body_html = body.replace('\n\n', '</p><p>').replace('\n', '<br>')
        if body_html:
            body_html = f'<p>{body_html}</p>'

        link_html = f'<a href="{link}">阅读原文</a>' if link else ''

        articles_html.append(f"""
        <div style="margin-bottom: 35px; padding-bottom: 25px; border-bottom: 1px solid #e0e0e0;">
            <h2 style="color: #1a1a1a; font-size: 18px; margin: 0 0 10px 0;">{i+1}. {title}</h2>
            <div style="font-size: 14px; line-height: 1.7; color: #444;">
                {body_html}
            </div>
            <div style="margin-top: 12px; font-size: 13px;">
                {link_html}
            </div>
        </div>
        """)

    display_date = datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; background: #f5f5f5; }}
        .container {{ background: #fff; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .header {{ border-bottom: 3px solid #c41230; padding-bottom: 15px; margin-bottom: 30px; }}
        h1 {{ color: #c41230; margin: 0; font-size: 24px; }}
        .date {{ color: #666; font-size: 14px; margin-top: 5px; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #e0e0e0; font-size: 12px; color: #888; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>DIAMOND 财经每日新闻</h1>
            <div class="date">{display_date}</div>
        </div>
        <div class="content">
            {''.join(articles_html)}
        </div>
        <div class="footer">此邮件由 OpenClaw Agent 自动发送</div>
    </div>
</body>
</html>"""
    return html


def send_email(html_content, date_str):
    """发送 HTML 邮件"""
    if not SMTP_PASS:
        print("[ERR] SMTP_PASS 未设置")
        return False

    display_date = datetime.strptime(date_str, "%Y%m%d").strftime("%Y-%m-%d")
    subject = f"DIAMOND 财经每日新闻 - {display_date}"

    msg = MIMEMultipart()
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO
    msg['Subject'] = subject
    msg.attach(MIMEText(html_content, 'html', 'utf-8'))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
        print(f"[OK] 邮件已发送至 {EMAIL_TO}")
        return True
    except Exception as e:
        print(f"[ERR] 邮件发送失败: {e}")
        return False


def main(filepath=None):
    """主函数"""
    if filepath is None:
        if len(sys.argv) > 1:
            filepath = sys.argv[1]
        else:
            print("[ERR] 未指定文件路径")
            return False

    # 从文件路径解析日期
    filename = os.path.basename(filepath)
    date_str = filename.replace('.md', '').replace('translate/', '')

    content = read_translate_file(filepath)
    if not content or not content.strip():
        print(f"[WARN] 翻译文件为空或不存在: {filepath}")
        return False

    print(f"读取翻译文件: {filepath} ({len(content)} 字符)")

    html = format_email_html(content, date_str)
    return send_email(html, date_str)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
