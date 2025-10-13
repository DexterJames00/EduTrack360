#!/usr/bin/env python3
"""
Simple startup script for single bot system
"""

import os
import sys
import time
import subprocess
import requests
import json

def main():
    print("="*60)
    print("🎯 STARTING SINGLE BOT SYSTEM")
    print("="*60)
    
    # Start Flask app
    print("🚀 Starting Flask app...")
    venv_python = os.path.join(os.getcwd(), 'env', 'bin', 'python')
    python_cmd = venv_python if os.path.exists(venv_python) else sys.executable
    
    flask_process = subprocess.Popen([
        python_cmd, '-c', '''
import sys
sys.path.append(".")
from app_clean import app
app.run(debug=False, host="0.0.0.0", port=5000, use_reloader=False)
'''], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Wait for Flask
    print("⏳ Waiting for Flask to start...")
    for i in range(10):
        try:
            response = requests.get('http://localhost:5000/', timeout=2)
            if response.status_code == 200:
                print("✅ Flask is running!")
                break
        except:
            time.sleep(1)
    else:
        print("❌ Flask failed to start")
        flask_process.terminate()
        return
    
    # Start ngrok
    print("🔗 Starting ngrok...")
    # Use system ngrok (not the pyngrok from virtual environment)
    ngrok_process = subprocess.Popen(['/usr/local/bin/ngrok', 'http', '5000'], 
                                   stdout=subprocess.DEVNULL, 
                                   stderr=subprocess.DEVNULL)
    
    # Wait for ngrok
    print("⏳ Waiting for ngrok tunnel...")
    ngrok_url = None
    for i in range(20):
        try:
            time.sleep(1)
            response = requests.get('http://localhost:4040/api/tunnels', timeout=2)
            if response.status_code == 200:
                data = response.json()
                for tunnel in data.get('tunnels', []):
                    if tunnel.get('proto') == 'https':
                        ngrok_url = tunnel['public_url']
                        print(f"✅ Ngrok tunnel: {ngrok_url}")
                        break
                if ngrok_url:
                    break
        except:
            pass
    
    if not ngrok_url:
        print("❌ Failed to get ngrok URL")
        flask_process.terminate()
        ngrok_process.terminate()
        return
    
    # Get bot config and set webhook
    print("🤖 Setting up bot webhook...")
    try:
        result = subprocess.run([
            python_cmd, '-c', f'''
import sys
sys.path.append(".")
from app_clean import app
from models import TelegramConfig
import requests

with app.app_context():
    config = TelegramConfig.query.filter_by(is_active=True).first()
    if config:
        webhook_url = "{ngrok_url}/school_admin/webhook"
        response = requests.post(
            f"https://api.telegram.org/bot{{config.bot_token}}/setWebhook",
            json={{"url": webhook_url}},
            timeout=10
        )
        if response.status_code == 200 and response.json().get("ok"):
            print(f"✅ Webhook set for @{{config.bot_username}}: {{webhook_url}}")
        else:
            print(f"❌ Failed to set webhook: {{response.text}}")
    else:
        print("❌ No active bot found")
'''
        ], capture_output=True, text=True, timeout=15)
        
        if result.stdout:
            print(result.stdout.strip())
    
    except Exception as e:
        print(f"❌ Error setting webhook: {e}")
    
    # Success message
    print("\n" + "="*60)
    print("🎉 SINGLE BOT SYSTEM READY!")
    print("="*60)
    print(f"✅ Flask app: http://localhost:5000")
    print(f"✅ Public URL: {ngrok_url}")
    print(f"✅ Webhook: {ngrok_url}/school_admin/webhook")
    print("\n📱 Bot is ready! Test with:")
    print("   ACLCCOLLEG ABC123")
    print("   MAGAUDNATI XYZ789")
    print("\n🛑 Press Ctrl+C to stop")
    print("="*60)
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🧹 Stopping...")
        flask_process.terminate()
        ngrok_process.terminate()
        subprocess.run(['pkill', '-f', 'ngrok'], check=False)
        print("✅ Stopped")

if __name__ == "__main__":
    main()