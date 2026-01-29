"""Palentir OSINT - Configuration Settings using Pydantic."""

import os
import logging
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, computed_field, field_validator

logger = logging.getLogger(__name__)


def _is_docker_environment() -> bool:
    """Check if running in Docker environment."""
    # Check for Docker-specific environment indicators
    return (
        os.path.exists("/.dockerenv") or
        os.environ.get("DOCKER_ENV", "").lower() == "true" or
        os.environ.get("CONTAINER_NAME") is not None
    )


def _get_service_host(service_name: str, docker_host: str, local_host: str = "localhost") -> str:
    """Get service host based on environment.
    
    Args:
        service_name: Name of the service (e.g., 'neo4j', 'redis')
        docker_host: Hostname to use in Docker (service name in docker-compose)
        local_host: Hostname to use locally (default: localhost)
    
    Returns:
        Appropriate hostname based on environment
    """
    # Check for explicit override via environment variable
    env_key = f"{service_name.upper()}_HOST"
    explicit_host = os.environ.get(env_key)
    if explicit_host:
        return explicit_host
    
    # Use docker host if in docker, otherwise local
    if _is_docker_environment():
        return docker_host
    return local_host


class Settings(BaseSettings):
    """Application settings with Docker/local environment support."""

    # Application
    app_name: str = Field(default="Palentir OSINT", description="Application name")
    app_version: str = Field(default="2.0.0", description="Application version")
    app_env: str = Field(default="development", description="Environment")
    debug: bool = Field(default=False, description="Debug mode")

    # API
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=4, description="Number of workers")
    api_reload: bool = Field(default=False, description="Auto-reload")

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8501"],
        description="CORS origins"
    )
    trusted_hosts: List[str] = Field(
        default=["*"],
        description="Trusted hosts"
    )
    
    # Environment
    environment: str = Field(default="development", description="Environment")
    
    # Docker/Local mode
    docker_env: bool = Field(default_factory=_is_docker_environment, description="Docker environment flag")
    use_docker_services: Optional[bool] = Field(default=None, description="Force use docker services")

    # Neo4j - supports both local and docker
    neo4j_host: Optional[str] = Field(default=None, description="Neo4j host (auto-detected if not set)")
    neo4j_port: int = Field(default=7687, description="Neo4j port")
    neo4j_uri: Optional[str] = Field(default=None, description="Neo4j URI (auto-constructed if not set)")
    neo4j_username: str = Field(default="neo4j", description="Neo4j username")
    neo4j_password: str = Field(default="password", description="Neo4j password")

    # Qdrant - supports both local and docker
    qdrant_host: Optional[str] = Field(default=None, description="Qdrant host (auto-detected if not set)")
    qdrant_port: int = Field(default=6333, description="Qdrant port")
    qdrant_api_key: Optional[str] = Field(default=None, description="Qdrant API key")

    # Redis - supports both local and docker
    redis_host: Optional[str] = Field(default=None, description="Redis host (auto-detected if not set)")
    redis_port: int = Field(default=6379, description="Redis port")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    
    @computed_field
    @property
    def effective_neo4j_host(self) -> str:
        """Get effective Neo4j host based on environment."""
        if self.neo4j_host:
            return self.neo4j_host
        use_docker = self.use_docker_services if self.use_docker_services is not None else self.docker_env
        return _get_service_host("neo4j", "neo4j", "localhost")
    
    @computed_field
    @property
    def effective_neo4j_uri(self) -> str:
        """Get effective Neo4j URI based on environment."""
        if self.neo4j_uri:
            return self.neo4j_uri
        return f"bolt://{self.effective_neo4j_host}:{self.neo4j_port}"
    
    @computed_field
    @property
    def effective_qdrant_host(self) -> str:
        """Get effective Qdrant host based on environment."""
        if self.qdrant_host:
            return self.qdrant_host
        use_docker = self.use_docker_services if self.use_docker_services is not None else self.docker_env
        return _get_service_host("qdrant", "qdrant", "localhost")
    
    @computed_field
    @property
    def effective_redis_host(self) -> str:
        """Get effective Redis host based on environment."""
        if self.redis_host:
            return self.redis_host
        use_docker = self.use_docker_services if self.use_docker_services is not None else self.docker_env
        return _get_service_host("redis", "redis", "localhost")

    # External APIs
    shodan_api_key: Optional[str] = Field(default=None, description="Shodan API key")
    twitter_api_key: Optional[str] = Field(default=None, description="Twitter API key")
    linkedin_api_key: Optional[str] = Field(default=None, description="LinkedIn API key")
    github_api_key: Optional[str] = Field(default=None, description="GitHub API key")
    censys_api_id: Optional[str] = Field(default=None, description="Censys API ID")
    censys_api_secret: Optional[str] = Field(default=None, description="Censys API Secret")
    liferaft_api_key: Optional[str] = Field(default=None, description="Liferaft API key")
    maltego_api_key: Optional[str] = Field(default=None, description="Maltego API key")
    sociallinks_api_key: Optional[str] = Field(default=None, description="Social Links API key")

    # CAMEL-AI
    camel_model_platform: str = Field(default="openai", description="CAMEL model platform")
    camel_model_type: str = Field(default="gpt-5", description="CAMEL model type (default: gpt-5 for best performance)")
    openai_api_key: str = Field(..., description="OpenAI API key (REQUIRED - CAMEL-AI depends on OpenAI)")

    @field_validator("openai_api_key")
    @classmethod
    def validate_openai_api_key(cls, v: str) -> str:
        """Validate OpenAI API key is provided."""
        if not v or v.strip() == "" or v.startswith("sk-your-") or v.startswith("your-"):
            raise ValueError(
                "OPENAI_API_KEY is required. Please set a valid OpenAI API key in your .env file. "
                "CAMEL-AI framework requires OpenAI API key to function."
            )
        return v

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from environment variables


def get_settings() -> Settings:
    """Get settings instance."""
    return Settings()


def get_service_config() -> dict:
    """Get service configuration based on environment.
    
    Returns:
        Dictionary with service configuration for local or docker
    """
    settings = get_settings()
    use_docker = settings.use_docker_services if settings.use_docker_services is not None else settings.docker_env
    
    if use_docker:
        return {
            "neo4j": {
                "host": "neo4j",
                "port": 7687,
                "uri": "bolt://neo4j:7687",
            },
            "redis": {
                "host": "redis",
                "port": 6379,
            },
            "qdrant": {
                "host": "qdrant",
                "port": 6333,
            },
        }
    else:
        return {
            "neo4j": {
                "host": settings.effective_neo4j_host,
                "port": settings.neo4j_port,
                "uri": settings.effective_neo4j_uri,
            },
            "redis": {
                "host": settings.effective_redis_host,
                "port": settings.redis_port,
            },
            "qdrant": {
                "host": settings.effective_qdrant_host,
                "port": settings.qdrant_port,
            },
        }
