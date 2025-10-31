#!/usr/bin/env python3
"""
Quick test script to verify mobile app backend API endpoints
Run this after starting the Flask server to test if everything is working
"""

import requests
import json
from colorama import init, Fore, Style

init(autoreset=True)

BASE_URL = "http://localhost:5000"

def print_header(text):
    print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{text.center(60)}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")

def print_success(text):
    print(f"{Fore.GREEN}✓ {text}{Style.RESET_ALL}")

def print_error(text):
    print(f"{Fore.RED}✗ {text}{Style.RESET_ALL}")

def print_info(text):
    print(f"{Fore.YELLOW}ℹ {text}{Style.RESET_ALL}")

def test_login():
    """Test login endpoint"""
    print_header("Testing Login Endpoint")
    
    # You need to provide valid credentials from your database
    print_info("Testing with sample credentials (update with your actual credentials)")
    print_info("If this fails, update the credentials in this script")
    
    credentials = {
        "username": "instructor1",  # CHANGE THIS
        "password": "password123"   # CHANGE THIS
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/auth/login",
            json=credentials,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print_success(f"Login successful!")
                print_success(f"Token received: {data['token'][:50]}...")
                print_success(f"User: {data['user']['username']} (Role: {data['user']['role']})")
                return data['token']
            else:
                print_error(f"Login failed: {data.get('message')}")
        elif response.status_code == 401:
            print_error("Invalid credentials - please update credentials in this script")
        else:
            print_error(f"Login failed with status code: {response.status_code}")
            print_error(f"Response: {response.text}")
    except requests.exceptions.ConnectionError:
        print_error("Could not connect to server. Is Flask running on port 5000?")
        print_info("Start server with: python app_realtime.py")
        return None
    except Exception as e:
        print_error(f"Error: {str(e)}")
    
    return None

def test_verify_token(token):
    """Test token verification"""
    print_header("Testing Token Verification")
    
    try:
        response = requests.get(
            f"{BASE_URL}/auth/verify",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            print_success("Token verification successful!")
            return True
        else:
            print_error(f"Token verification failed: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_get_conversations(token):
    """Test get conversations endpoint"""
    print_header("Testing Get Conversations")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/messaging/conversations",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            conversations = data.get('conversations', [])
            print_success(f"Retrieved {len(conversations)} conversations")
            if conversations:
                for conv in conversations[:3]:  # Show first 3
                    print_info(f"  • {conv['participantName']} ({conv['participantRole']}) - {conv['unreadCount']} unread")
            else:
                print_info("No conversations yet (this is normal for a new setup)")
            return True
        else:
            print_error(f"Failed to get conversations: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_get_unread_count(token):
    """Test get unread count endpoint"""
    print_header("Testing Get Unread Count")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/messaging/unread-count",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            count = data.get('count', 0)
            print_success(f"Unread message count: {count}")
            return True
        else:
            print_error(f"Failed to get unread count: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def test_search_users(token):
    """Test user search endpoint"""
    print_header("Testing User Search")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/messaging/users/search?q=in",  # Search for "in" (instructor, admin, etc.)
            headers={"Authorization": f"Bearer {token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            users = data.get('users', [])
            print_success(f"Found {len(users)} users matching 'in'")
            if users:
                for user in users[:5]:  # Show first 5
                    print_info(f"  • {user['firstName']} {user['lastName']} ({user['role']}) - @{user['username']}")
            else:
                print_info("No users found (try different search query)")
            return True
        else:
            print_error(f"Failed to search users: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print_header("🧪 EduTrack360 Mobile API Test Suite")
    
    print_info("This script will test the mobile app API endpoints")
    print_info(f"Testing server at: {BASE_URL}")
    print_info("Make sure Flask server is running!\n")
    
    # Test login
    token = test_login()
    if not token:
        print_error("\n❌ Login failed. Cannot continue with other tests.")
        print_info("\n📝 To fix:")
        print_info("1. Make sure Flask server is running: python app_realtime.py")
        print_info("2. Update credentials in this script (test_mobile_api.py)")
        print_info("3. Check that database has users with instructor or admin accounts")
        return
    
    # Test other endpoints
    results = []
    results.append(("Login", True))
    results.append(("Token Verification", test_verify_token(token)))
    results.append(("Get Conversations", test_get_conversations(token)))
    results.append(("Get Unread Count", test_get_unread_count(token)))
    results.append(("Search Users", test_search_users(token)))
    
    # Summary
    print_header("📊 Test Results Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}: PASSED")
        else:
            print_error(f"{test_name}: FAILED")
    
    print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
    if passed == total:
        print(f"{Fore.GREEN}🎉 All tests passed! ({passed}/{total}){Style.RESET_ALL}")
        print(f"{Fore.GREEN}✅ Mobile app backend is ready to use!{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}⚠️  Some tests failed ({passed}/{total}){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Check the errors above and fix the issues{Style.RESET_ALL}")
    print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test interrupted by user{Style.RESET_ALL}")
