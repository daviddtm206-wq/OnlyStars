# OnlyStars Bot - Telegram OnlyFans Platform

## Overview
This is a Telegram bot that allows creators to sell exclusive content using Telegram Stars (⭐️). The platform supports monthly subscriptions, pay-per-view content, tips, and includes an admin panel with a 20% platform commission.

## Recent Changes
- September 9, 2025: Successfully imported from GitHub and set up for Replit environment
- Fixed import issues for proper module resolution
- Integrated payment router with main handlers
- Configured deployment for VM target (always-on bot)
- Implemented complete feature set: creator registration, PPV content, tips, admin panel
- Added FSM (Finite State Machine) for interactive flows
- Enhanced payment system to handle subscriptions, PPV, and tips

## Project Architecture
- **Language**: Python 3.11
- **Framework**: aiogram 3.12.0 (Telegram Bot API library)
- **Database**: SQLite with tables for creators, transactions, and subscribers
- **Environment**: Configured with all necessary environment variables

### File Structure
```
bot/
├── main.py              # Bot entry point with FSM storage
├── handlers.py          # Main command handlers (start, help)
├── payments.py          # Payment processing (subscriptions, PPV, tips)
├── creator_handlers.py  # Creator registration and management
├── admin_handlers.py    # Administrator functions
├── ppv_handlers.py      # Pay-per-view content handlers
├── database.py          # SQLite database operations
└── __init__.py          # Package initialization

.env                     # Environment variables
requirements.txt         # Python dependencies
```

### Key Features
- **Creator Registration**: Interactive flow for creator onboarding
- **Monthly Subscriptions**: Using Telegram Stars with automatic billing
- **PPV Content**: Pay-per-view photos and videos
- **Tips System**: Direct tips to creators
- **Admin Panel**: Full administrative controls and statistics
- **Payment Processing**: Automatic commission calculation (20%)
- **User Management**: Ban system and user verification
- **Database**: SQLite with tables for creators, transactions, subscribers, PPV content
- **FSM Support**: Interactive conversational flows

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

## Available Commands

### For Everyone:
- `/start` - Welcome message and command overview
- `/help` - Complete command list

### For Creators:
- `/convertirme_en_creador` - Interactive creator registration
- `/mi_perfil` - View profile and statistics
- `/balance` - Check balance and withdrawal options
- `/retirar <amount>` - Withdraw earnings
- `/crear_contenido_ppv` - Create pay-per-view content

### For Fans:
- `/explorar_creadores` - Browse available creators
- `/suscribirme_a <creator_id>` - Subscribe to a creator
- `/comprar_ppv <content_id>` - Purchase PPV content
- `/enviar_propina <creator_id> <amount>` - Send tips

### For Admins:
- `/admin_panel` - View platform statistics
- `/banear_usuario <user_id>` - Ban users
- `/stats` - Detailed platform analytics

The bot handles all payment processing automatically using Telegram Stars with 20% platform commission.