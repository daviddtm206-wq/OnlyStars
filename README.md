# 🌟 OnlyStars-Bot — Tu plataforma OnlyFans en Telegram con Telegram Stars

## 🚀 Descripción

Bot de Telegram que permite a múltiples creadores vender contenido exclusivo usando **Telegram Stars (⭐️)**.  
- Suscripciones mensuales  
- Contenido PPV (Pago por Ver)  
- Propinas  
- Panel de administrador  
- Comisión del 20% para la plataforma  

## 🛠️ Requisitos

- Token de bot de Telegram (de BotFather)  
- Cuenta en [Railway.app](https://railway.app) (gratis, sin tarjeta)  

## ⚙️ Instalación en Railway.app

1. Ve a [Railway.app](https://railway.app) y crea una cuenta.  
2. Haz clic en “New Project” → “Deploy from GitHub repo”.  
3. Pega la URL de este repositorio.  
4. En “Variables”, agrega:  
   ```
   BOT_TOKEN = 8411359903:AAG0EkumLen1aRnbnGsgYABhHm4x0b-4dnQ
   ADMIN_USERNAME = @Daviddtm
   COMMISSION_PERCENTAGE = 20
   DEFAULT_CURRENCY = XTR
   EXCHANGE_RATE = 0.013
   MIN_WITHDRAWAL = 1000
   WITHDRAWAL_MODE = REAL
   ```  
5. En “Start Command”, pon: `python bot/main.py`  
6. ¡Listo! Tu bot estará vivo 24/7.  

## 📞 Comandos

- `/start` → Bienvenida  
- `/convertirme_en_creador` → Registro de creadores (en desarrollo)  
- `/suscribirme_a ` → Suscribirse a un creador  
- `/explorar_creadores` → Ver lista de creadores (en desarrollo)  

## 🆘 Soporte

Si necesitas ayuda, contacta a @Daviddtm.
