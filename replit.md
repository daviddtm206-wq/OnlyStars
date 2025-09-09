# OnlyStars Bot - Telegram OnlyFans Platform

## Overview
This is a Telegram bot that allows creators to sell exclusive content using Telegram Stars (⭐️). The platform supports monthly subscriptions, pay-per-view content, tips, and includes an admin panel with a 20% platform commission.

## Recent Changes
- September 9, 2025: Successfully imported from GitHub and set up for Replit environment
- Fixed import issues for proper module resolution
- Integrated payment router with main handlers
- Configured deployment for VM target (always-on bot)

## Project Architecture
- **Language**: Python 3.11
- **Framework**: aiogram 3.12.0 (Telegram Bot API library)
- **Database**: SQLite with tables for creators, transactions, and subscribers
- **Environment**: Configured with all necessary environment variables

### File Structure
```
bot/
├── main.py           # Bot entry point and configuration
├── handlers.py       # Main command handlers (start, etc.)
├── payments.py       # Payment processing with Telegram Stars
├── database.py       # SQLite database operations
└── __init__.py       # Package initialization

.env                  # Environment variables (bot token, admin, etc.)
requirements.txt      # Python dependencies
```

### Key Features
- Monthly subscriptions using Telegram Stars
- Payment processing with automatic commission calculation (20%)
- SQLite database for user data and transactions
- Admin functionality
- Support for creators and subscribers

### Environment Configuration
- BOT_TOKEN: Telegram bot token from BotFather
- ADMIN_USERNAME: Platform administrator
- COMMISSION_PERCENTAGE: Platform commission (20%)
- DEFAULT_CURRENCY: XTR (Telegram Stars)
- EXCHANGE_RATE: 0.013
- MIN_WITHDRAWAL: 1000 stars
- WITHDRAWAL_MODE: REAL

## Current State
✅ Bot is running and connected to Telegram (@Onlyfans2408bot)
✅ All dependencies installed and configured
✅ Database initialization working
✅ Payment system integrated
✅ Deployment configured for production

The bot is ready for use and can handle:
- /start command for welcome message
- /suscribirme_a <creator_id> for subscriptions
- Payment processing through Telegram Stars