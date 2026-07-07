# Walden Card Hunter

Automated eBay scanner for 1990s basketball insert opportunities.

## What it does

- Generates search queries from `players.csv` + `insert_sets.csv`
- Searches active eBay auction and fixed-price listings
- Filters obvious junk
- Uses `comps_cache.csv` when available
- Uses a default estimate when no comp exists yet
- Scores listings with a Walden Score
- Sends Telegram alerts

## GitHub Secrets Required

- `EBAY_CLIENT_ID`
- `EBAY_CLIENT_SECRET`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Manual Run

GitHub → Actions → Walden Card Hunter → Run workflow
