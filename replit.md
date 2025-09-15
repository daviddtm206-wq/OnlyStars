# OnlyStars Bot - Telegram OnlyFans Platform

## Overview
This is a Telegram bot that allows creators to sell exclusive content using Telegram Stars (⭐️). The platform supports monthly subscriptions, pay-per-view content, tips, and includes an admin panel with a 20% platform commission.

## Recent Changes
- **September 15, 2025**: 
  - ✅ Fresh clone imported and fully configured for Replit environment
  - ✅ Moved sensitive credentials (BOT_TOKEN, ADMIN_USERNAME) to secure Replit Secrets
  - ✅ Fixed requirements.txt to remove duplicates and ensure deterministic deployments
  - ✅ Added BOT_TOKEN validation with fail-fast behavior for better error handling
  - ✅ Configured database as runtime artifact (removed from version control)
  - ✅ Set up VM deployment target for always-on bot functionality
  - ✅ Validated all dependencies and bot polling functionality
  - **NEW**: ✅ Implemented complete hierarchical navigation system with organized menu structure
  - **NEW**: ✅ Integrated nav_handlers.py for clean menu navigation with back button functionality
  - **NEW**: ✅ Resolved handler conflicts between legacy and hierarchical navigation systems
  - **NEW**: ✅ Updated /start command to use NavigationManager for proper state management
- September 9, 2025: Successfully imported from GitHub and set up for Replit environment
- Fixed import issues for proper module resolution
- Integrated payment router with main handlers
- Configured deployment for VM target (always-on bot)
- Implemented complete feature set: creator registration, PPV content, tips, admin panel
- Added FSM (Finite State Machine) for interactive flows
- Enhanced payment system to handle subscriptions, PPV, and tips
- **NEW**: Added profile editing functionality for creators with /editar_perfil command
- **September 12, 2025**: Added complete catalog system for creators with /mis_catalogos command
- **NEW**: Implemented personalized PPV catalogs per creator with professional channel-like interface
- **NEW**: Added support for FREE subscriptions (0 ⭐️ stars) for creators

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
- **Creator Registration**: Interactive flow for creator onboarding (supports FREE subscriptions)
- **Monthly Subscriptions**: Using Telegram Stars with automatic billing or FREE (0 ⭐)
- **Private Catalogs**: Personalized PPV catalogs per creator (channel-like interface)
- **PPV Content**: Pay-per-view photos and videos with secure paywall
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

## User Preferences
- **Language**: Always respond in Spanish (Siempre responder en español)

## Current State
✅ Bot is running and connected to Telegram (@Onlyfans2408bot)
✅ Python 3.11 installed with aiogram 3.12.0
✅ All dependencies installed and configured (requirements.txt cleaned)
✅ Database initialization working (SQLite runtime creation)
✅ Payment system integrated with Telegram Stars
✅ Deployment configured for production (VM target)
✅ Secrets properly secured in Replit environment
✅ BOT_TOKEN validation and error handling implemented
✅ Workflow running successfully with proper polling

## Available Commands

### For Everyone:
- `/start` - Welcome message and command overview
- `/help` - Complete command list

### For Creators:
- `/convertirme_en_creador` - Interactive creator registration
- `/mi_perfil` - View profile and statistics
- `/editar_perfil` - Edit profile information (name, description, price, photo)
- `/balance` - Check balance and withdrawal options
- `/retirar <amount>` - Withdraw earnings
- `/crear_contenido_ppv` - Create pay-per-view content

### For Fans:
- `/explorar_creadores` - Browse available creators
- `/suscribirme_a <creator_id>` - Subscribe to a creator (free or paid)
- `/mis_catalogos` - View exclusive catalogs from subscribed creators
- `/comprar_ppv <content_id>` - Purchase PPV content
- `/enviar_propina <creator_id> <amount>` - Send tips

### For Admins:
- `/admin_panel` - View platform statistics
- `/banear_usuario <user_id>` - Ban users
- `/stats` - Detailed platform analytics

The bot handles all payment processing automatically using Telegram Stars with 20% platform commission.