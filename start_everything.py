#!/usr/bin/env python3
"""
Simple script to start everything for the Telegram bot
- Start Flask app
- Start ngrok
- Set webhook
- Test bot
"""

import os
import sys
import time
import subprocess
import requests
import json
import signal
import threading
from pathlib import Path

class BotStarter:
    def __init__(self):
        self.flask_process = None
        self.ngrok_process = None
        self.ngrok_url = None
        
    def cleanup(self, signum=None, frame=None):
        """Clean up processes"""
        print("\n🧹 Cleaning up...")
        
        if self.flask_process:
            self.flask_process.terminate()
            print("✅ Flask stopped")
            
        if self.ngrok_process:
            self.ngrok_process.terminate()
            print("✅ Ngrok stopped")
            
        # Kill any leftover ngrok processes
        try:
            subprocess.run(['pkill', '-f', 'ngrok'], check=False)
        except:
            pass
            
        sys.exit(0)
    
    def start_flask(self):
        """Start Flask app"""
        print("🚀 Starting Flask app...")
        
        # Set environment variables
        env = os.environ.copy()
        env['FLASK_APP'] = 'app.py'
        env['FLASK_DEBUG'] = '1'
        
        # Start Flask in background using virtual environment Python
        venv_python = os.path.join(os.getcwd(), 'env', 'bin', 'python')
        python_cmd = venv_python if os.path.exists(venv_python) else sys.executable
        
        self.flask_process = subprocess.Popen(
            [python_cmd, 'app_clean.py'],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for Flask to start
        print("⏳ Waiting for Flask to start...")
        time.sleep(5)
        
        # Test if Flask is running
        try:
            response = requests.get('http://localhost:5000/', timeout=5)
            print("✅ Flask is running!")
            return True
        except:
            print("❌ Flask failed to start")
            return False
    
    def start_ngrok(self):
        """Start ngrok tunnel"""
        print("🔗 Starting ngrok tunnel...")
        
        # Kill any existing ngrok processes
        try:
            subprocess.run(['pkill', '-f', 'ngrok'], check=False)
            time.sleep(2)
        except:
            pass
        
        # Start ngrok
        self.ngrok_process = subprocess.Popen(
            ['ngrok', 'http', '5000', '--log=stdout'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait for ngrok to start
        print("⏳ Waiting for ngrok to start...")
        time.sleep(5)
        
        # Get ngrok URL
        try:
            response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
            data = response.json()
            
            for tunnel in data.get('tunnels', []):
                if tunnel.get('proto') == 'https':
                    self.ngrok_url = tunnel['public_url']
                    print(f"✅ Ngrok tunnel: {self.ngrok_url}")
                    return True
                    
            print("❌ No HTTPS tunnel found")
            return False
            
        except Exception as e:
            print(f"❌ Failed to get ngrok URL: {e}")
            return False
    
    def get_bot_config(self):
        """Get bot configuration from database"""
        try:
            # Import Flask app context
            sys.path.append('.')
            from app import app
            from models import TelegramConfig
            
            with app.app_context():
                config = TelegramConfig.query.first()
                if config:
                    print(f"✅ Found bot: @{config.bot_username}")
                    return config.bot_token, config.bot_username
                else:
                    print("❌ No bot configuration found in database")
                    return None, None
                    
        except Exception as e:
            print(f"❌ Error getting bot config: {e}")
            return None, None
    
    def test_bot(self, bot_token):
        """Test if bot token is valid"""
        try:
            print("🤖 Testing bot token...")
            
            response = requests.get(
                f'https://api.telegram.org/bot{bot_token}/getMe',
                timeout=10
            )
            
            if response.status_code == 200:
                bot_info = response.json()
                if bot_info.get('ok'):
                    bot_data = bot_info['result']
                    print(f"✅ Bot is valid: @{bot_data['username']}")
                    return True
                    
            print(f"❌ Bot test failed: {response.text}")
            return False
            
        except Exception as e:
            print(f"❌ Bot test error: {e}")
            return False
    
    def set_webhook(self, bot_token):
        """Set webhook for the bot"""
        try:
            print("🔗 Setting webhook...")
            
            webhook_url = f"{self.ngrok_url}/school_admin/webhook"
            
            response = requests.post(
                f'https://api.telegram.org/bot{bot_token}/setWebhook',
                json={'url': webhook_url},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print(f"✅ Webhook set: {webhook_url}")
                    return True
                    
            print(f"❌ Webhook failed: {response.text}")
            return False
            
        except Exception as e:
            print(f"❌ Webhook error: {e}")
            return False
    
    def verify_webhook(self, bot_token):
        """Verify webhook is working"""
        try:
            print("🔍 Verifying webhook...")
            
            response = requests.get(
                f'https://api.telegram.org/bot{bot_token}/getWebhookInfo',
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    webhook_info = result['result']
                    if webhook_info.get('url'):
                        print(f"✅ Webhook verified: {webhook_info['url']}")
                        return True
                        
            print("❌ Webhook verification failed")
            return False
            
        except Exception as e:
            print(f"❌ Webhook verification error: {e}")
            return False
    
    def run(self):
        """Run the complete setup"""
        print("="*60)
        print("🎯 STARTING TELEGRAM BOT SETUP")
        print("="*60)
        
        # Set up signal handler for cleanup
        signal.signal(signal.SIGINT, self.cleanup)
        signal.signal(signal.SIGTERM, self.cleanup)
        
        try:
            # Step 1: Start Flask
            if not self.start_flask():
                print("❌ Setup failed: Flask couldn't start")
                return False
            
            # Step 2: Start ngrok
            if not self.start_ngrok():
                print("❌ Setup failed: Ngrok couldn't start")
                return False
            
            # Step 3: Get bot config
            bot_token, bot_username = self.get_bot_config()
            if not bot_token:
                print("❌ Setup failed: No bot configuration")
                return False
            
            # Step 4: Test bot
            if not self.test_bot(bot_token):
                print("❌ Setup failed: Bot token invalid")
                return False
            
            # Step 5: Set webhook
            if not self.set_webhook(bot_token):
                print("❌ Setup failed: Webhook couldn't be set")
                return False
            
            # Step 6: Verify webhook
            if not self.verify_webhook(bot_token):
                print("❌ Setup failed: Webhook verification failed")
                return False
            
            # Success!
            print("\n" + "="*60)
            print("🎉 SETUP COMPLETE!")
            print("="*60)
            print(f"✅ Flask app: http://localhost:5000")
            print(f"✅ Public URL: {self.ngrok_url}")
            print(f"✅ Bot: @{bot_username}")
            print(f"✅ Webhook: {self.ngrok_url}/school_admin/webhook")
            print("\n📱 Your bot is ready! Test it by sending:")
            print("   Aclc College of Butuan OLOW5IZK")
            print("\n🛑 Press Ctrl+C to stop everything")
            print("="*60)
            
            # Keep running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
                
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
        finally:
            self.cleanup()

if __name__ == "__main__":
    starter = BotStarter()
    starter.run()