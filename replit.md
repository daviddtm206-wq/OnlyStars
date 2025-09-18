# OnlyStars Bot - Telegram OnlyFans Platform

## Overview
This is a Telegram bot that allows creators to sell exclusive content using Telegram Stars (⭐️). The platform supports monthly subscriptions, pay-per-view content, tips, and includes an admin panel with a 20% platform commission.

## Recent Changes
- **September 18, 2025**:
  - ✅ Fresh GitHub import successfully configured for Replit environment
  - ✅ Python 3.11 installed with all required dependencies
  - ✅ Fixed duplicate dependencies in requirements.txt for clean builds
  - ✅ Set up workflow for continuous Telegram bot operation
  - ✅ Configured VM deployment target for always-on bot functionality
  - ⚠️ **SETUP REQUIRED**: Bot token and secrets need to be configured in Replit Secrets
  - **NEW**: ✅ **TRANSFORMACIÓN COMPLETA: Catálogo Profesional Estilo Canal**
    - Eliminados mensajes de encabezado y fin de catálogo no deseados
    - Reescrita función keyboard_my_catalog para mostrar posts individuales reales
    - Implementada visualización profesional con fotos/videos completos para cada contenido
    - Agregados botones de gestión en cada post (editar, estadísticas, eliminar, cambiar precio)
    - Soporte completo para álbumes con MediaGroupBuilder
    - Interfaz ahora se ve como un canal tradicional de Telegram para creadores
    - Handlers implementados para todas las funciones de gestión de contenido
    - Formato profesional con información detallada de precio y tipo de contenido
- **September 15, 2025**: 
  - ✅ Fresh clone imported and fully configured for Replit environment
  - ✅ Moved ALL sensitive credentials to secure Replit Secrets (BOT_TOKEN, ADMIN_USERNAME, COMMISSION_PERCENTAGE, DEFAULT_CURRENCY, EXCHANGE_RATE, MIN_WITHDRAWAL, WITHDRAWAL_MODE)
  - ✅ Fixed requirements.txt to remove duplicates and ensure deterministic deployments
  - ✅ Added BOT_TOKEN validation with fail-fast behavior for better error handling
  - ✅ Configured database as runtime artifact (removed from version control)
  - ✅ Set up VM deployment target for always-on bot functionality
  - ✅ Validated all dependencies and bot polling functionality
  - ✅ Removed .env file for security (now using Replit Secrets)
  - ✅ Python 3.11 environment properly installed with aiogram 3.12.0
  - ✅ Bot successfully running and polling (@Onlyfans2408bot)
  - **NEW**: ✅ Implemented complete hierarchical navigation system with organized menu structure
  - **NEW**: ✅ Integrated nav_handlers.py for clean menu navigation with back button functionality
  - **NEW**: ✅ Resolved handler conflicts between legacy and hierarchical navigation systems
  - **NEW**: ✅ Updated /start command to use NavigationManager for proper state management
  - **NEW**: ✅ **MAJOR IMPROVEMENT: Professional Button-Based Creator Registration**
    - Fixed "Registrarme como Creador" button to start registration directly (no more commands)
    - Implemented complete button-based registration flow with professional UI
    - Added confirmation buttons for name and description steps
    - Created professional price selection with predefined options (FREE, 50⭐, 100⭐, 200⭐, 500⭐, 1000⭐)
    - Added elegant photo upload/skip buttons with helpful tips
    - Integrated cancel registration option at every step
    - Enhanced user experience with step-by-step guidance and validation
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
- **September 17, 2025**: ✅ **CRITICAL FIX: Albums in PPV Catalogs**
  - Fixed album detection bug in catalog display (incorrect field index)
  - Albums now properly appear in catalogs using sendPaidMedia native integration
  - Corrected album_type field indexing from content[8] to content[7]
  - All content types (single photos/videos and albums) now display correctly

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
✅ Python 3.11 environment fully configured and tested
✅ All dependencies properly installed (aiogram 3.12.0, python-dotenv)
✅ Database initialization working (SQLite runtime creation)
✅ Workflow configured for continuous bot operation
✅ VM deployment configured for always-on functionality
✅ Requirements.txt cleaned up (removed duplicates)
⚠️ **Setup Required**: Configure BOT_TOKEN and other secrets in Replit Secrets
⚠️ **Next Step**: Add BOT_TOKEN from @BotFather to make bot operational

## Required Secrets Configuration
The following secrets need to be added to Replit Secrets:
- `BOT_TOKEN` - Get this from @BotFather on Telegram
- `ADMIN_USERNAME` - Telegram username for platform administrator (e.g. @username)
- `COMMISSION_PERCENTAGE` - Platform commission rate (recommended: 20)
- `DEFAULT_CURRENCY` - Currency code (use: XTR for Telegram Stars)
- `EXCHANGE_RATE` - Exchange rate (recommended: 0.013)
- `MIN_WITHDRAWAL` - Minimum withdrawal amount (recommended: 1000)
- `WITHDRAWAL_MODE` - Withdrawal mode (use: REAL)

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