# Walden Card Hunter v2

Modular scanner for 1990s basketball inserts.

## Files
- `scanner.py` - main scanner runner
- `catalog_generate_watchlist.py` - creates `watchlist.csv` from `card_catalog.csv`
- `comp_manager.py` - creates a missing comps report
- `wch/` - modular app code

## GitHub Secrets Required
- `EBAY_CLIENT_ID`
- `EBAY_CLIENT_SECRET`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

## Workflow Modes
- `scanner`
- `test_sold_comps`
- `test_sold_endpoint`
- `comp_manager`
