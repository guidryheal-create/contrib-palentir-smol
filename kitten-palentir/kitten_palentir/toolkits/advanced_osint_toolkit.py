"""Palentir OSINT - Advanced OSINT Toolkits.

Implements toolkits for Liferaft, Censys, Maltego, and other OSINT services.
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

import httpx
from camel.toolkits import FunctionTool


logger = logging.getLogger(__name__)


@dataclass
class CensysResult:
    """Censys search result."""

    ip: str
    ports: List[int]
    services: Dict[str, Any]
    location: Dict[str, str]
    asn: str
    isp: str
    confidence: float


@dataclass
class LiferaftResult:
    """Liferaft breach result."""

    breach_name: str
    date: str
    records_count: int
    data_types: List[str]
    source_url: str
    confidence: float


@dataclass
class MaltegoEntity:
    """Maltego entity."""

    entity_type: str
    value: str
    properties: Dict[str, Any]
    links: List[str]


class CensysToolkit:
    """Censys.io OSINT toolkit."""

    def __init__(self, api_id: str, api_secret: str):
        """Initialize Censys toolkit.

        Args:
            api_id: Censys API ID
            api_secret: Censys API secret
        """
        self.api_id = api_id
        self.api_secret = api_secret
        self.base_url = "https://search.censys.io/api/v2"
        self.client = httpx.AsyncClient(
            auth=(api_id, api_secret),
            timeout=30.0,
        )

    def get_tools(self) -> List[FunctionTool]:
        """Get CAMEL-compatible tools.
        
        Returns:
            List of FunctionTool instances
        """
        return [
            FunctionTool(self.search_ipv4),
            FunctionTool(self.search_certificates),
            FunctionTool(self.get_ip_details),
        ]

    async def search_ipv4(self, query: str) -> List[Dict[str, Any]]:
        """Search IPv4 addresses.

        Args:
            query: Search query string

        Returns:
            List of IPv4 search results as dictionaries
        """
        logger.info(f"Searching IPv4: {query}")

        try:
            response = await self.client.get(
                f"{self.base_url}/ipv4/search",
                params={"q": query},
            )
            response.raise_for_status()

            data = response.json()
            results = []

            for result in data.get("results", []):
                results.append({
                    "ip": result.get("ip", ""),
                    "ports": result.get("ports", []),
                    "services": result.get("services", {}),
                    "location": result.get("location", {}),
                    "asn": result.get("autonomous_system", {}).get("asn", ""),
                    "isp": result.get("autonomous_system", {}).get("name", ""),
                    "confidence": 0.95,
                })

            logger.info(f"Found {len(results)} IPv4 results")
            return results

        except Exception as e:
            logger.error(f"IPv4 search failed: {e}")
            return []

    async def search_certificates(self, query: str) -> List[Dict[str, Any]]:
        """Search SSL certificates.

        Args:
            query: Search query (domain or email)

        Returns:
            List of certificate dictionaries
        """
        logger.info(f"Searching certificates: {query}")

        try:
            response = await self.client.get(
                f"{self.base_url}/certificates/search",
                params={"q": query},
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            logger.info(f"Found {len(results)} certificates")
            return results

        except Exception as e:
            logger.error(f"Certificate search failed: {e}")
            return []

    async def get_ip_details(self, ip: str) -> Dict[str, Any]:
        """Get detailed IP information.

        Args:
            ip: IP address to query

        Returns:
            Dictionary containing IP details
        """
        logger.info(f"Getting IP details: {ip}")

        try:
            response = await self.client.get(f"{self.base_url}/ipv4/{ip}")
            response.raise_for_status()

            data = response.json()
            logger.info(f"Got IP details for {ip}")
            return data

        except Exception as e:
            logger.error(f"IP details failed: {e}")
            return {}

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class LiferaftToolkit:
    """Liferaft.com OSINT toolkit for breach data."""

    def __init__(self, api_key: str):
        """Initialize Liferaft toolkit.

        Args:
            api_key: Liferaft API key
        """
        self.api_key = api_key
        self.base_url = "https://api.liferaft.com"
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    def get_tools(self) -> List[FunctionTool]:
        """Get CAMEL-compatible tools.
        
        Returns:
            List of FunctionTool instances
        """
        return [
            FunctionTool(self.search_breaches),
            FunctionTool(self.get_breach_details),
            FunctionTool(self.search_dark_web),
        ]

    async def search_breaches(self, query: str) -> List[Dict[str, Any]]:
        """Search for data breaches.

        Args:
            query: Email, domain, or username to search

        Returns:
            List of breach result dictionaries
        """
        logger.info(f"Searching breaches: {query}")

        try:
            response = await self.client.get(
                f"{self.base_url}/search",
                params={"q": query},
            )
            response.raise_for_status()

            data = response.json()
            results = []

            for breach in data.get("breaches", []):
                results.append({
                    "breach_name": breach.get("name", ""),
                    "date": breach.get("date", ""),
                    "records_count": breach.get("records", 0),
                    "data_types": breach.get("data_types", []),
                    "source_url": breach.get("source_url", ""),
                    "confidence": 0.90,
                })

            logger.info(f"Found {len(results)} breaches")
            return results

        except Exception as e:
            logger.error(f"Breach search failed: {e}")
            return []

    async def get_breach_details(self, breach_id: str) -> Dict[str, Any]:
        """Get detailed breach information.

        Args:
            breach_id: Breach ID to query

        Returns:
            Dictionary containing breach details
        """
        logger.info(f"Getting breach details: {breach_id}")

        try:
            response = await self.client.get(f"{self.base_url}/breaches/{breach_id}")
            response.raise_for_status()

            data = response.json()
            logger.info(f"Got breach details for {breach_id}")
            return data

        except Exception as e:
            logger.error(f"Breach details failed: {e}")
            return {}

    async def search_dark_web(self, query: str) -> List[Dict[str, Any]]:
        """Search dark web mentions.

        Args:
            query: Search query string

        Returns:
            List of dark web mention dictionaries
        """
        logger.info(f"Searching dark web: {query}")

        try:
            response = await self.client.get(
                f"{self.base_url}/darkweb/search",
                params={"q": query},
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("mentions", [])

            logger.info(f"Found {len(results)} dark web mentions")
            return results

        except Exception as e:
            logger.error(f"Dark web search failed: {e}")
            return []

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class MaltegoToolkit:
    """Maltego OSINT toolkit integration."""

    def __init__(self, api_key: str, api_url: str = "https://api.maltego.com"):
        """Initialize Maltego toolkit.

        Args:
            api_key: Maltego API key
            api_url: Maltego API URL
        """
        self.api_key = api_key
        self.api_url = api_url
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    def get_tools(self) -> List[FunctionTool]:
        """Get CAMEL-compatible tools.
        
        Returns:
            List of FunctionTool instances
        """
        return [
            FunctionTool(self.transform_entity),
            FunctionTool(self.get_entity_details),
        ]

    async def transform_entity(
        self,
        entity_type: str,
        entity_value: str,
    ) -> List[Dict[str, Any]]:
        """Transform entity using Maltego.

        Args:
            entity_type: Entity type (Email, Domain, etc.)
            entity_value: Entity value to transform

        Returns:
            List of transformed entity dictionaries
        """
        logger.info(f"Transforming {entity_type}: {entity_value}")

        try:
            response = await self.client.post(
                f"{self.api_url}/transform",
                json={
                    "entity_type": entity_type,
                    "entity_value": entity_value,
                },
            )
            response.raise_for_status()

            data = response.json()
            results = []

            for entity in data.get("entities", []):
                results.append({
                    "entity_type": entity.get("type", ""),
                    "value": entity.get("value", ""),
                    "properties": entity.get("properties", {}),
                    "links": entity.get("links", []),
                })

            logger.info(f"Transformed to {len(results)} entities")
            return results

        except Exception as e:
            logger.error(f"Transform failed: {e}")
            return []

    async def get_entity_details(self, entity_id: str) -> Dict[str, Any]:
        """Get detailed entity information.

        Args:
            entity_id: Entity ID to query

        Returns:
            Dictionary containing entity details
        """
        logger.info(f"Getting entity details: {entity_id}")

        try:
            response = await self.client.get(f"{self.api_url}/entities/{entity_id}")
            response.raise_for_status()

            data = response.json()
            logger.info(f"Got entity details for {entity_id}")
            return data

        except Exception as e:
            logger.error(f"Entity details failed: {e}")
            return {}

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class SocialLinksToolkit:
    """Social Links (SL Crimewall) OSINT toolkit."""

    def __init__(self, api_key: str):
        """Initialize Social Links toolkit.

        Args:
            api_key: Social Links API key
        """
        self.api_key = api_key
        self.base_url = "https://api.sociallinks.io"
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=30.0,
        )

    def get_tools(self) -> List[FunctionTool]:
        """Get CAMEL-compatible tools.
        
        Returns:
            List of FunctionTool instances
        """
        return [
            FunctionTool(self.search_person),
            FunctionTool(self.search_username),
            FunctionTool(self.search_email),
        ]

    async def search_person(self, name: str, email: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for person across social networks.

        Args:
            name: Person name to search
            email: Optional email address

        Returns:
            List of profile dictionaries
        """
        logger.info(f"Searching person: {name}")

        try:
            params = {"name": name}
            if email:
                params["email"] = email

            response = await self.client.get(
                f"{self.base_url}/search/person",
                params=params,
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("profiles", [])

            logger.info(f"Found {len(results)} profiles")
            return results

        except Exception as e:
            logger.error(f"Person search failed: {e}")
            return []

    async def search_username(self, username: str) -> List[Dict[str, Any]]:
        """Search for username across platforms.

        Args:
            username: Username to search

        Returns:
            List of account dictionaries
        """
        logger.info(f"Searching username: {username}")

        try:
            response = await self.client.get(
                f"{self.base_url}/search/username",
                params={"username": username},
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("accounts", [])

            logger.info(f"Found {len(results)} accounts")
            return results

        except Exception as e:
            logger.error(f"Username search failed: {e}")
            return []

    async def search_email(self, email: str) -> List[Dict[str, Any]]:
        """Search for email across platforms.

        Args:
            email: Email address to search

        Returns:
            List of profile dictionaries
        """
        logger.info(f"Searching email: {email}")

        try:
            response = await self.client.get(
                f"{self.base_url}/search/email",
                params={"email": email},
            )
            response.raise_for_status()

            data = response.json()
            results = data.get("profiles", [])

            logger.info(f"Found {len(results)} profiles")
            return results

        except Exception as e:
            logger.error(f"Email search failed: {e}")
            return []

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()


class AdvancedOSINTToolkitManager:
    """Manager for all advanced OSINT toolkits."""

    def __init__(
        self,
        censys_api_id: Optional[str] = None,
        censys_api_secret: Optional[str] = None,
        liferaft_api_key: Optional[str] = None,
        maltego_api_key: Optional[str] = None,
        sociallinks_api_key: Optional[str] = None,
    ):
        """Initialize toolkit manager.

        Args:
            censys_api_id: Censys API ID
            censys_api_secret: Censys API secret
            liferaft_api_key: Liferaft API key
            maltego_api_key: Maltego API key
            sociallinks_api_key: Social Links API key
        """
        self.censys = None
        self.liferaft = None
        self.maltego = None
        self.sociallinks = None

        if censys_api_id and censys_api_secret:
            self.censys = CensysToolkit(censys_api_id, censys_api_secret)
            logger.info("Censys toolkit initialized")

        if liferaft_api_key:
            self.liferaft = LiferaftToolkit(liferaft_api_key)
            logger.info("Liferaft toolkit initialized")

        if maltego_api_key:
            self.maltego = MaltegoToolkit(maltego_api_key)
            logger.info("Maltego toolkit initialized")

        if sociallinks_api_key:
            self.sociallinks = SocialLinksToolkit(sociallinks_api_key)
            logger.info("Social Links toolkit initialized")

    async def search_ip_comprehensive(self, ip: str) -> Dict[str, Any]:
        """Comprehensive IP search across all toolkits.

        Args:
            ip: IP address

        Returns:
            Combined results
        """
        logger.info(f"Comprehensive IP search: {ip}")

        results = {
            "ip": ip,
            "censys": None,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if self.censys:
            try:
                results["censys"] = await self.censys.get_ip_details(ip)
            except Exception as e:
                logger.error(f"Censys IP search failed: {e}")

        return results

    async def search_person_comprehensive(
        self,
        name: str,
        email: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Comprehensive person search across all toolkits.

        Args:
            name: Person name
            email: Optional email

        Returns:
            Combined results
        """
        logger.info(f"Comprehensive person search: {name}")

        results = {
            "name": name,
            "email": email,
            "sociallinks": None,
            "liferaft": None,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if self.sociallinks:
            try:
                results["sociallinks"] = await self.sociallinks.search_person(name, email)
            except Exception as e:
                logger.error(f"Social Links search failed: {e}")

        if self.liferaft and email:
            try:
                results["liferaft"] = await self.liferaft.search_breaches(email)
            except Exception as e:
                logger.error(f"Liferaft search failed: {e}")

        return results

    async def close(self):
        """Close all toolkit connections."""
        if self.censys:
            await self.censys.close()
        if self.liferaft:
            await self.liferaft.close()
        if self.maltego:
            await self.maltego.close()
        if self.sociallinks:
            await self.sociallinks.close()

        logger.info("All toolkits closed")
