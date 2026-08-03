# SmartPriceBot

Telegram bot that checks product prices, remembers prior results, and notifies you when a price changes or reaches your target. It is prepared for these parts:

- Mobil 1 5W-20 motor oil
- WIX 57060 oil filter
- Mopar 68191349AC oil filter

The project is deliberately configurable: choose the Ukrainian shops and paste their product links into `config/products.toml`. It can be expanded with Ukrainian Railways ticket tracking without changing the price-tracking core.

## 1. Create the Telegram bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather).
2. Send `/newbot`, follow its prompts, and copy the token it gives you.
3. Start a chat with your new bot and send `/id`. It will reply with your numeric chat ID.

## 2. Add the store links

Open `config/products.toml` and put a product-page URL in each `url` field. The supplied entries are templates for the exact parts above. Add more `[[products]]` sections to track other shops or pack sizes.

Most ordinary store pages work without further configuration because the bot reads Schema.org JSON-LD, meta tags, and common price elements. If a shop uses a non-standard page, inspect its page HTML and set `price_selector` to a CSS selector, for example:

```toml
price_selector = ".product-price__value"
```

`target_price_uah` is optional. A notification is sent when a price is at or below it.

## 3. Run locally

Requires Python 3.11 or later.

```bash
git clone https://github.com/YOUR-ACCOUNT/SmartPriceBot.git
cd SmartPriceBot
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

Fill `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_IDS` in `.env`, then run:

```bash
python -m smartpricebot.main bot
```

Commands:

- `/check` — check all configured products now
- `/status` — show the latest saved prices
- `/products` — list the configured products
- `/id` — display the current chat ID (useful during setup)
- `/help` — command help

To test one price check without starting the Telegram bot:

```bash
python -m smartpricebot.main check
```

## 4. Run automatically with GitHub Actions

1. Upload this whole folder to a new GitHub repository (do **not** upload `.env`).
2. In the repository, open **Settings → Secrets and variables → Actions**.
3. Create these repository secrets:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_IDS`
4. Go to **Actions**, enable workflows if GitHub asks, and run **Track prices** once with **Run workflow**.

The workflow checks every three hours and commits the price history back to the repository. You can change the schedule in `.github/workflows/track-prices.yml`. GitHub scheduled jobs can sometimes start later than their exact scheduled time; use the manual run for an immediate check.

## How it works

1. The scraper reads each configured product URL and finds a price using JSON-LD, OpenGraph/product meta tags, or your `price_selector`.
2. `data/price_history.json` stores the most recent known price and a compact price history.
3. Alerts are sent only for a first successful check, a changed price, or a target price reached. Unchanged values remain quiet.

Prices may be missing or blocked by shops that render content only with JavaScript, require login, or present anti-bot verification. For those stores, use a shop's official API if available, a different retailer, or add a dedicated adapter in `smartpricebot/sources/`.

## Project structure

```text
smartpricebot/
  config.py              Configuration and environment parsing
  scraper.py             Generic HTML / JSON-LD price extraction
  tracker.py             Price comparison, history and notifications
  telegram_bot.py        Telegram commands
  ukrainian_railways.py  Extension point for ticket alerts
config/products.toml     Products and store URLs to track
.github/workflows/       Scheduled GitHub Action
```

## Ukrainian Railways extension

`smartpricebot/ukrainian_railways.py` contains a small provider interface and a ticket-watch model. Add an official, permitted data source there, then schedule it alongside `PriceTracker`. This avoids mixing transport-query logic into the price scraper.

## Security

Never commit `.env`, a bot token, or your chat ID. GitHub Actions receives credentials only from repository secrets. If a token is exposed, revoke it via @BotFather and create a new one.
