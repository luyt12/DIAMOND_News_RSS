import os
import sys
import logging
import requests
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

KIMI_API_KEY = os.getenv("KIMI_API_KEY")
KIMI_MODEL = os.getenv("KIMI_MODEL", "moonshotai/kimi-k2.5")
KIMI_API_URL = os.getenv("KIMI_API_URL", "https://integrate.api.nvidia.com/v1/chat/completions")

INPUT_DIR = "dailynews"
OUTPUT_DIR = "translate"

PROMPT = """You are a professional financial news editor. Please complete the following task on the Japanese article below:

## Task: Extract and Summarize
Extract key points from the article and write a Chinese summary with these requirements:
1. No need to translate the full text - extract key points directly from the Japanese
2. High information density - cover main points, background, and significance
3. Keep key details (names, institutions, data)
4. Word count: if original > 2000 English words, Chinese summary ~1000 characters (~50% of original); if < 2000 words, can translate fully
5. Concise style, avoid "This article discusses..." filler
6. Stay neutral on controversial topics

## Output Format
Output the Chinese summary directly, no introductions or meta-comments."""


def summarize_and_translate(content):
    if not KIMI_API_KEY:
        logging.error("KIMI_API_KEY not set")
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
            logging.info(f"Submitting summarize+translate (attempt {attempt + 1}/5)...")
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
                logging.error(f"API response error: {result}")
                if attempt < 4:
                    time.sleep(30 * (2 ** attempt))
        except requests.exceptions.Timeout:
            logging.error(f"API timeout (attempt {attempt + 1}/5)")
            if attempt < 4:
                time.sleep(30 * (2 ** attempt))
        except Exception as e:
            logging.error(f"Request failed: {e}")
            if attempt < 4:
                time.sleep(30 * (2 ** attempt))
    return None


def translate_file(filepath):
    if not os.path.exists(filepath):
        logging.error(f"File not found: {filepath}")
        return False

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    outpath = os.path.join(OUTPUT_DIR, os.path.basename(filepath))

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    logging.info(f"Starting summarize+translate: {filepath} ({len(content)} chars)")
    result = summarize_and_translate(content)

    if result:
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(result)
        logging.info(f"Done: {outpath} ({len(result)} chars)")
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
            files = sorted(glob.glob(os.path.join(INPUT_DIR, sys.argv[1])))
            for f in files:
                translate_file(f)
    else:
        files = sorted(glob.glob(os.path.join(INPUT_DIR, "*.md")))
        if files:
            for f in files:
                translate_file(f)
        else:
            logging.error("No article files found")
