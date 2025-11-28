import os
import sys
import json
import urllib.request
import urllib.error
import subprocess

# Add backend directory to sys.path to import api modules
sys.path.append(os.path.join(os.getcwd(), 'backend'))

# Configuration
API_URL = "https://project-progress-api-prod-29226667525.asia-northeast1.run.app"

def get_jwt_secret():
    print("🔑 Fetching JWT secret from Secret Manager...")
    try:
        result = subprocess.run(
            ['gcloud', 'secrets', 'versions', 'access', 'latest', '--secret=jwt-secret-key'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ Error fetching secret: {e}")
        exit(1)

def make_request(token):
    url = f"{API_URL}/auth/me"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    
    print(f"🚀 Sending request to {url}...")
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            print(f"✅ Success! Status: {response.status}")
            print(f"Response: {response.read().decode('utf-8')}")
            return True
    except urllib.error.HTTPError as e:
        print(f"❌ Failed. Status: {e.code}")
        print(f"Reason: {e.read().decode('utf-8')}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    # 1. Setup Environment
    secret = get_jwt_secret()
    os.environ["JWT_SECRET_KEY"] = secret
    
    # 2. Import backend JWT logic
    try:
        from api.auth.jwt import create_access_token
    except ImportError as e:
        print(f"❌ ImportError: {e}")
        print("Make sure you are running this from the project root.")
        return

    # 3. Generate Token
    print("🔨 Generating token using backend logic...")
    user_data = {
        "sub": "debug-user",
        "email": "debug@example.com",
        "name": "Debug User"
    }
    token = create_access_token(user_data)
    print(f"Token generated (len={len(token)})")

    # 4. Test API
    make_request(token)

if __name__ == "__main__":
    main()
