"""
Simple Webhook Setup - Use when you have ngrok running manually
"""

import requests
from models import TelegramConfig
from database import db

def setup_webhooks_with_url(app, ngrok_url):
    """Set up webhooks for all bots using a provided ngrok URL"""
    
    if not ngrok_url:
        print("❌ No ngrok URL provided")
        return False
    
    # Ensure HTTPS
    if ngrok_url.startswith('http://'):
        ngrok_url = ngrok_url.replace('http://', 'https://')
    
    webhook_url = f"{ngrok_url}/school_admin/webhook"
    
    print(f"🔗 Setting up webhooks with URL: {webhook_url}")
    
    try:
        with app.app_context():
            # Get all bot configurations
            configs = TelegramConfig.query.all()
            
            if not configs:
                print("⚠️  No bot configurations found.")
                print("💡 Add bot configurations in the admin panel first.")
                return False
            
            success_count = 0
            
            for config in configs:
                if setup_single_webhook(config.bot_token, webhook_url):
                    print(f"✅ Webhook set for @{config.bot_username}")
                    success_count += 1
                else:
                    print(f"❌ Failed to set webhook for @{config.bot_username}")
            
            if success_count > 0:
                print(f"\n🎉 Webhook setup completed! {success_count} bot(s) ready.")
                return True
            else:
                print("❌ No webhooks were set successfully.")
                return False
                
    except Exception as e:
        print(f"❌ Error setting up webhooks: {e}")
        return False

def setup_single_webhook(bot_token, webhook_url):
    """Set webhook for a single bot"""
    try:
        # Test bot token first
        test_response = requests.get(
            f'https://api.telegram.org/bot{bot_token}/getMe', 
            timeout=10
        )
        
        if test_response.status_code != 200:
            print(f"❌ Invalid bot token: {bot_token[:10]}...")
            return False
        
        # Set webhook
        webhook_response = requests.post(
            f'https://api.telegram.org/bot{bot_token}/setWebhook',
            json={'url': webhook_url},
            timeout=10
        )
        
        if webhook_response.status_code == 200:
            webhook_data = webhook_response.json()
            return webhook_data.get('ok', False)
        else:
            print(f"❌ Webhook setup failed: {webhook_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")
        return False

def quick_setup(app, ngrok_url="https://adc380f07bf3.ngrok-free.app"):
    """Quick setup using user's known ngrok URL"""
    
    print("\n" + "="*50)
    print("🚀 QUICK TELEGRAM WEBHOOK SETUP")
    print("="*50)
    print(f"🔗 Using ngrok URL: {ngrok_url}")
    
    success = setup_webhooks_with_url(app, ngrok_url)
    
    if success:
        print("\n" + "="*50)
        print("🎉 QUICK SETUP COMPLETE!")
        print("="*50)
        print(f"✅ Webhook URL: {ngrok_url}/school_admin/webhook")
        print(f"📱 Your bots are ready!")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("❌ QUICK SETUP FAILED")
        print("="*50)
        print("💡 Make sure you have:")
        print("   1. Valid bot configurations in the database")
        print("   2. Correct ngrok URL")
        print("   3. Internet connection")
        print("="*50)
    
    return success