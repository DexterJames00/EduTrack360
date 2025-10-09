# 🚀 Auto Telegram Bot Setup Guide

## What This Does

✅ **You only run ONE command: `python app.py`**  
✅ **It automatically starts ngrok**  
✅ **Gets the public HTTPS URL**  
✅ **Sets up Telegram webhooks automatically**  

## Quick Start

### 1. Make sure you have a bot token
```bash
# If you don't have a bot yet:
# 1. Open Telegram → Search @BotFather
# 2. Send /newbot
# 3. Follow instructions to create your bot
# 4. Copy the token BotFather gives you
```

### 2. Add your bot to the database
```bash
# Start your app once to access the admin panel
python app.py

# Then go to: http://localhost:5000/school_admin/telegram_config
# Add your bot token and username in the "Bot Configuration" section
```

### 3. That's it! 
```bash
# Every time you start your app now:
python app.py

# Auto-magic happens:
# ✅ Flask starts
# ✅ Ngrok tunnel starts automatically  
# ✅ Gets public HTTPS URL
# ✅ Sets webhook for ALL your configured bots
# ✅ Bots are ready to receive messages!
```

## What You'll See

When you run `python app.py`, you'll see:

```
🚀 Starting Flask app with auto Telegram bot setup...
✅ Auto-setup initialized! Starting Flask server...
 * Running on all addresses (0.0.0.0)
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.x.x:5000

==================================================
🤖 AUTO TELEGRAM BOT SETUP STARTING...
==================================================
⏳ Waiting 3 seconds for Flask to start...
🚀 Starting ngrok tunnel...
✅ Ngrok tunnel active: https://abc123def456.ngrok-free.app
✅ Webhook set for @YourBot
==================================================
🎉 AUTO-SETUP COMPLETE!
==================================================
✅ Your Flask app is running
✅ Ngrok tunnel is active: https://abc123def456.ngrok-free.app
✅ Telegram webhooks are configured
📱 Test your bots now!
==================================================
```

## How to Test

1. **Open Telegram**
2. **Search for your bot**: `@YourBotUsername`
3. **Send test message**: `Hello bot!`
4. **Register a student**: `SCHOOLNAME STUDENTCODE`

## Features

- ✅ **Zero configuration** - Just run and go!
- ✅ **Auto-restarts** - Works every time you start your app
- ✅ **Multiple bots** - Sets up webhooks for all configured bots
- ✅ **Clean shutdown** - Automatically cleans up ngrok when you stop
- ✅ **Status dashboard** - See auto-setup status in admin panel
- ✅ **Error handling** - Graceful fallbacks if something goes wrong

## Troubleshooting

### "Auto-setup not available"
```bash
# Install missing packages:
pip install pyngrok requests
```

### "No bot configurations found"
1. Go to admin panel: `http://localhost:5000/school_admin/telegram_config`
2. Add your bot token and username
3. Restart the app

### Ngrok tunnel fails
- Check your internet connection
- Make sure port 5000 is not in use by another app
- Try restarting the app

## Manual Override

If you need to disable auto-setup, just comment out the auto-setup lines in `app.py`:

```python
# Comment these lines to disable auto-setup:
# auto_setup_instance = initialize_auto_setup(app, flask_port=5000)
# start_auto_setup(delay=3)
```

## That's It! 

No more manual ngrok management, no more webhook setup headaches. Just run your Flask app and everything happens automatically! 🎉