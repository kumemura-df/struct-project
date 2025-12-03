"""Pytest configuration and shared fixtures."""
import os
import pytest

# Set test environment variables before any imports
os.environ["USE_LOCAL_DB"] = "false"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing"
os.environ["PROJECT_ID"] = "test-project"
os.environ["BIGQUERY_DATASET"] = "test_dataset"

