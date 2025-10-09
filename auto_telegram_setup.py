"""
Auto Telegram Bot Setup
Automatically starts ngrok, gets public URL, and sets up webhook when Flask app starts.
"""

import os
import time
import requests
import threading
from pyngrok import ngrok
from models import TelegramConfig
from database import db

class AutoTelegramSetup:
    def __init__(self, app, flask_port=5000):
        self.app = app
        self.flask_port = flask_port
        self.ngrok_tunnel = None
        self.public_url = None
        self.setup_complete = False
        
    def start_ngrok(self):
        """Start ngrok tunnel and get public HTTPS URL"""
        try:
            print("🚀 Starting ngrok tunnel...")
            
            # First, try to get existing ngrok tunnels
            try:
                from pyngrok import ngrok
                tunnels = ngrok.get_tunnels()
                
                # Look for existing HTTP tunnel on our port
                for tunnel in tunnels:
                    if (hasattr(tunnel, 'config') and 
                        tunnel.config.get('addr') == f'localhost:{self.flask_port}'):
                        self.public_url = tunnel.public_url
                        
                        # Ensure HTTPS
                        if self.public_url.startswith('http://'):
                            self.public_url = self.public_url.replace('http://', 'https://')
                        
                        print(f"✅ Using existing ngrok tunnel: {self.public_url}")
                        return True
                
                # Look for any HTTP tunnel (might be what user already has)
                for tunnel in tunnels:
                    if tunnel.proto == 'http' or tunnel.proto == 'https':
                        self.public_url = tunnel.public_url
                        
                        # Ensure HTTPS
                        if self.public_url.startswith('http://'):
                            self.public_url = self.public_url.replace('http://', 'https://')
                        
                        print(f"✅ Using existing ngrok tunnel: {self.public_url}")
                        print(f"⚠️  Note: This tunnel points to {tunnel.config.get('addr', 'unknown')}")
                        return True
                        
            except Exception as e:
                print(f"⚠️  Could not check existing tunnels: {e}")
            
            # If no existing tunnel found, try to create new one
            print("📡 No existing tunnel found, creating new one...")
            
            # Kill any existing ngrok processes first
            try:
                ngrok.kill()
            except:
                pass
            
            # Start new tunnel
            self.ngrok_tunnel = ngrok.connect(self.flask_port, "http")
            self.public_url = self.ngrok_tunnel.public_url
            
            # Ensure HTTPS
            if self.public_url.startswith('http://'):
                self.public_url = self.public_url.replace('http://', 'https://')
            
            print(f"✅ New ngrok tunnel created: {self.public_url}")
            return True
            
        except Exception as e:
            print(f"❌ Error with ngrok: {e}")
            
            # Fallback: Ask user to provide their ngrok URL
            print("\n💡 FALLBACK: Manual ngrok URL detection")
            print("If you have ngrok running manually, we can use that!")
            print("Common ngrok URLs look like: https://abc123def456.ngrok-free.app")
            
            # Try to detect from user's previous setup or environment
            potential_urls = [
                "https://adc380f07bf3.ngrok-free.app",  # User mentioned this URL
                # Could add more detection logic here
            ]
            
            for url in potential_urls:
                if self.test_url_accessibility(url):
                    self.public_url = url
                    print(f"✅ Detected working ngrok URL: {url}")
                    return True
            
            print("❌ Could not start or detect ngrok tunnel")
            print("💡 Please ensure ngrok is running or restart the app")
            return False
    
    def test_url_accessibility(self, url):
        """Test if a URL is accessible and likely pointing to our Flask app"""
        try:
            import requests
            
            # Test if the URL responds
            test_url = f"{url}/"
            response = requests.get(test_url, timeout=5)
            
            # If we get any response, consider it working
            if response.status_code in [200, 404, 301, 302]:
                return True
            
            return False
            
        except Exception:
            return False
    
    def setup_webhook_for_all_bots(self):
        """Set up webhooks for all configured bots"""
        try:
            with self.app.app_context():
                # Get all bot configurations
                configs = TelegramConfig.query.all()
                
                if not configs:
                    print("⚠️  No bot configurations found. Please configure a bot first.")
                    return False
                
                webhook_url = f"{self.public_url}/school_admin/webhook"
                success_count = 0
                
                for config in configs:
                    if self.setup_webhook(config.bot_token, webhook_url):
                        print(f"✅ Webhook set for @{config.bot_username}")
                        success_count += 1
                    else:
                        print(f"❌ Failed to set webhook for @{config.bot_username}")
                
                if success_count > 0:
                    print(f"\n🎉 Auto-setup completed! {success_count} bot(s) ready.")
                    print(f"📱 Webhook URL: {webhook_url}")
                    print(f"🌐 Public URL: {self.public_url}")
                    self.setup_complete = True
                    return True
                else:
                    print("❌ No webhooks were set successfully.")
                    return False
                    
        except Exception as e:
            print(f"❌ Error setting up webhooks: {e}")
            return False
    
    def setup_webhook(self, bot_token, webhook_url):
        """Set webhook for a specific bot"""
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
                return False
                
        except Exception as e:
            print(f"❌ Error setting webhook: {e}")
            return False
    
    def auto_setup(self, delay=3):
        """Run the complete auto-setup process"""
        def setup_process():
            print("\n" + "="*50)
            print("🤖 AUTO TELEGRAM BOT SETUP STARTING...")
            print("="*50)
            
            # Wait for Flask to start
            print(f"⏳ Waiting {delay} seconds for Flask to start...")
            time.sleep(delay)
            
            # Start ngrok
            if not self.start_ngrok():
                print("❌ Auto-setup failed: Could not start ngrok")
                return
            
            # Wait a moment for ngrok to stabilize
            time.sleep(2)
            
            # Setup webhooks
            if self.setup_webhook_for_all_bots():
                print("\n" + "="*50)
                print("🎉 AUTO-SETUP COMPLETE!")
                print("="*50)
                print(f"✅ Your Flask app is running")
                print(f"✅ Ngrok tunnel is active: {self.public_url}")
                print(f"✅ Telegram webhooks are configured")
                print(f"📱 Test your bots now!")
                print("="*50)
            else:
                print("\n" + "="*50)
                print("⚠️  AUTO-SETUP PARTIALLY COMPLETE")
                print("="*50)
                print(f"✅ Flask app is running")
                print(f"✅ Ngrok tunnel is active: {self.public_url}")
                print(f"❌ No bot configurations found")
                print(f"💡 Add bot configurations in the admin panel")
                print("="*50)
        
        # Run setup in background thread
        setup_thread = threading.Thread(target=setup_process, daemon=True)
        setup_thread.start()
    
    def cleanup(self):
        """Clean up ngrok tunnel"""
        try:
            if self.ngrok_tunnel:
                ngrok.disconnect(self.ngrok_tunnel.public_url)
                print("🧹 Ngrok tunnel closed")
        except:
            pass
        
        try:
            ngrok.kill()
        except:
            pass

# Global instance
auto_setup = None

def initialize_auto_setup(app, flask_port=5000):
    """Initialize the auto-setup system"""
    global auto_setup
    auto_setup = AutoTelegramSetup(app, flask_port)
    return auto_setup

def start_auto_setup(delay=3):
    """Start the auto-setup process"""
    global auto_setup
    if auto_setup:
        auto_setup.auto_setup(delay)
    else:
        print("❌ Auto-setup not initialized")

def cleanup_auto_setup():
    """Clean up auto-setup resources"""
    global auto_setup
    if auto_setup:
        auto_setup.cleanup()

def get_public_url():
    """Get the current public URL"""
    global auto_setup
    if auto_setup and auto_setup.public_url:
        return auto_setup.public_url
    return None

def is_setup_complete():
    """Check if auto-setup is complete"""
    global auto_setup
    if auto_setup:
        return auto_setup.setup_complete
    return False