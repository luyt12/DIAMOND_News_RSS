import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

today = datetime.now().strftime('%Y-%m-%d')

report = f"""馃摪 姣忔棩绠€鎶?鈥?{today}

================================================================
馃實 鍦扮紭鏀挎不锛氱編浼婃垬浜夛紙绗?0澶╋級
----------------------------------------------------------------------
鈥?缇庡浗鍜屼互鑹插垪鑱斿悎鎵撳嚮浼婃湕澧冨唴鍐涗簨鐩爣锛屼互鑹插垪琚嚮浜嗗崡甯曞皵鏂ぉ鐒舵皵鐢?鈥?娌逛环椋欏崌 鈥?鍏ㄧ悆鑳芥簮甯傚満鍙楀埌閲嶅ぇ鍐插嚮
鈥?鐗规湕鏅細"涓嶄細鍚戜紛鏈楁淳閬ｅ湴闈㈤儴闃?
鈥?鏍稿績鎯呮姤鎽樿锛氱編浠ュ啿绐佺20澶╋紝缇庡啗娣卞叆鎵撳嚮浼婃湕澧冨唴鍐涗簨鐩爣锛屼互鑹插垪琚嚮鍗楀笗灏旀柉姘旂敯瀵艰嚧鑳芥簮浠锋牸鏆存定銆?
馃搸 鏉ユ簮锛?  - CNN: https://www.cnn.com/2026/03/19/middleeast/us-israel-iran-middle-east-war-day-20-what-we-know-intl-hnk
  - Al Jazeera: https://www.aljazeera.com/video/newsfeed/2026/3/20/unpacking-netanyahus-latest-claims-about-the-war-on-iran
  - Fox News: https://www.foxnews.com/video/6391246686112

----------------------------------------------------------------------
馃 AI 涓庣鎶€
----------------------------------------------------------------------
鈥?AI 鍩虹璁炬柦蹇€熸墿寮?鈥?Cerebras 鐧婚檰 AWS銆丯VIDIA 寮€鏀炬暟鎹鍒?鈥?2026骞?鏈堝涓柊 AI 妯″瀷鍙戝竷锛涘垵鍒涘叕鍙稿彈鐩婁簬鍩虹璁炬柦鏀瑰杽
鈥?鏍稿績鎯呮姤鎽樿锛欰I 鍩虹璁炬柦蹇€熸墿寮狅紝澶氫釜鏂版ā鍨嬪拰鍚堜綔椤圭洰娑岀幇锛屽寘鎷?Cerebras 涓?AWS 鐨勫悎浣滀互鍙?NVIDIA 鐨勫紑鏀炬暟鎹鍒掋€?
馃搸 鏉ユ簮锛?  - Mean CEO: https://blog.mean.ceo/new-ai-model-releases-news-march-2026/
  - Radical Data Science: https://radicaldatascience.wordpress.com/2026/03/17/ai-news-briefs-bulletin-board-for-march-2026/

----------------------------------------------------------------------
馃嚭馃嚫 缇庡浗鏀挎不
----------------------------------------------------------------------
鈥?鐗规湕鏅?鏈?0鏃ヤ細瑙佸鍥介瀵间汉锛岀缃查拡瀵逛紛鏈楃殑鏂拌鏀夸护
鈥?鍑哄腑澹叺閬椾綋褰掑浗浠紡锛涗紛鏈楁垬浜夋垚涓虹浜屼换鏈熸牳蹇冭棰?鈥?鏍稿績鎯呮姤鎽樿锛?鏈?0鏃ョ壒鏈楁櫘浼氳鍥介檯棰嗗浜猴紝绛剧讲閽堝浼婃湕濞佽儊鐨勮鏀夸护锛屽苟鍑哄腑浼や骸灏嗗＋褰掑浗浠紡銆?
馃搸 鏉ユ簮锛?  - CNN: https://www.cnn.com/politics/president-donald-trump-47
  - AP News: https://apnews.com/hub/donald-trump
  - 鐧藉: https://www.whitehouse.gov/videos/president-trump-participates-in-a-bilateral-meeting-mar-19-2026/

----------------------------------------------------------------------
馃挵 甯傚満涓庣粡娴?----------------------------------------------------------------------
鈥?閬撴寚3鏈?0鏃ヤ笂娑?00+鐐癸紝鏍囨櫘500涓婃定
鈥?鏍囨櫘500鏃╀簺鏃跺€欏洜浼婃湕鐭虫补鍗辨満鍒涘勾鍐呮柊浣?鈥?娌逛环缁存寔楂樹綅锛汵vidia 鍜屾补浠锋槸鍗庡皵琛楀叧娉ㄧ劍鐐?鈥?鍏ㄧ悆15%鍏崇◣鐢熸晥 鈥?甯傚満娉㈠姩鎸佺画

馃搸 鏉ユ簮锛?  - CNBC: https://www.cnbc.com/2026/03/03/stock-market-today-live-updates.html
  - CNBC: https://www.cnbc.com/2026/03/12/stock-market-today-live-updates.html

================================================================
鐢?OpenClaw Agent 鐢熸垚 | Tavily Search API 椹卞姩
"""

print("=== 姣忔棩绠€鎶ラ偖浠跺彂閫?===")
print(f"鏀朵欢浜? HZ-lu2007@outlook.com")
print(f"涓婚: 姣忔棩绠€鎶?{today}")
print("")

# Check for SMTP credentials in .env
env_path = r"C:\Program Files\QClaw\resources\openclaw\config\skills\imap-smtp-email\.env"
smtp_host = None
smtp_user = None
smtp_pass = None
smtp_port = 587
smtp_from = None

if os.path.exists(env_path):
    print("鎵惧埌 SMTP 閰嶇疆鏂囦欢...")
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if line.startswith('#') or '=' not in line:
                continue
            k, v = line.split('=', 1)
            k = k.strip()
            v = v.strip()
            if k == 'SMTP_HOST': smtp_host = v
            elif k == 'SMTP_PORT': smtp_port = int(v)
            elif k == 'SMTP_USER': smtp_user = v
            elif k == 'SMTP_PASS': smtp_pass = v
            elif k == 'SMTP_FROM': smtp_from = v

    print(f"  SMTP_HOST: {'宸查厤缃? if smtp_host else '鏈厤缃?}")
    print(f"  SMTP_USER: {'宸查厤缃? if smtp_user else '鏈厤缃?}")
    print(f"  SMTP_PASS: {'宸查厤缃? if smtp_pass else '鏈厤缃?}")
else:
    print("鏈壘鍒?SMTP 閰嶇疆鏂囦欢")

if not all([smtp_host, smtp_user, smtp_pass]):
    print("")
    print("SMTP 鏈畬鏁撮厤缃紝璺宠繃鍙戦€併€傛棩鎶ュ唴瀹瑰涓嬶細")
    print(report)
else:
    try:
        print("\n姝ｅ湪杩炴帴 SMTP 鏈嶅姟鍣?..")
        msg = MIMEMultipart()
        msg['From'] = smtp_from or smtp_user
        msg['To'] = 'HZ-lu2007@outlook.com'
        msg['Subject'] = f"姣忔棩绠€鎶?{today}"
        msg.attach(MIMEText(report, 'plain', 'utf-8'))

        server = smtplib.SMTP(smtp_host, smtp_port)
        server.ehlo()
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, ['HZ-lu2007@outlook.com'], msg.as_string())
        server.quit()

        print("鉁?閭欢鍙戦€佹垚鍔?")
    except Exception as e:
        print(f"鉂?鍙戦€佸け璐? {e}")
        print("")
        print("鏃ユ姤鍐呭锛?)
        print(report)
