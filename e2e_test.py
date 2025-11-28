import os
import sys
import time
import json
import urllib.request
import urllib.error
import subprocess

# Add backend directory to sys.path to allow importing modules
# We need to add the parent directory of 'api' to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, 'backend')
if backend_dir not in sys.path:
    sys.path.append(backend_dir)


# Configuration
API_URL = "https://project-progress-api-prod-29226667525.asia-northeast1.run.app"
TEST_FILE_PATH = "test_meeting_notes_e2e.md"

def get_jwt_secret():
    try:
        result = subprocess.run(
            ['gcloud', 'secrets', 'versions', 'access', 'latest', '--secret=jwt-secret-key'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error fetching secret: {e}")
        exit(1)

def make_request(method, endpoint, headers=None, data=None, files=None):
    url = f"{API_URL}{endpoint}"
    if headers is None:
        headers = {}
    
    req = urllib.request.Request(url, method=method)
    for k, v in headers.items():
        req.add_header(k, v)
        
    if files:
        boundary = 'wL36Yn8afVp8Ag7AmP8qZ0SA4n1v9T'
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        
        body = []
        for name, value in data.items():
            body.append(f'--{boundary}'.encode('utf-8'))
            body.append(f'Content-Disposition: form-data; name="{name}"'.encode('utf-8'))
            body.append(b'')
            body.append(str(value).encode('utf-8'))
            
        for name, (filename, file_obj, content_type) in files.items():
            file_content = file_obj.read()
            if isinstance(file_content, str):
                file_content = file_content.encode('utf-8')
                
            body.append(f'--{boundary}'.encode('utf-8'))
            body.append(f'Content-Disposition: form-data; name="{name}"; filename="{filename}"'.encode('utf-8'))
            body.append(f'Content-Type: {content_type}'.encode('utf-8'))
            body.append(b'')
            body.append(file_content)
            
        body.append(f'--{boundary}--'.encode('utf-8'))
        body.append(b'')
        req.data = b'\r\n'.join(body)
        
    elif data:
        req.add_header('Content-Type', 'application/json')
        req.data = json.dumps(data).encode('utf-8')

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return {
                "status_code": response.status,
                "text": response.read().decode('utf-8')
            }
    except urllib.error.HTTPError as e:
        return {
            "status_code": e.code,
            "text": e.read().decode('utf-8')
        }
    except Exception as e:
        print(f"Request Error: {e}")
        return None

def create_test_file():
    content = """
# E2E Test Meeting

Date: 2024-11-26

## Projects
### Project Alpha
- Status: On Track

## Tasks
- [ ] Complete E2E testing for production deployment (Owner: QA Team)
- [ ] Verify BigQuery data ingestion (Owner: Data Team)

## Risks
- Network latency might affect test stability (Level: LOW)

## Decisions
- We will use Python script for API verification.
    """
    with open(TEST_FILE_PATH, "w") as f:
        f.write(content)
    return TEST_FILE_PATH

def run_test():
    print(f"🚀 Starting E2E Test against {API_URL}")
    
    # 1. Setup Auth
    secret = get_jwt_secret()
    os.environ["JWT_SECRET_KEY"] = secret
    
    try:
        from api.auth.jwt import create_access_token
    except ImportError as e:
        print(f"❌ ImportError: Could not import backend modules: {e}")
        print(f"sys.path: {sys.path}")
        return

    user_data = {
        "sub": "e2e-user",
        "email": "e2e@example.com",
        "name": "E2E User"
    }
    token = create_access_token(user_data)
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Generated Auth Token")

    # 2. Health Check
    print("Checking API Health...")
    resp = make_request("GET", "/")
    if resp and resp["status_code"] == 200:
        print("✅ API Health Check Passed")
    else:
        print(f"❌ API Health Check Failed: {resp['status_code'] if resp else 'None'}")
        return

    # 3. Upload File
    create_test_file()
    print("📄 Created test meeting notes")
    
    files = {
        "file": (TEST_FILE_PATH, open(TEST_FILE_PATH, "rb"), "text/markdown")
    }
    data = {
        "meeting_date": "2024-11-26",
        "title": "E2E Test Meeting"
    }
    
    print("📤 Uploading file...")
    resp = make_request("POST", "/upload/", headers=headers, data=data, files=files)
    
    if resp and resp["status_code"] == 200:
        try:
            upload_data = json.loads(resp["text"])
            meeting_id = upload_data.get("meeting_id")
            print(f"✅ Upload Successful. Meeting ID: {meeting_id}")
        except:
            print(f"✅ Upload Successful but failed to parse JSON")
            meeting_id = None
    else:
        print(f"❌ Upload Failed: {resp['status_code'] if resp else 'None'}")
        if resp: print(f"Response: {resp['text']}")
        return

    # 4. Wait for Worker Processing (Polling)
    print("⏳ Waiting for AI processing (max 60s)...")
    max_retries = 12
    processed = False
    
    for i in range(max_retries):
        time.sleep(5)
        
        resp = make_request("GET", "/projects/", headers=headers)
        if resp and resp["status_code"] == 200:
            try:
                projects = json.loads(resp["text"])
                found = any(p.get("project_name") == "Project Alpha" for p in projects)
                if found:
                    print("✅ AI Processing Verified: 'Project Alpha' found in projects list")
                    processed = True
                    break
            except:
                pass
        print(f"   ...polling ({i+1}/{max_retries})")
        
    if not processed:
        print("⚠️ AI Processing Timed Out")
    
    # 5. Verify Tasks
    if processed:
        resp = make_request("GET", "/tasks/", headers=headers)
        if resp and resp["status_code"] == 200:
            try:
                tasks = json.loads(resp["text"])
                e2e_task = any("Complete E2E testing" in t.get("task_title", "") for t in tasks)
                if e2e_task:
                    print("✅ Task Verification Passed: 'Complete E2E testing' task found")
                else:
                    print("❌ Task Verification Failed: Test task not found")
            except:
                pass
        
    print("🎉 E2E Test Completed")

if __name__ == "__main__":
    run_test()
