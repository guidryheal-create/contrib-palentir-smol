"""Pytest configuration and fixtures for Palentir OSINT."""

import pytest
import asyncio
from typing import Dict, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_neo4j_service():
    """Mock Neo4j service."""
    service = AsyncMock()
    service.execute_query = AsyncMock(return_value=[])
    service.create_node = AsyncMock(return_value="node_123")
    service.create_relationship = AsyncMock(return_value="rel_123")
    service.get_node = AsyncMock(return_value={"id": "node_123", "name": "Test"})
    service.delete_node = AsyncMock(return_value=True)
    service.close = AsyncMock(return_value=None)
    return service


@pytest.fixture
def mock_qdrant_service():
    """Mock Qdrant service."""
    service = AsyncMock()
    service.add_document = AsyncMock(return_value="doc_123")
    service.search = AsyncMock(
        return_value=[
            {
                "id": "doc_123",
                "text": "Test document",
                "score": 0.95,
            }
        ]
    )
    service.delete_document = AsyncMock(return_value=True)
    service.close = AsyncMock(return_value=None)
    return service


@pytest.fixture
def mock_redis_service():
    """Mock Redis service."""
    service = AsyncMock()
    service.set = AsyncMock(return_value=True)
    service.get = AsyncMock(return_value="test_value")
    service.delete = AsyncMock(return_value=True)
    service.lpush = AsyncMock(return_value=1)
    service.lpop = AsyncMock(return_value="item")
    service.close = AsyncMock(return_value=None)
    return service


@pytest.fixture
def mock_shodan_client():
    """Mock Shodan client."""
    client = AsyncMock()
    client.search = AsyncMock(
        return_value={
            "matches": [
                {
                    "ip_str": "192.168.1.1",
                    "port": 80,
                    "org": "Test Org",
                    "data": "HTTP/1.1 200 OK",
                }
            ],
            "total": 1,
        }
    )
    client.host = AsyncMock(
        return_value={
            "ip_str": "192.168.1.1",
            "ports": [80, 443],
            "org": "Test Org",
            "os": "Linux",
        }
    )
    return client


@pytest.fixture
def mock_dns_twist_client():
    """Mock DNS Twist client."""
    client = AsyncMock()
    client.enumerate_domains = AsyncMock(
        return_value=[
            {
                "domain": "test.com",
                "fuzzer": "typosquatting",
                "dns_a": "192.168.1.1",
            }
        ]
    )
    return client


@pytest.fixture
def mock_social_media_client():
    """Mock Social Media client."""
    client = AsyncMock()
    client.search_twitter = AsyncMock(
        return_value=[
            {
                "id": "tweet_123",
                "text": "Test tweet",
                "author": "testuser",
            }
        ]
    )
    client.search_linkedin = AsyncMock(
        return_value=[
            {
                "id": "profile_123",
                "name": "Test User",
                "title": "Software Engineer",
            }
        ]
    )
    return client


@pytest.fixture
def mock_image_search_client():
    """Mock Image Search client."""
    client = AsyncMock()
    client.search = AsyncMock(
        return_value=[
            {
                "url": "https://example.com/image.jpg",
                "title": "Test Image",
                "source": "example.com",
            }
        ]
    )
    return client


@pytest.fixture
def mock_ai_response():
    """Mock AI response."""
    return {
        "content": "Test response from AI",
        "tokens_used": 100,
        "model": "gpt-4",
        "timestamp": datetime.utcnow().isoformat(),
    }


@pytest.fixture
def sample_company_data() -> Dict[str, Any]:
    """Sample company data for testing."""
    return {
        "id": "company_123",
        "name": "Test Company Inc.",
        "type": "Company",
        "description": "A test company",
        "industry": "Technology",
        "country": "USA",
        "website": "https://testcompany.com",
        "founded_year": 2010,
        "employees": 500,
    }


@pytest.fixture
def sample_person_data() -> Dict[str, Any]:
    """Sample person data for testing."""
    return {
        "id": "person_123",
        "name": "John Doe",
        "type": "Person",
        "title": "CEO",
        "company": "Test Company Inc.",
        "email": "john@testcompany.com",
        "phone": "+1-555-0123",
        "linkedin": "https://linkedin.com/in/johndoe",
        "twitter": "https://twitter.com/johndoe",
    }


@pytest.fixture
def sample_domain_data() -> Dict[str, Any]:
    """Sample domain data for testing."""
    return {
        "id": "domain_123",
        "name": "testcompany.com",
        "type": "Domain",
        "registrar": "GoDaddy",
        "registration_date": "2010-01-15",
        "expiration_date": "2025-01-15",
        "nameservers": ["ns1.testcompany.com", "ns2.testcompany.com"],
        "mx_records": ["mail.testcompany.com"],
    }


@pytest.fixture
def sample_ip_data() -> Dict[str, Any]:
    """Sample IP address data for testing."""
    return {
        "id": "ip_123",
        "address": "192.168.1.1",
        "type": "IPAddress",
        "organization": "Test ISP",
        "country": "USA",
        "ports": [80, 443, 22],
        "services": ["HTTP", "HTTPS", "SSH"],
        "os": "Linux",
    }


@pytest.fixture
def sample_technology_data() -> Dict[str, Any]:
    """Sample technology data for testing."""
    return {
        "id": "tech_123",
        "name": "Python",
        "type": "Technology",
        "category": "Programming Language",
        "version": "3.11",
        "description": "Python programming language",
    }


@pytest.fixture
def mock_camel_ai_agent():
    """Mock CAMEL-AI agent."""
    agent = AsyncMock()
    agent.step = AsyncMock(
        return_value={
            "role": "Test Agent",
            "content": "Test response",
            "terminated": False,
        }
    )
    agent.reset = AsyncMock(return_value=None)
    return agent


@pytest.fixture
def mock_camel_ai_task():
    """Mock CAMEL-AI task."""
    from camel.tasks import Task, TaskPriority

    task = Task(
        task_id="task_123",
        title="Test Task",
        description="A test task",
        priority=TaskPriority.NORMAL,
    )
    return task


@pytest.fixture
def mock_camel_ai_workforce():
    """Mock CAMEL-AI workforce."""
    workforce = AsyncMock()
    workforce.add_agent = AsyncMock(return_value=None)
    workforce.remove_agent = AsyncMock(return_value=None)
    workforce.get_agents = AsyncMock(return_value=[])
    workforce.execute_task = AsyncMock(return_value={"status": "completed"})
    workforce.run = AsyncMock(return_value={"status": "success", "result": "Task completed"})
    workforce.get_shared_memory = AsyncMock(return_value={})
    return workforce


@pytest.fixture
def mock_environment(monkeypatch):
    """Mock environment variables."""
    env_vars = {
        "APP_NAME": "Palentir OSINT",
        "APP_VERSION": "2.0.0",
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG",
        "API_HOST": "0.0.0.0",
        "API_PORT": "8000",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USERNAME": "neo4j",
        "NEO4J_PASSWORD": "test_password",
        "REDIS_HOST": "localhost",
        "REDIS_PORT": "6379",
        "QDRANT_HOST": "localhost",
        "QDRANT_PORT": "6333",
        "OPENAI_API_KEY": "test_key",
        "TESTING": "true",
    }

    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    return env_vars


@pytest.fixture
def mock_logger(monkeypatch):
    """Mock logger."""
    logger = MagicMock()
    logger.info = MagicMock()
    logger.debug = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.critical = MagicMock()
    return logger


@pytest.fixture
def mock_http_client():
    """Mock HTTP client."""
    client = AsyncMock()
    client.get = AsyncMock(
        return_value=MagicMock(
            status_code=200,
            json=AsyncMock(return_value={"status": "ok"}),
        )
    )
    client.post = AsyncMock(
        return_value=MagicMock(
            status_code=201,
            json=AsyncMock(return_value={"id": "123", "status": "created"}),
        )
    )
    client.close = AsyncMock(return_value=None)
    return client


@pytest.fixture
def mock_graph_context() -> Dict[str, Any]:
    """Mock graph context."""
    return {
        "nodes": [
            {
                "id": "node_1",
                "label": "Test Company",
                "type": "Company",
                "icon": "building",
            },
            {
                "id": "node_2",
                "label": "John Doe",
                "type": "Person",
                "icon": "user",
            },
        ],
        "edges": [
            {
                "id": "edge_1",
                "source": "node_1",
                "target": "node_2",
                "type": "WORKS_AT",
            }
        ],
    }


@pytest.fixture
def mock_pipeline_context() -> Dict[str, Any]:
    """Mock pipeline context."""
    return {
        "pipeline_id": "pipeline_123",
        "stages": [
            {
                "stage_id": "stage_1",
                "name": "Network Analysis",
                "status": "pending",
            }
        ],
        "graph": {"nodes": [], "edges": []},
        "memory": {},
    }


@pytest.fixture
def mock_graph_builder_agent():
    """Mock Graph Builder Agent."""
    agent = AsyncMock()
    agent.process_event = AsyncMock(
        return_value={
            "nodes_created": 2,
            "relationships_created": 1,
            "status": "success",
        }
    )
    return agent


@pytest.fixture
def sample_intelligence_event() -> Dict[str, Any]:
    """Sample intelligence event."""
    return {
        "event_type": "person_found",
        "source_agent": "SocialMediaAgent",
        "data": {
            "name": "John Doe",
            "email": "john@example.com",
            "company": "Tech Corp",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singleton instances before each test."""
    # This ensures each test gets fresh instances
    yield
    # Cleanup after test


# Markers for test categorization
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "agent: mark test as an agent test"
    )
    config.addinivalue_line(
        "markers", "pipeline: mark test as a pipeline test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow"
    )
    config.addinivalue_line(
        "markers", "requires_api: mark test as requiring external API keys"
    )
    config.addinivalue_line(
        "markers", "requires_service: mark test as requiring external services (Neo4j, Redis, etc.)"
    )
    config.addinivalue_line(
        "markers", "skip_if_no_api_key: skip test if API key is not available"
    )
