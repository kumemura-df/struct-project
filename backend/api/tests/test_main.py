from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Project Progress DB API is running", "version": "1.0.0"}

def test_upload_missing_auth():
    # Test upload without token should fail
    response = client.post("/upload/")
    assert response.status_code == 401
