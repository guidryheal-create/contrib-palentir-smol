"""Service configuration utilities for local and docker environments."""

import os
from typing import Dict, Optional
from src.config.settings import get_settings


def is_docker_environment() -> bool:
    """Check if running in Docker environment.
    
    Returns:
        True if running in Docker, False otherwise
    """
    return (
        os.path.exists("/.dockerenv") or
        os.environ.get("DOCKER_ENV", "").lower() == "true" or
        os.environ.get("CONTAINER_NAME") is not None
    )


def get_neo4j_config() -> Dict[str, str]:
    """Get Neo4j configuration based on environment.
    
    Returns:
        Dictionary with Neo4j connection details
    """
    settings = get_settings()
    use_docker = settings.use_docker_services if settings.use_docker_services is not None else settings.docker_env
    
    if use_docker:
        return {
            "uri": "bolt://neo4j:7687",
            "host": "neo4j",
            "port": 7687,
            "username": settings.neo4j_username,
            "password": settings.neo4j_password,
        }
    else:
        # Check for explicit override
        host = os.environ.get("NEO4J_HOST", "localhost")
        port = int(os.environ.get("NEO4J_PORT", "7687"))
        return {
            "uri": f"bolt://{host}:{port}",
            "host": host,
            "port": port,
            "username": settings.neo4j_username,
            "password": settings.neo4j_password,
        }


def get_redis_config() -> Dict[str, any]:
    """Get Redis configuration based on environment.
    
    Returns:
        Dictionary with Redis connection details
    """
    settings = get_settings()
    use_docker = settings.use_docker_services if settings.use_docker_services is not None else settings.docker_env
    
    if use_docker:
        return {
            "host": "redis",
            "port": 6379,
            "password": settings.redis_password,
        }
    else:
        # Check for explicit override
        host = os.environ.get("REDIS_HOST", "localhost")
        port = int(os.environ.get("REDIS_PORT", "6379"))
        return {
            "host": host,
            "port": port,
            "password": settings.redis_password,
        }


def get_qdrant_config() -> Dict[str, any]:
    """Get Qdrant configuration based on environment.
    
    Returns:
        Dictionary with Qdrant connection details
    """
    settings = get_settings()
    use_docker = settings.use_docker_services if settings.use_docker_services is not None else settings.docker_env
    
    if use_docker:
        return {
            "host": "qdrant",
            "port": 6333,
            "api_key": settings.qdrant_api_key,
        }
    else:
        # Check for explicit override
        host = os.environ.get("QDRANT_HOST", "localhost")
        port = int(os.environ.get("QDRANT_PORT", "6333"))
        return {
            "host": host,
            "port": port,
            "api_key": settings.qdrant_api_key,
        }


def get_all_service_configs() -> Dict[str, Dict[str, any]]:
    """Get all service configurations.
    
    Returns:
        Dictionary with all service configurations
    """
    return {
        "neo4j": get_neo4j_config(),
        "redis": get_redis_config(),
        "qdrant": get_qdrant_config(),
    }

