"""
DIAMOND 鏂囩珷缈昏瘧鍣?
鍏堟彁鐐艰鐐癸紝鍐嶇炕璇戜负绠€浣撲腑鏂?
姣忕瘒鏂囩珷杈撳嚭 300-500 瀛楃殑涓枃鎽樿
"""
import os
import sys
import logging
import requests
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

KIMI_API_KEY = os.getenv("kimi_API_KEY")
KIMI_MODEL = os.getenv("KIMI_MODEL", "moonshotai/kimi-k2.5")
KIMI_API_URL = os.getenv("KIMI_API_URL", "https://integrate.api.nvidia.com/v1/chat/completions")

INPUT_DIR = "dailynews"
OUTPUT_DIR = "translate"

# 鍏堟彁鐐艰鐐癸紝鍐嶇炕璇戜负涓枃
PROMPT = """浣犳槸涓€浣嶄笓涓氱殑璐㈢粡鏂伴椈缂栬緫銆傝瀵逛互涓嬫棩鏈储缁忔枃绔犲畬鎴愪袱姝ヤ换鍔★細

## 绗竴姝ワ細鎻愮偧瑕佺偣
浠旂粏闃呰鍘熸枃锛屾彁鍙栨渶鏍稿績鐨勪俊鎭偣锛?
- 鏂囩珷璁ㄨ鐨勬牳蹇冭棰樻槸浠€涔堬紵
- 鏈夊摢浜涘叧閿暟鎹€佹暟瀛椼€佹帓鍚嶏紵
- 涓昏瑙傜偣鎴栫粨璁烘槸浠€涔堬紵
- 瀵硅鑰呮渶閲嶈鐨勫惎绀烘槸浠€涔堬紵

## 绗簩姝ワ細缈昏瘧骞剁患杩?
灏嗘彁鐐肩殑瑕佺偣缈昏瘧涓虹畝浣撲腑鏂囷紝鍐欎綔瑕佹眰锛?
1. 杈撳嚭 300-500 瀛楃殑涓枃鎽樿
2. 浣跨敤 Markdown 鏍煎紡锛屼簩绾ф爣棰樹负鏂囩珷鏍囬
3. 鍦ㄦ爣棰樹笅鏂规敞鏄庡師鏂囬摼鎺?
4. 鍑嗙‘鎬э細蹇犲疄鍘熸枃锛屼笉閬楁紡鍏抽敭鏁板瓧鍜岀粨璁?
5. 娴佺晠鎬э細绗﹀悎鐜颁唬绠€浣撲腑鏂囪〃杈撅紝閬垮厤缈昏瘧鑵?
6. 绠€娲佹€э細涓诲姩鎷嗗垎闀垮彞锛岀簿鐐肩敤璇?

## 杈撳嚭鏍煎紡
鐩存帴杈撳嚭涓枃鎽樿锛屼笉瑕佸姞鍏ヤ换浣曟棤鍏冲唴瀹癸紝涓嶈鍐?浠ヤ笅鏄憳瑕?涔嬬被鐨勫墠瑷€"""


def summarize_and_translate(content):
    """璋冪敤 Kimi API 鎻愮偧瑕佺偣骞剁炕璇?""
    if not KIMI_API_KEY:
        logging.error("kimi_API_KEY not set")
        sys.exit(1)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {KIMI_API_KEY}"
    }
    data = {
        "model": KIMI_MODEL,
        "messages": [
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": content}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    for attempt in range(5):
        try:
            logging.info(f"[log]")
            resp = requests.post(
                KIMI_API_URL,
                headers=headers,
                json=data,
                timeout=300
            )
            resp.raise_for_status()
            result = resp.json()
            if result.get("choices") and result["choices"][0]:
                return result["choices"][0]["message"]["content"]
            else:
                logging.error(f"[log]")
                if attempt < 4:
                    time.sleep(30 * (2 ** attempt))
        except requests.exceptions.Timeout:
            logging.error(f"[log]")
            if attempt < 4:
                time.sleep(30 * (2 ** attempt))
        except Exception as e:
            logging.error(f"[log]")
            if attempt < 4:
                time.sleep(30 * (2 ** attempt))
    return None


def translate_file(filepath):
    """缈昏瘧鍗曚釜鏂囦欢"""
    if not os.path.exists(filepath):
        logging.error(f"[log]")
        return False

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    outpath = os.path.join(OUTPUT_DIR, os.path.basename(filepath))

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    logging.info(f"[log]")

    result = summarize_and_translate(content)

    if result:
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(result)
        logging.info(f"[log]")
        return True
    else:
        logging.error("Translation failed")
        return False


if __name__ == "__main__":
    import glob
    if len(sys.argv) > 1:
        if os.path.isfile(sys.argv[1]):
            translate_file(sys.argv[1])
        else:
            # 鎸夋枃浠跺悕妯″紡缈昏瘧
            pattern = os.path.join(INPUT_DIR, sys.argv[1])
            files = sorted(glob.glob(pattern))
            for f in files:
                translate_file(f)
    else:
        files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.md")))
        if files:
            for f in files:
                translate_file(f)
        else:
            logging.error("No article files found")
