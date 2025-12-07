"""Unit tests for Project Progress DB API."""
import os
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Set environment variables before importing app
os.environ["USE_LOCAL_DB"] = "false"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing"

from main import app
from auth.jwt import create_access_token, verify_token, SECRET_KEY, ALGORITHM

client = TestClient(app)


# ==============================================================================
# Test Data Fixtures
# ==============================================================================

@pytest.fixture
def mock_projects():
    """Sample project data for testing."""
    return [
        {
            "project_id": "proj-001",
            "tenant_id": "default",
            "project_name": "Project Alpha",
            "latest_meeting_id": "meet-001",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-15T00:00:00"
        },
        {
            "project_id": "proj-002",
            "tenant_id": "default",
            "project_name": "Project Beta",
            "latest_meeting_id": "meet-002",
            "created_at": "2024-01-05T00:00:00",
            "updated_at": "2024-01-20T00:00:00"
        }
    ]


@pytest.fixture
def mock_tasks():
    """Sample task data for testing."""
    return [
        {
            "task_id": "task-001",
            "meeting_id": "meet-001",
            "project_id": "proj-001",
            "task_title": "Complete unit testing",
            "task_description": "Write comprehensive tests",
            "owner": "Developer",
            "owner_email": "dev@example.com",
            "due_date": "2024-02-01",
            "status": "IN_PROGRESS",
            "priority": "HIGH",
            "created_at": "2024-01-15T00:00:00",
            "updated_at": "2024-01-15T00:00:00",
            "source_sentence": "Need to complete unit testing by February"
        },
        {
            "task_id": "task-002",
            "meeting_id": "meet-001",
            "project_id": "proj-001",
            "task_title": "Deploy to staging",
            "task_description": "Setup staging environment",
            "owner": "DevOps",
            "owner_email": None,
            "due_date": "2024-02-15",
            "status": "NOT_STARTED",
            "priority": "MEDIUM",
            "created_at": "2024-01-15T00:00:00",
            "updated_at": "2024-01-15T00:00:00",
            "source_sentence": "We should deploy to staging"
        }
    ]


@pytest.fixture
def mock_risks():
    """Sample risk data for testing."""
    return [
        {
            "risk_id": "risk-001",
            "meeting_id": "meet-001",
            "project_id": "proj-001",
            "risk_description": "Schedule might slip",
            "risk_level": "HIGH",
            "likelihood": None,
            "impact": None,
            "owner": "PM",
            "created_at": "2024-01-15T00:00:00",
            "source_sentence": "I'm worried we might not make the deadline"
        },
        {
            "risk_id": "risk-002",
            "meeting_id": "meet-001",
            "project_id": "proj-001",
            "risk_description": "Resource constraints",
            "risk_level": "MEDIUM",
            "likelihood": None,
            "impact": None,
            "owner": "Manager",
            "created_at": "2024-01-15T00:00:00",
            "source_sentence": "We might need more developers"
        }
    ]


@pytest.fixture
def mock_decisions():
    """Sample decision data for testing."""
    return [
        {
            "decision_id": "dec-001",
            "meeting_id": "meet-001",
            "project_id": "proj-001",
            "decision_content": "Use Python for E2E testing",
            "created_at": "2024-01-15T00:00:00",
            "source_sentence": "We decided to use Python for E2E testing"
        }
    ]


@pytest.fixture
def mock_risk_stats():
    """Sample risk statistics for testing."""
    return {
        "total": 5,
        "by_level": {"HIGH": 2, "MEDIUM": 2, "LOW": 1},
        "by_project": [
            {"project_id": "proj-001", "project_name": "Project Alpha", "count": 3},
            {"project_id": "proj-002", "project_name": "Project Beta", "count": 2}
        ]
    }


@pytest.fixture
def valid_user_data():
    """Valid user data for JWT tokens."""
    return {
        "sub": "user-123",
        "email": "test@example.com",
        "name": "Test User"
    }


@pytest.fixture
def auth_headers(valid_user_data):
    """Generate auth headers with valid JWT token."""
    token = create_access_token(valid_user_data)
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# Health Check Tests
# ==============================================================================

class TestHealthCheck:
    """Tests for health check endpoint."""
    
    def test_health_check(self):
        """Test health check returns 200 and correct message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Project Progress DB API is running"
        assert data["version"] == "1.0.0"
        assert "environment" in data


# ==============================================================================
# JWT Authentication Tests
# ==============================================================================

class TestJWTAuthentication:
    """Tests for JWT token management."""
    
    def test_create_access_token_success(self, valid_user_data):
        """Test JWT token creation with valid data."""
        token = create_access_token(valid_user_data)
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_verify_token_success(self, valid_user_data):
        """Test JWT token verification with valid token."""
        token = create_access_token(valid_user_data)
        payload = verify_token(token)
        
        assert payload is not None
        assert payload["sub"] == valid_user_data["sub"]
        assert payload["email"] == valid_user_data["email"]
        assert payload["name"] == valid_user_data["name"]
        assert "exp" in payload
        assert "iat" in payload
    
    def test_verify_token_expired(self, valid_user_data):
        """Test JWT token verification fails for expired token."""
        # Create token that expires in the past
        token = create_access_token(
            valid_user_data, 
            expires_delta=timedelta(seconds=-10)
        )
        payload = verify_token(token)
        
        assert payload is None
    
    def test_verify_token_invalid(self):
        """Test JWT token verification fails for invalid token."""
        payload = verify_token("invalid-token-string")
        assert payload is None
    
    def test_verify_token_tampered(self, valid_user_data):
        """Test JWT token verification fails for tampered token."""
        token = create_access_token(valid_user_data)
        # Tamper with the token
        tampered_token = token[:-5] + "xxxxx"
        payload = verify_token(tampered_token)
        
        assert payload is None
    
    def test_token_with_custom_expiry(self, valid_user_data):
        """Test JWT token creation with custom expiry."""
        custom_delta = timedelta(hours=2)
        token = create_access_token(valid_user_data, expires_delta=custom_delta)
        payload = verify_token(token)
        
        assert payload is not None
        # Check expiry is approximately 2 hours from now
        exp_time = datetime.utcfromtimestamp(payload["exp"])
        now = datetime.utcnow()
        assert (exp_time - now).total_seconds() > 7000  # ~2 hours minus some margin


# ==============================================================================
# Upload Endpoint Tests
# ==============================================================================

class TestUploadEndpoint:
    """Tests for file upload endpoint."""
    
    def test_upload_missing_auth(self):
        """Test upload without token should fail with 401."""
        response = client.post("/upload/")
        assert response.status_code == 401
        assert "Not authenticated" in response.json()["detail"]
    
    def test_upload_invalid_token(self):
        """Test upload with invalid token should fail."""
        headers = {"Authorization": "Bearer invalid-token"}
        response = client.post("/upload/", headers=headers)
        assert response.status_code == 401


# ==============================================================================
# Projects Endpoint Tests
# ==============================================================================

class TestProjectsEndpoint:
    """Tests for projects endpoint."""
    
    def test_projects_missing_auth(self):
        """Test projects endpoint without auth should fail."""
        response = client.get("/projects/")
        assert response.status_code == 401
    
    @patch("routers.projects.bigquery.list_projects")
    def test_get_projects_success(self, mock_list_projects, auth_headers, mock_projects):
        """Test successful projects retrieval."""
        mock_list_projects.return_value = mock_projects
        
        response = client.get("/projects/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        # Paginated response format
        assert "items" in data
        assert len(data["items"]) == 2
        assert data["items"][0]["project_name"] == "Project Alpha"
        assert data["items"][1]["project_name"] == "Project Beta"
    
    @patch("routers.projects.bigquery.list_projects")
    def test_get_projects_empty(self, mock_list_projects, auth_headers):
        """Test projects endpoint with no data."""
        mock_list_projects.return_value = []
        
        response = client.get("/projects/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        # Paginated response format
        assert "items" in data
        assert data["items"] == []
    
    @patch("routers.projects.bigquery.list_projects")
    def test_get_projects_server_error(self, mock_list_projects, auth_headers):
        """Test projects endpoint handles server errors."""
        mock_list_projects.side_effect = Exception("Database error")
        
        response = client.get("/projects/", headers=auth_headers)
        
        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]


# ==============================================================================
# Tasks Endpoint Tests
# ==============================================================================

class TestTasksEndpoint:
    """Tests for tasks endpoint."""
    
    def test_tasks_missing_auth(self):
        """Test tasks endpoint without auth should fail."""
        response = client.get("/tasks/")
        assert response.status_code == 401
    
    @patch("routers.tasks.bigquery.list_tasks_paginated")
    def test_get_tasks_success(self, mock_list_tasks, auth_headers, mock_tasks):
        """Test successful tasks retrieval."""
        mock_list_tasks.return_value = {
            "items": mock_tasks,
            "total": len(mock_tasks),
            "limit": 20,
            "offset": 0,
            "has_more": False
        }
        
        response = client.get("/tasks/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        # Paginated response format
        assert "items" in data
        assert len(data["items"]) == 2
        assert data["items"][0]["task_title"] == "Complete unit testing"
    
    @patch("routers.tasks.bigquery.list_tasks_paginated")
    def test_get_tasks_with_project_filter(self, mock_list_tasks, auth_headers, mock_tasks):
        """Test tasks retrieval with project_id filter."""
        mock_list_tasks.return_value = {
            "items": [mock_tasks[0]],
            "total": 1,
            "limit": 20,
            "offset": 0,
            "has_more": False
        }
        
        response = client.get("/tasks/?project_id=proj-001", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    @patch("routers.tasks.bigquery.list_tasks_paginated")
    def test_get_tasks_empty(self, mock_list_tasks, auth_headers):
        """Test tasks endpoint with no data."""
        mock_list_tasks.return_value = {
            "items": [],
            "total": 0,
            "limit": 20,
            "offset": 0,
            "has_more": False
        }
        
        response = client.get("/tasks/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        # Paginated response format
        assert "items" in data
        assert data["items"] == []


# ==============================================================================
# Risks Endpoint Tests
# ==============================================================================

class TestRisksEndpoint:
    """Tests for risks endpoint."""
    
    def test_risks_missing_auth(self):
        """Test risks endpoint without auth should fail."""
        response = client.get("/risks/")
        assert response.status_code == 401
    
    @patch("routers.risks.bigquery.list_risks_paginated")
    def test_get_risks_success(self, mock_list_risks, auth_headers, mock_risks):
        """Test successful risks retrieval."""
        mock_list_risks.return_value = {
            "items": mock_risks,
            "total": len(mock_risks),
            "limit": 20,
            "offset": 0,
            "has_more": False
        }
        
        response = client.get("/risks/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        # Paginated response format
        assert "items" in data
        assert len(data["items"]) == 2
        assert data["items"][0]["risk_level"] == "HIGH"
    
    @patch("routers.risks.bigquery.list_risks_paginated")
    def test_get_risks_with_level_filter(self, mock_list_risks, auth_headers, mock_risks):
        """Test risks retrieval with risk_level filter."""
        mock_list_risks.return_value = {
            "items": [mock_risks[0]],
            "total": 1,
            "limit": 20,
            "offset": 0,
            "has_more": False
        }
        
        response = client.get("/risks/?risk_level=HIGH", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    @patch("routers.risks.bigquery.list_risks_paginated")
    def test_get_risks_with_multiple_filters(self, mock_list_risks, auth_headers):
        """Test risks retrieval with multiple filters."""
        mock_list_risks.return_value = {
            "items": [],
            "total": 0,
            "limit": 20,
            "offset": 0,
            "has_more": False
        }
        
        response = client.get(
            "/risks/?project_id=proj-001&risk_level=HIGH&meeting_id=meet-001",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
    
    @patch("routers.risks.bigquery.get_risk_stats")
    def test_get_risk_stats_success(self, mock_get_stats, auth_headers, mock_risk_stats):
        """Test successful risk statistics retrieval."""
        mock_get_stats.return_value = mock_risk_stats
        
        response = client.get("/risks/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert data["by_level"]["HIGH"] == 2
        assert len(data["by_project"]) == 2
    
    @patch("routers.risks.bigquery.list_decisions_paginated")
    def test_get_decisions_success(self, mock_list_decisions, auth_headers, mock_decisions):
        """Test successful decisions retrieval."""
        mock_list_decisions.return_value = {
            "items": mock_decisions,
            "total": len(mock_decisions),
            "limit": 20,
            "offset": 0,
            "has_more": False
        }
        
        response = client.get("/risks/decisions", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        # Paginated response format
        assert "items" in data
        assert len(data["items"]) == 1
        assert "Python" in data["items"][0]["decision_content"]


# ==============================================================================
# Export Endpoint Tests
# ==============================================================================

class TestExportEndpoint:
    """Tests for export endpoints."""
    
    def test_export_projects_missing_auth(self):
        """Test export projects without auth should fail."""
        response = client.get("/export/projects")
        assert response.status_code == 401
    
    @patch("routers.export.bigquery.list_projects")
    def test_export_projects_success(self, mock_list_projects, auth_headers, mock_projects):
        """Test successful projects CSV export."""
        mock_list_projects.return_value = mock_projects
        
        response = client.get("/export/projects", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
        assert "project_id" in response.text
        assert "Project Alpha" in response.text
    
    @patch("routers.export.bigquery.list_tasks")
    def test_export_tasks_success(self, mock_list_tasks, auth_headers, mock_tasks):
        """Test successful tasks CSV export."""
        mock_list_tasks.return_value = mock_tasks
        
        response = client.get("/export/tasks", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "task_id" in response.text
        assert "Complete unit testing" in response.text
    
    @patch("routers.export.bigquery.list_tasks")
    def test_export_tasks_with_project_filter(self, mock_list_tasks, auth_headers, mock_tasks):
        """Test tasks CSV export with project filter."""
        mock_list_tasks.return_value = mock_tasks
        
        response = client.get("/export/tasks?project_id=proj-001", headers=auth_headers)
        
        assert response.status_code == 200
        mock_list_tasks.assert_called_once_with(project_id="proj-001")
    
    @patch("routers.export.bigquery.list_risks")
    def test_export_risks_success(self, mock_list_risks, auth_headers, mock_risks):
        """Test successful risks CSV export."""
        mock_list_risks.return_value = mock_risks
        
        response = client.get("/export/risks", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "risk_id" in response.text
        assert "risk_level" in response.text
    
    @patch("routers.export.bigquery.list_decisions")
    def test_export_decisions_success(self, mock_list_decisions, auth_headers, mock_decisions):
        """Test successful decisions CSV export."""
        mock_list_decisions.return_value = mock_decisions
        
        response = client.get("/export/decisions", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "decision_id" in response.text


# ==============================================================================
# Export Service Tests
# ==============================================================================

class TestExportService:
    """Tests for export service functions."""
    
    def test_generate_csv_basic(self):
        """Test basic CSV generation."""
        from services.export import generate_csv
        
        data = [
            {"id": "1", "name": "Item 1"},
            {"id": "2", "name": "Item 2"}
        ]
        headers = ["id", "name"]
        
        csv_content = generate_csv(data, headers)
        
        assert "id,name" in csv_content
        assert "1,Item 1" in csv_content
        assert "2,Item 2" in csv_content
    
    def test_generate_projects_csv(self, mock_projects):
        """Test projects CSV generation."""
        from services.export import generate_projects_csv
        
        csv_content = generate_projects_csv(mock_projects)
        
        assert "project_id" in csv_content
        assert "project_name" in csv_content
        assert "Project Alpha" in csv_content
    
    def test_generate_tasks_csv(self, mock_tasks):
        """Test tasks CSV generation."""
        from services.export import generate_tasks_csv
        
        csv_content = generate_tasks_csv(mock_tasks)
        
        assert "task_id" in csv_content
        assert "task_title" in csv_content
        assert "due_date" in csv_content
        assert "Complete unit testing" in csv_content
    
    def test_generate_risks_csv(self, mock_risks):
        """Test risks CSV generation."""
        from services.export import generate_risks_csv
        
        csv_content = generate_risks_csv(mock_risks)
        
        assert "risk_id" in csv_content
        assert "risk_level" in csv_content
        assert "source_sentence" in csv_content
    
    def test_get_export_filename(self):
        """Test export filename generation."""
        from services.export import get_export_filename
        
        filename = get_export_filename("tasks")
        
        assert filename.startswith("project_progress_tasks_")
        assert filename.endswith(".csv")


# ==============================================================================
# Cookie-based Authentication Tests
# ==============================================================================

class TestCookieAuthentication:
    """Tests for cookie-based authentication."""
    
    def test_auth_via_cookie(self, valid_user_data, mock_projects):
        """Test authentication works via cookie."""
        with patch("routers.projects.bigquery.list_projects") as mock_list:
            mock_list.return_value = mock_projects
            
            token = create_access_token(valid_user_data)
            
            # Set cookie directly in test client
            response = client.get(
                "/projects/",
                cookies={"access_token": token}
            )
            
            assert response.status_code == 200


# ==============================================================================
# Error Handling Tests
# ==============================================================================

class TestErrorHandling:
    """Tests for API error handling."""
    
    def test_validation_error_response(self):
        """Test validation errors return structured response."""
        # This would trigger if we had endpoints with strict validation
        # The endpoint exists but the validation is minimal in current implementation
        pass
    
    @patch("routers.projects.bigquery.list_projects")
    def test_internal_error_handling(self, mock_list, auth_headers):
        """Test internal errors return 500 with message."""
        mock_list.side_effect = Exception("Unexpected database error")
        
        response = client.get("/projects/", headers=auth_headers)
        
        assert response.status_code == 500
        assert "Unexpected database error" in response.json()["detail"]
