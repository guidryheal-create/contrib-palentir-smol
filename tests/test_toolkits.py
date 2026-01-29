"""Tests for OSINT toolkits with mocked services."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, List, Any

from src.toolkits.advanced_osint_toolkit import (
    CensysToolkit,
    LiferaftToolkit,
    MaltegoToolkit,
    SocialLinksToolkit,
)
from src.toolkits.social_media_toolkit import SocialMediaToolkit
from camel.toolkits import FunctionTool


class TestCensysToolkit:
    """Test Censys Toolkit."""

    @pytest.fixture
    def toolkit(self):
        """Create toolkit instance."""
        return CensysToolkit(api_id="test_id", api_secret="test_secret")

    def test_get_tools(self, toolkit):
        """Test get_tools returns FunctionTool instances."""
        tools = toolkit.get_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert all(isinstance(tool, FunctionTool) for tool in tools)

    @pytest.mark.asyncio
    async def test_search_ipv4(self, toolkit):
        """Test search_ipv4 returns dict list."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "results": [
                {
                    "ip": "1.2.3.4",
                    "ports": [80, 443],
                    "services": {},
                    "location": {},
                    "autonomous_system": {"asn": "12345", "name": "Test ISP"},
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(toolkit.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            results = await toolkit.search_ipv4("test query")
            
            assert isinstance(results, list)
            assert len(results) > 0
            assert isinstance(results[0], dict)
            assert "ip" in results[0]
            assert "confidence" in results[0]

    @pytest.mark.asyncio
    async def test_search_certificates(self, toolkit):
        """Test search_certificates returns dict list."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()

        with patch.object(toolkit.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            results = await toolkit.search_certificates("example.com")
            
            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_get_ip_details(self, toolkit):
        """Test get_ip_details returns dict."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"ip": "1.2.3.4", "details": "test"}
        mock_response.raise_for_status = MagicMock()

        with patch.object(toolkit.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            result = await toolkit.get_ip_details("1.2.3.4")
            
            assert isinstance(result, dict)


class TestLiferaftToolkit:
    """Test Liferaft Toolkit."""

    @pytest.fixture
    def toolkit(self):
        """Create toolkit instance."""
        return LiferaftToolkit(api_key="test_key")

    def test_get_tools(self, toolkit):
        """Test get_tools returns FunctionTool instances."""
        tools = toolkit.get_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert all(isinstance(tool, FunctionTool) for tool in tools)

    @pytest.mark.asyncio
    async def test_search_breaches(self, toolkit):
        """Test search_breaches returns dict list."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "breaches": [
                {
                    "name": "Test Breach",
                    "date": "2024-01-01",
                    "records": 1000,
                    "data_types": ["email", "password"],
                    "source_url": "https://example.com",
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(toolkit.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            results = await toolkit.search_breaches("test@example.com")
            
            assert isinstance(results, list)
            if results:
                assert isinstance(results[0], dict)
                assert "breach_name" in results[0]
                assert "confidence" in results[0]


class TestMaltegoToolkit:
    """Test Maltego Toolkit."""

    @pytest.fixture
    def toolkit(self):
        """Create toolkit instance."""
        return MaltegoToolkit(api_key="test_key")

    def test_get_tools(self, toolkit):
        """Test get_tools returns FunctionTool instances."""
        tools = toolkit.get_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert all(isinstance(tool, FunctionTool) for tool in tools)

    @pytest.mark.asyncio
    async def test_transform_entity(self, toolkit):
        """Test transform_entity returns dict list."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "entities": [
                {
                    "type": "Email",
                    "value": "test@example.com",
                    "properties": {},
                    "links": [],
                }
            ]
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(toolkit.client, "post", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = mock_response
            results = await toolkit.transform_entity("Email", "test@example.com")
            
            assert isinstance(results, list)
            if results:
                assert isinstance(results[0], dict)
                assert "entity_type" in results[0]


class TestSocialLinksToolkit:
    """Test Social Links Toolkit."""

    @pytest.fixture
    def toolkit(self):
        """Create toolkit instance."""
        return SocialLinksToolkit(api_key="test_key")

    def test_get_tools(self, toolkit):
        """Test get_tools returns FunctionTool instances."""
        tools = toolkit.get_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert all(isinstance(tool, FunctionTool) for tool in tools)

    @pytest.mark.asyncio
    async def test_search_person(self, toolkit):
        """Test search_person returns dict list."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"profiles": []}
        mock_response.raise_for_status = MagicMock()

        with patch.object(toolkit.client, "get", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            results = await toolkit.search_person("John Doe")
            
            assert isinstance(results, list)


class TestSocialMediaToolkit:
    """Test Social Media Toolkit."""

    @pytest.fixture
    def toolkit(self):
        """Create toolkit instance."""
        return SocialMediaToolkit()

    def test_get_tools(self, toolkit):
        """Test get_tools returns FunctionTool instances."""
        tools = toolkit.get_tools()
        assert isinstance(tools, list)
        assert len(tools) > 0
        assert all(isinstance(tool, FunctionTool) for tool in tools)

    @pytest.mark.asyncio
    async def test_search_linkedin_people(self, toolkit):
        """Test search_linkedin_people returns dict list."""
        results = await toolkit.search_linkedin_people("test query", limit=5)
        
        assert isinstance(results, list)
        if results:
            assert isinstance(results[0], dict)
            assert "profile_id" in results[0]

    @pytest.mark.asyncio
    async def test_search_facebook_people(self, toolkit):
        """Test search_facebook_people returns dict list."""
        results = await toolkit.search_facebook_people("test query", limit=5)
        
        assert isinstance(results, list)
        if results:
            assert isinstance(results[0], dict)
            assert "profile_id" in results[0]

    @pytest.mark.asyncio
    async def test_search_instagram_profiles(self, toolkit):
        """Test search_instagram_profiles returns dict list."""
        results = await toolkit.search_instagram_profiles("test query", limit=5)
        
        assert isinstance(results, list)
        if results:
            assert isinstance(results[0], dict)
            assert "username" in results[0]


@pytest.mark.asyncio
async def test_toolkit_error_handling():
    """Test toolkit error handling."""
    toolkit = CensysToolkit(api_id="test_id", api_secret="test_secret")
    
    with patch.object(toolkit.client, "get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Network error")
        results = await toolkit.search_ipv4("test")
        
        assert isinstance(results, list)
        assert len(results) == 0  # Should return empty list on error

