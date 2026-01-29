"""Palentir OSINT - Graph Builder Agent.

Advanced CAMEL-AI agent that builds and maintains the knowledge graph.
Integrates Neo4j, Graphistry, and Streamlit for real-time visualization.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from uuid import uuid4

from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType

from models.graph_nodes import (
    GraphNode,
    GraphEdge,
    NodeMetadata,
    NodeType,
    PersonNodeMetadata,
    CompanyNodeMetadata,
    IPAddressNodeMetadata,
    DomainNodeMetadata,
    EdgeMetadata,
    RelationType,
)
from services.neo4j_service import Neo4jService
from services.graphistry_service import GraphistryService


logger = logging.getLogger(__name__)


class IntelligenceEvent:
    """Event from other agents."""

    def __init__(
        self,
        event_type: str,
        source_agent: str,
        data: Dict[str, Any],
        timestamp: Optional[str] = None,
    ):
        """Initialize intelligence event.

        Args:
            event_type: Type of event (person_found, company_found, etc.)
            source_agent: Name of agent that generated event
            data: Event data
            timestamp: Event timestamp
        """
        self.event_type = event_type
        self.source_agent = source_agent
        self.data = data
        self.timestamp = timestamp or datetime.utcnow().isoformat()


class GraphBuilderAgent:
    """Graph Builder Agent using CAMEL-AI.

    Receives intelligence events from other agents and builds/updates
    the Neo4j knowledge graph with Graphistry visualization.
    """

    def __init__(
        self,
        neo4j_url: str = "bolt://localhost:7687",
        neo4j_user: str = "neo4j",
        neo4j_password: str = "password",
    ):
        """Initialize Graph Builder Agent.

        Args:
            neo4j_url: Neo4j connection URL
            neo4j_user: Neo4j username
            neo4j_password: Neo4j password
        """
        # Create model
        self.model = ModelFactory.create(
            model_platform=ModelPlatformType.OPENAI,
            model_type=ModelType.GPT_4,
        )

        # Initialize services
        self.neo4j_service = Neo4jService(
            url=neo4j_url,
            username=neo4j_user,
            password=neo4j_password,
        )
        self.graphistry_service = GraphistryService()

        # Create CAMEL-AI agent
        self.agent = ChatAgent(
            system_message=BaseMessage.make_assistant_message(
                role_name="GraphBuilder",
                content=(
                    "You are a graph builder agent. Analyze intelligence events "
                    "from other agents and build a comprehensive knowledge graph. "
                    "Create nodes for entities (people, companies, domains, IPs) "
                    "and edges for relationships. Detect duplicates and merge nodes "
                    "when appropriate. Maintain data quality and confidence scores."
                ),
            ),
            model=self.model,
        )

        # In-memory cache
        self.node_cache: Dict[str, GraphNode] = {}
        self.edge_cache: Dict[str, GraphEdge] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()

        # Streamlit update callbacks
        self.update_callbacks: List[callable] = []

        logger.info("Graph Builder Agent initialized")

    def register_update_callback(self, callback: callable) -> None:
        """Register callback for graph updates.

        Args:
            callback: Async callback function
        """
        self.update_callbacks.append(callback)
        logger.info(f"Registered update callback: {callback.__name__}")

    async def process_event(self, event: IntelligenceEvent) -> Dict[str, Any]:
        """Process intelligence event and update graph.

        Args:
            event: Intelligence event from agent

        Returns:
            Processing result
        """
        logger.info(f"Processing event: {event.event_type} from {event.source_agent}")

        try:
            # Route event to appropriate handler
            if event.event_type == "person_found":
                result = await self._handle_person_found(event)

            elif event.event_type == "company_found":
                result = await self._handle_company_found(event)

            elif event.event_type == "domain_found":
                result = await self._handle_domain_found(event)

            elif event.event_type == "ip_found":
                result = await self._handle_ip_found(event)

            elif event.event_type == "relationship_found":
                result = await self._handle_relationship_found(event)

            else:
                logger.warning(f"Unknown event type: {event.event_type}")
                result = {"status": "unknown_event"}

            # Notify subscribers
            await self._notify_updates(result)

            return result

        except Exception as e:
            logger.error(f"Event processing failed: {e}")
            return {
                "status": "failed",
                "error": str(e),
            }

    async def _handle_person_found(
        self,
        event: IntelligenceEvent,
    ) -> Dict[str, Any]:
        """Handle person found event.

        Args:
            event: Intelligence event

        Returns:
            Processing result
        """
        logger.info("Handling person found event")

        data = event.data
        person_id = f"person_{uuid4().hex[:8]}"

        # Check for duplicates
        existing = await self._find_duplicate_person(data)
        if existing:
            logger.info(f"Found duplicate person: {existing.node_id}")
            person_id = existing.node_id
            metadata = existing.metadata
            # Update metadata
            metadata.sources.append(event.source_agent)
            metadata.updated_at = datetime.utcnow().isoformat()
        else:
            # Create new person node
            metadata = PersonNodeMetadata(
                node_id=person_id,
                label=data.get("name", "Unknown"),
                title=data.get("job_title", ""),
                full_name=data.get("name", ""),
                email=data.get("email", ""),
                phone=data.get("phone", ""),
                location=data.get("location", ""),
                company=data.get("company", ""),
                job_title=data.get("job_title", ""),
                bio=data.get("bio", ""),
                linkedin_profile=data.get("linkedin", ""),
                twitter_profile=data.get("twitter", ""),
                facebook_profile=data.get("facebook", ""),
                instagram_profile=data.get("instagram", ""),
                github_profile=data.get("github", ""),
                connections_count=data.get("connections", 0),
                followers_count=data.get("followers", 0),
                source=event.source_agent,
                sources=[event.source_agent],
                agent_maker=event.source_agent,
                confidence=data.get("confidence", 0.7),
            )

        # Create node
        node = GraphNode(node_id=person_id, metadata=metadata)

        # Cache and store
        self.node_cache[person_id] = node
        await self.neo4j_service.add_node(
            node_id=person_id,
            label=metadata.label,
            node_type=NodeType.PERSON.value,
            properties=metadata.model_dump(),
        )

        logger.info(f"Person node created/updated: {person_id}")

        return {
            "status": "success",
            "node_id": person_id,
            "node_type": "person",
            "action": "created" if not existing else "updated",
        }

    async def _handle_company_found(
        self,
        event: IntelligenceEvent,
    ) -> Dict[str, Any]:
        """Handle company found event.

        Args:
            event: Intelligence event

        Returns:
            Processing result
        """
        logger.info("Handling company found event")

        data = event.data
        company_id = f"company_{uuid4().hex[:8]}"

        # Check for duplicates
        existing = await self._find_duplicate_company(data)
        if existing:
            logger.info(f"Found duplicate company: {existing.node_id}")
            company_id = existing.node_id
            metadata = existing.metadata
            metadata.sources.append(event.source_agent)
            metadata.updated_at = datetime.utcnow().isoformat()
        else:
            # Create new company node
            metadata = CompanyNodeMetadata(
                node_id=company_id,
                label=data.get("name", "Unknown"),
                title=data.get("name", ""),
                company_name=data.get("name", ""),
                industry=data.get("industry", ""),
                founded_year=data.get("founded_year", None),
                headquarters=data.get("headquarters", ""),
                website=data.get("website", ""),
                employee_count=data.get("employee_count", None),
                revenue=data.get("revenue", ""),
                linkedin_company=data.get("linkedin", ""),
                facebook_page=data.get("facebook", ""),
                twitter_account=data.get("twitter", ""),
                instagram_account=data.get("instagram", ""),
                source=event.source_agent,
                sources=[event.source_agent],
                agent_maker=event.source_agent,
                confidence=data.get("confidence", 0.7),
            )

        # Create node
        node = GraphNode(node_id=company_id, metadata=metadata)

        # Cache and store
        self.node_cache[company_id] = node
        await self.neo4j_service.add_node(
            node_id=company_id,
            label=metadata.label,
            node_type=NodeType.COMPANY.value,
            properties=metadata.model_dump(),
        )

        logger.info(f"Company node created/updated: {company_id}")

        return {
            "status": "success",
            "node_id": company_id,
            "node_type": "company",
            "action": "created" if not existing else "updated",
        }

    async def _handle_domain_found(
        self,
        event: IntelligenceEvent,
    ) -> Dict[str, Any]:
        """Handle domain found event.

        Args:
            event: Intelligence event

        Returns:
            Processing result
        """
        logger.info("Handling domain found event")

        data = event.data
        domain_name = data.get("domain", "")
        domain_id = f"domain_{domain_name.replace('.', '_')}"

        # Check for duplicates
        existing = await self._find_duplicate_domain(data)
        if existing:
            logger.info(f"Found duplicate domain: {existing.node_id}")
            domain_id = existing.node_id
            metadata = existing.metadata
            metadata.sources.append(event.source_agent)
            metadata.updated_at = datetime.utcnow().isoformat()
        else:
            # Create new domain node
            metadata = DomainNodeMetadata(
                node_id=domain_id,
                label=domain_name,
                title=domain_name,
                domain_name=domain_name,
                registrar=data.get("registrar", ""),
                registration_date=data.get("registration_date", ""),
                expiration_date=data.get("expiration_date", ""),
                registrant=data.get("registrant", ""),
                dns_records=data.get("dns_records", {}),
                mx_records=data.get("mx_records", []),
                ns_records=data.get("ns_records", []),
                ssl_certificate=data.get("ssl_certificate", ""),
                ssl_issuer=data.get("ssl_issuer", ""),
                ssl_expiration=data.get("ssl_expiration", ""),
                website_title=data.get("website_title", ""),
                website_description=data.get("website_description", ""),
                technologies=data.get("technologies", []),
                source=event.source_agent,
                sources=[event.source_agent],
                agent_maker=event.source_agent,
                confidence=data.get("confidence", 0.7),
            )

        # Create node
        node = GraphNode(node_id=domain_id, metadata=metadata)

        # Cache and store
        self.node_cache[domain_id] = node
        await self.neo4j_service.add_node(
            node_id=domain_id,
            label=metadata.label,
            node_type=NodeType.DOMAIN.value,
            properties=metadata.model_dump(),
        )

        logger.info(f"Domain node created/updated: {domain_id}")

        return {
            "status": "success",
            "node_id": domain_id,
            "node_type": "domain",
            "action": "created" if not existing else "updated",
        }

    async def _handle_ip_found(
        self,
        event: IntelligenceEvent,
    ) -> Dict[str, Any]:
        """Handle IP address found event.

        Args:
            event: Intelligence event

        Returns:
            Processing result
        """
        logger.info("Handling IP found event")

        data = event.data
        ip_address = data.get("ip", "")
        ip_id = f"ip_{ip_address.replace('.', '_')}"

        # Check for duplicates
        existing = await self._find_duplicate_ip(data)
        if existing:
            logger.info(f"Found duplicate IP: {existing.node_id}")
            ip_id = existing.node_id
            metadata = existing.metadata
            metadata.sources.append(event.source_agent)
            metadata.updated_at = datetime.utcnow().isoformat()
        else:
            # Create new IP node
            metadata = IPAddressNodeMetadata(
                node_id=ip_id,
                label=ip_address,
                title=ip_address,
                ip_address=ip_address,
                country=data.get("country", ""),
                city=data.get("city", ""),
                isp=data.get("isp", ""),
                asn=data.get("asn", ""),
                open_ports=data.get("open_ports", []),
                services=data.get("services", []),
                technologies=data.get("technologies", []),
                vulnerabilities=data.get("vulnerabilities", []),
                hosting_provider=data.get("hosting_provider", ""),
                is_vpn=data.get("is_vpn", False),
                is_proxy=data.get("is_proxy", False),
                is_datacenter=data.get("is_datacenter", False),
                source=event.source_agent,
                sources=[event.source_agent],
                agent_maker=event.source_agent,
                confidence=data.get("confidence", 0.7),
            )

        # Create node
        node = GraphNode(node_id=ip_id, metadata=metadata)

        # Cache and store
        self.node_cache[ip_id] = node
        await self.neo4j_service.add_node(
            node_id=ip_id,
            label=metadata.label,
            node_type=NodeType.IP_ADDRESS.value,
            properties=metadata.model_dump(),
        )

        logger.info(f"IP node created/updated: {ip_id}")

        return {
            "status": "success",
            "node_id": ip_id,
            "node_type": "ip_address",
            "action": "created" if not existing else "updated",
        }

    async def _handle_relationship_found(
        self,
        event: IntelligenceEvent,
    ) -> Dict[str, Any]:
        """Handle relationship found event.

        Args:
            event: Intelligence event

        Returns:
            Processing result
        """
        logger.info("Handling relationship found event")

        data = event.data
        source_id = data.get("source_id", "")
        target_id = data.get("target_id", "")
        relationship_type = data.get("relationship_type", "related_to")
        edge_id = f"edge_{source_id}_{target_id}_{relationship_type}"

        # Create edge metadata
        metadata = EdgeMetadata(
            edge_id=edge_id,
            source_id=source_id,
            target_id=target_id,
            label=data.get("label", relationship_type),
            relationship_type=RelationType(relationship_type),
            strength=data.get("strength", 0.5),
            confidence=data.get("confidence", 0.7),
            source=event.source_agent,
            sources=[event.source_agent],
            agent_maker=event.source_agent,
            evidence=data.get("evidence", ""),
        )

        # Create edge
        edge = GraphEdge(edge_id=edge_id, metadata=metadata)

        # Cache and store
        self.edge_cache[edge_id] = edge
        await self.neo4j_service.add_relationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=relationship_type,
            properties=metadata.model_dump(),
        )

        logger.info(f"Relationship created: {source_id} -> {target_id}")

        return {
            "status": "success",
            "edge_id": edge_id,
            "source_id": source_id,
            "target_id": target_id,
            "relationship_type": relationship_type,
        }

    async def _find_duplicate_person(
        self,
        data: Dict[str, Any],
    ) -> Optional[GraphNode]:
        """Find duplicate person in cache.

        Args:
            data: Person data

        Returns:
            Existing node or None
        """
        name = data.get("name", "").lower()
        email = data.get("email", "").lower()

        for node in self.node_cache.values():
            if isinstance(node.metadata, PersonNodeMetadata):
                if (node.metadata.full_name and node.metadata.full_name.lower() == name) or (
                    node.metadata.email and node.metadata.email.lower() == email
                ):
                    return node

        return None

    async def _find_duplicate_company(
        self,
        data: Dict[str, Any],
    ) -> Optional[GraphNode]:
        """Find duplicate company in cache.

        Args:
            data: Company data

        Returns:
            Existing node or None
        """
        name = data.get("name", "").lower()

        for node in self.node_cache.values():
            if isinstance(node.metadata, CompanyNodeMetadata):
                if node.metadata.company_name and node.metadata.company_name.lower() == name:
                    return node

        return None

    async def _find_duplicate_domain(
        self,
        data: Dict[str, Any],
    ) -> Optional[GraphNode]:
        """Find duplicate domain in cache.

        Args:
            data: Domain data

        Returns:
            Existing node or None
        """
        domain = data.get("domain", "").lower()

        for node in self.node_cache.values():
            if isinstance(node.metadata, DomainNodeMetadata):
                if node.metadata.domain_name and node.metadata.domain_name.lower() == domain:
                    return node

        return None

    async def _find_duplicate_ip(
        self,
        data: Dict[str, Any],
    ) -> Optional[GraphNode]:
        """Find duplicate IP in cache.

        Args:
            data: IP data

        Returns:
            Existing node or None
        """
        ip = data.get("ip", "")

        for node in self.node_cache.values():
            if isinstance(node.metadata, IPAddressNodeMetadata):
                if node.metadata.ip_address == ip:
                    return node

        return None

    async def _notify_updates(self, result: Dict[str, Any]) -> None:
        """Notify subscribers of graph updates.

        Args:
            result: Update result
        """
        for callback in self.update_callbacks:
            try:
                await callback(result)
            except Exception as e:
                logger.error(f"Callback failed: {e}")

    async def get_graph_snapshot(self) -> Tuple[List[GraphNode], List[GraphEdge]]:
        """Get current graph snapshot.

        Returns:
            Tuple of (nodes, edges)
        """
        nodes = list(self.node_cache.values())
        edges = list(self.edge_cache.values())

        logger.info(f"Graph snapshot: {len(nodes)} nodes, {len(edges)} edges")

        return nodes, edges

    async def get_graphistry_url(self) -> Optional[str]:
        """Get Graphistry visualization URL.

        Returns:
            Graphistry URL or None
        """
        try:
            nodes, edges = await self.get_graph_snapshot()

            if not nodes or not edges:
                logger.warning("No nodes or edges to visualize")
                return None

            g = self.graphistry_service.create_graph(nodes, edges)

            if g:
                url = self.graphistry_service.plot_graph(g)
                logger.info(f"Graphistry URL: {url}")
                return url

            return None

        except Exception as e:
            logger.error(f"Graphistry URL generation failed: {e}")
            return None

    async def close(self) -> None:
        """Close agent resources."""
        logger.info("Closing Graph Builder Agent")
        try:
            await self.neo4j_service.close()
        except Exception as e:
            logger.error(f"Error closing Neo4j service: {e}")
