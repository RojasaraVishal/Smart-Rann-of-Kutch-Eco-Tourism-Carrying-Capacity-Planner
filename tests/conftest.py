"""
pytest configuration — shared fixtures and path setup.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Set test environment
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_kutch.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
os.environ.setdefault("IBM_API_KEY", "")
os.environ.setdefault("DEMO_MODE", "true")
