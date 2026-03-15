"""
conftest.py — pytest fixtures shared across all test files.
"""
import sys
import os

# Add backend directory to sys.path early for reliable imports
PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base


# Use a fresh in-memory database for the test session
TEST_DATABASE_URL = "sqlite:///./test_fitness.db"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    import os
    if os.path.exists("test_fitness.db"):
        os.remove("test_fitness.db")
