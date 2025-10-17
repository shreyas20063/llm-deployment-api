#!/usr/bin/env python3
"""
Test script for LLM Deployment API
Usage: python test_api.py [API_URL]
Example: python test_api.py http://localhost:5000
"""

import sys
import requests
import json
import time
import os
from dotenv import load_dotenv

load_dotenv()

def test_api(base_url):
    """Test the API endpoint with a sample request"""
    
    endpoint = f"{base_url}/api/deploy"
    
    # Sample test request
    test_request = {
        "email": "test@example.com",
        "secret": os.environ.get('YOUR_SECRET', 'test_secret'),
        "task": f"test-task-{int(time.time())}",
        "round": 1,
        "nonce": f"test-nonce-{int(time.time())}",
        "brief": "Create a simple Bootstrap page with a heading 'Test Page' and a blue button that says 'Click Me'",
        "checks": [
            "Page has Bootstrap 5 loaded from CDN",
            "Page has h1 heading with text 'Test Page'",
            "Page has a blue button with text 'Click Me'"
        ],
        "evaluation_url": "https://httpbin.org/post",
        "attachments": []
    }
    
    print("=" * 60)
    print("Testing LLM Deployment API")
    print("=" * 60)
    print(f"\nEndpoint: {endpoint}")
    print(f"Request Task: {test_request['task']}")
    print("\nSending request...")
    
    try:
        response = requests.post(
            endpoint,
            json=test_request,
            headers={"Content-Type": "application/json"},
            timeout=120  # 2 minute timeout
        )
        
        print(f"\n✅ Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n🎉 SUCCESS! Response:")
            print(json.dumps(result, indent=2))
            
            print("\n" + "=" * 60)
            print("📊 RESULTS:")
            print("=" * 60)
            if 'repo_url' in result:
                print(f"✓ GitHub Repo: {result['repo_url']}")
            if 'pages_url' in result:
                print(f"✓ GitHub Pages: {result['pages_url']}")
                print("\n⏳ Wait 2-3 minutes for GitHub Pages to deploy")
                print(f"   Then visit: {result['pages_url']}")
            
            return True
        else:
            print(f"\n❌ FAILED with status {response.status_code}")
            print("Response:")
            print(response.text)
            return False
            
    except requests.exceptions.Timeout:
        print("\n⏰ ERROR: Request timed out after 2 minutes")
        print("This might happen if LLM generation is slow.")
        print("Check your server logs for details.")
        return False
        
    except requests.exceptions.ConnectionError:
        print(f"\n🔌 ERROR: Cannot connect to {base_url}")
        print("Make sure your server is running.")
        return False
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False

def test_health(base_url):
    """Test the health check endpoint"""
    try:
        response = requests.get(f"{base_url}/health", timeout=10)
        if response.status_code == 200:
            print(f"✅ Health check passed: {response.json()}")
            return True
        else:
            print(f"⚠️  Health check returned {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        api_url = sys.argv[1].rstrip('/')
    else:
        api_url = "http://localhost:5000"
    
    print("Testing health endpoint...")
    test_health(api_url)
    
    print("\n" + "=" * 60)
    input("Press Enter to test the deployment endpoint...")
    
    success = test_api(api_url)
    
    if success:
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\n🚀 Your API is ready for production!")
        print("\nNext steps:")
        print("1. Deploy to Render/Railway")
        print("2. Submit your API URL to the Google Form")
        print("3. Wait for instructor requests")
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ TESTS FAILED")
        print("=" * 60)
        print("\nDebug checklist:")
        print("1. Are all environment variables set?")
        print("2. Is your GITHUB_TOKEN valid?")
        print("3. Is your AIPIPE_TOKEN valid?")
        print("4. Does YOUR_SECRET match the test request?")
        print("5. Check server logs for detailed errors")
        sys.exit(1)
