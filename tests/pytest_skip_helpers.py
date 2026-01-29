"""Helper functions for skipping tests based on service/API availability."""

import os
import pytest
from typing import Optional


def skip_if_no_api_key(api_key_env_var: str, reason: Optional[str] = None):
    """Skip test if API key is not available.
    
    Args:
        api_key_env_var: Environment variable name for the API key
        reason: Optional reason for skipping
    
    Usage:
        @skip_if_no_api_key("OPENAI_API_KEY")
        def test_something():
            ...
    """
    api_key = os.environ.get(api_key_env_var)
    if not api_key:
        pytest.skip(reason or f"Missing {api_key_env_var} - test requires API key")


def skip_if_service_unavailable(service_name: str, host: str, port: int, reason: Optional[str] = None):
    """Skip test if service is not available.
    
    Args:
        service_name: Name of the service
        host: Service hostname
        port: Service port
        reason: Optional reason for skipping
    
    Usage:
        @skip_if_service_unavailable("Neo4j", "localhost", 7687)
        def test_something():
            ...
    """
    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        result = sock.connect_ex((host, port))
        sock.close()
        if result != 0:
            pytest.skip(reason or f"{service_name} not available at {host}:{port}")
    except Exception:
        pytest.skip(reason or f"Cannot connect to {service_name} at {host}:{port}")


def require_api_key(api_key_env_var: str):
    """Decorator to require API key for test.
    
    Args:
        api_key_env_var: Environment variable name for the API key
    
    Usage:
        @require_api_key("OPENAI_API_KEY")
        def test_something():
            ...
    """
    def decorator(func):
        return pytest.mark.skip_if_no_api_key(api_key_env_var)(func)
    return decorator


def require_service(service_name: str, host: str, port: int):
    """Decorator to require service for test.
    
    Args:
        service_name: Name of the service
        host: Service hostname
        port: Service port
    
    Usage:
        @require_service("Neo4j", "localhost", 7687)
        def test_something():
            ...
    """
    def decorator(func):
        return pytest.mark.skip_if_service_unavailable(service_name, host, port)(func)
    return decorator

