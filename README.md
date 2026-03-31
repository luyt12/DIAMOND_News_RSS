# DIAMOND Finance Daily Email

Automated daily email digest of DIAMOND (Diamond Online) Japanese financial news, translated to Chinese via Kimi K2.5 AI.

## How It Works

1. Fetches latest articles from Diamond Online RSS feed (via Yahoo Japan News)
2. Scrapes full article content page by page
3. Translates Japanese content to Chinese using Kimi K2.5 (NVIDIA API)
4. Sends a formatted HTML email daily

## Schedule

Runs automatically every day at 03:00 UTC via GitHub Actions.

## Setup

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `KIMI_API_KEY` | Kimi K2.5 API key (NVIDIA endpoint) |
| `SMTP_PASS` | SMTP password / app password |
| `EMAIL_TO` | Recipient email address |
| `EMAIL_FROM` | Sender email address |
| `SMTP_HOST` | SMTP server hostname |
| `SMTP_PORT` | SMTP server port |
| `SMTP_USER` | SMTP login username |

### Manual Trigger

Go to **Actions** tab → **Daily DIAMOND Email** → **Run workflow**.

## Tech Stack

- Python 3.11
- GitHub Actions (scheduled)
- Kimi K2.5 via NVIDIA API
- BeautifulSoup4 for article scraping
- SMTP over TLS (port 465)
