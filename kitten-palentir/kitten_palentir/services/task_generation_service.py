"""Palentir OSINT - Task Generation Service.

Generates tasks for agents based on user queries and current graph state.
"""

import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
from uuid import uuid4

from camel.tasks import Task


logger = logging.getLogger(__name__)


class TaskPriority(str, Enum):
    """Task priority levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskType(str, Enum):
    """Task types."""

    RECONNAISSANCE = "reconnaissance"
    DOMAIN_ANALYSIS = "domain_analysis"
    PERSON_SEARCH = "person_search"
    COMPANY_RESEARCH = "company_research"
    NETWORK_ANALYSIS = "network_analysis"
    RELATIONSHIP_BUILDING = "relationship_building"
    BREACH_RESEARCH = "breach_research"
    GRAPH_ENRICHMENT = "graph_enrichment"


class PalentirTask:
    """Palentir task model."""

    def __init__(
        self,
        task_id: str,
        task_type: TaskType,
        title: str,
        description: str,
        priority: TaskPriority,
        assigned_agents: List[str],
        parameters: Dict[str, Any],
        parent_task_id: Optional[str] = None,
        dependencies: Optional[List[str]] = None,
    ):
        """Initialize task.

        Args:
            task_id: Task ID
            task_type: Task type
            title: Task title
            description: Task description
            priority: Task priority
            assigned_agents: List of agent names
            parameters: Task parameters
            parent_task_id: Parent task ID if subtask
            dependencies: List of dependent task IDs
        """
        self.task_id = task_id
        self.task_type = task_type
        self.title = title
        self.description = description
        self.priority = priority
        self.assigned_agents = assigned_agents
        self.parameters = parameters
        self.parent_task_id = parent_task_id
        self.dependencies = dependencies or []
        self.created_at = datetime.utcnow().isoformat()
        self.status = "pending"
        self.results = {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type.value,
            "title": self.title,
            "description": self.description,
            "priority": self.priority.value,
            "assigned_agents": self.assigned_agents,
            "parameters": self.parameters,
            "parent_task_id": self.parent_task_id,
            "dependencies": self.dependencies,
            "created_at": self.created_at,
            "status": self.status,
            "results": self.results,
        }


class TaskGenerationService:
    """Service for generating tasks based on queries and graph state."""

    def __init__(self):
        """Initialize task generation service."""
        self.task_templates = self._init_templates()

    def _init_templates(self) -> Dict[TaskType, Dict[str, Any]]:
        """Initialize task templates."""
        return {
            TaskType.RECONNAISSANCE: {
                "title": "Company Reconnaissance",
                "agents": [
                    "SocialMediaIntelligenceAgent",
                    "CompanyIntelligenceAgent",
                    "DomainAnalysisAgent",
                ],
                "subtasks": [
                    "find_company_info",
                    "find_employees",
                    "find_domains",
                    "find_social_profiles",
                ],
            },
            TaskType.DOMAIN_ANALYSIS: {
                "title": "Domain Analysis",
                "agents": [
                    "DomainAnalysisAgent",
                    "NetworkAnalyzerAgent",
                ],
                "subtasks": [
                    "dns_lookup",
                    "whois_lookup",
                    "ssl_analysis",
                    "technology_stack",
                    "ip_enumeration",
                ],
            },
            TaskType.PERSON_SEARCH: {
                "title": "Person Intelligence",
                "agents": [
                    "SocialMediaIntelligenceAgent",
                    "RelationshipBuilderAgent",
                ],
                "subtasks": [
                    "find_social_profiles",
                    "find_connections",
                    "find_work_history",
                    "find_publications",
                ],
            },
            TaskType.COMPANY_RESEARCH: {
                "title": "Company Research",
                "agents": [
                    "CompanyIntelligenceAgent",
                    "SocialMediaIntelligenceAgent",
                ],
                "subtasks": [
                    "company_info",
                    "leadership_team",
                    "employees",
                    "financial_info",
                    "news",
                ],
            },
            TaskType.NETWORK_ANALYSIS: {
                "title": "Network Analysis",
                "agents": [
                    "NetworkAnalyzerAgent",
                ],
                "subtasks": [
                    "port_scan",
                    "service_detection",
                    "vulnerability_scan",
                    "technology_detection",
                ],
            },
            TaskType.RELATIONSHIP_BUILDING: {
                "title": "Relationship Building",
                "agents": [
                    "RelationshipBuilderAgent",
                    "GraphBuilderAgent",
                ],
                "subtasks": [
                    "find_connections",
                    "build_relationships",
                    "detect_patterns",
                    "graph_enrichment",
                ],
            },
            TaskType.BREACH_RESEARCH: {
                "title": "Breach Research",
                "agents": [
                    "BreachIntelligenceAgent",
                ],
                "subtasks": [
                    "search_breaches",
                    "find_leaked_data",
                    "analyze_exposure",
                    "timeline_analysis",
                ],
            },
            TaskType.GRAPH_ENRICHMENT: {
                "title": "Graph Enrichment",
                "agents": [
                    "GraphBuilderAgent",
                    "MemoryAgent",
                ],
                "subtasks": [
                    "fill_gaps",
                    "verify_data",
                    "update_confidence",
                    "add_context",
                ],
            },
        }

    def generate_tasks_from_query(
        self,
        user_query: str,
        current_graph: Optional[Dict[str, Any]] = None,
    ) -> List[PalentirTask]:
        """Generate tasks from user query.

        Args:
            user_query: User query
            current_graph: Current graph state

        Returns:
            List of generated tasks
        """
        logger.info(f"Generating tasks from query: {user_query}")

        tasks = []
        query_lower = user_query.lower()

        # Detect query intent
        if any(keyword in query_lower for keyword in ["company", "organization", "corp"]):
            tasks.extend(self._generate_company_tasks(user_query))

        if any(keyword in query_lower for keyword in ["person", "people", "user", "employee"]):
            tasks.extend(self._generate_person_tasks(user_query))

        if any(keyword in query_lower for keyword in ["domain", "website", "site"]):
            tasks.extend(self._generate_domain_tasks(user_query))

        if any(keyword in query_lower for keyword in ["network", "ip", "server", "infrastructure"]):
            tasks.extend(self._generate_network_tasks(user_query))

        if any(keyword in query_lower for keyword in ["breach", "leak", "exposed", "compromised"]):
            tasks.extend(self._generate_breach_tasks(user_query))

        if any(keyword in query_lower for keyword in ["relationship", "connection", "link"]):
            tasks.extend(self._generate_relationship_tasks(user_query))

        # Prioritize tasks based on graph state
        if current_graph:
            tasks = self._prioritize_tasks(tasks, current_graph)

        logger.info(f"Generated {len(tasks)} tasks")
        return tasks

    def _generate_company_tasks(self, query: str) -> List[PalentirTask]:
        """Generate company research tasks."""
        logger.info(f"Generating company tasks for: {query}")

        tasks = []

        # Extract company name
        company_name = self._extract_entity(query, "company")

        if company_name:
            # Main reconnaissance task
            main_task = PalentirTask(
                task_id=f"task_{uuid4().hex[:8]}",
                task_type=TaskType.RECONNAISSANCE,
                title=f"Reconnaissance: {company_name}",
                description=f"Comprehensive reconnaissance of {company_name}",
                priority=TaskPriority.HIGH,
                assigned_agents=[
                    "SocialMediaIntelligenceAgent",
                    "CompanyIntelligenceAgent",
                    "DomainAnalysisAgent",
                ],
                parameters={
                    "company_name": company_name,
                    "depth": "comprehensive",
                },
            )
            tasks.append(main_task)

            # Domain analysis subtask
            domain_task = PalentirTask(
                task_id=f"task_{uuid4().hex[:8]}",
                task_type=TaskType.DOMAIN_ANALYSIS,
                title=f"Domain Analysis: {company_name}",
                description=f"Analyze domains associated with {company_name}",
                priority=TaskPriority.MEDIUM,
                assigned_agents=["DomainAnalysisAgent", "NetworkAnalyzerAgent"],
                parameters={
                    "company_name": company_name,
                },
                parent_task_id=main_task.task_id,
                dependencies=[main_task.task_id],
            )
            tasks.append(domain_task)

            # Network analysis subtask
            network_task = PalentirTask(
                task_id=f"task_{uuid4().hex[:8]}",
                task_type=TaskType.NETWORK_ANALYSIS,
                title=f"Network Analysis: {company_name}",
                description=f"Analyze network infrastructure of {company_name}",
                priority=TaskPriority.MEDIUM,
                assigned_agents=["NetworkAnalyzerAgent"],
                parameters={
                    "company_name": company_name,
                },
                parent_task_id=main_task.task_id,
                dependencies=[domain_task.task_id],
            )
            tasks.append(network_task)

        return tasks

    def _generate_person_tasks(self, query: str) -> List[PalentirTask]:
        """Generate person search tasks."""
        logger.info(f"Generating person tasks for: {query}")

        tasks = []

        # Extract person name
        person_name = self._extract_entity(query, "person")

        if person_name:
            # Main person search task
            main_task = PalentirTask(
                task_id=f"task_{uuid4().hex[:8]}",
                task_type=TaskType.PERSON_SEARCH,
                title=f"Person Search: {person_name}",
                description=f"Search for {person_name} across all platforms",
                priority=TaskPriority.HIGH,
                assigned_agents=["SocialMediaIntelligenceAgent"],
                parameters={
                    "person_name": person_name,
                    "depth": "comprehensive",
                },
            )
            tasks.append(main_task)

            # Relationship building task
            relationship_task = PalentirTask(
                task_id=f"task_{uuid4().hex[:8]}",
                task_type=TaskType.RELATIONSHIP_BUILDING,
                title=f"Relationship Building: {person_name}",
                description=f"Build relationship graph for {person_name}",
                priority=TaskPriority.MEDIUM,
                assigned_agents=["RelationshipBuilderAgent"],
                parameters={
                    "person_name": person_name,
                },
                parent_task_id=main_task.task_id,
                dependencies=[main_task.task_id],
            )
            tasks.append(relationship_task)

        return tasks

    def _generate_domain_tasks(self, query: str) -> List[PalentirTask]:
        """Generate domain analysis tasks."""
        logger.info(f"Generating domain tasks for: {query}")

        tasks = []

        # Extract domain
        domain = self._extract_entity(query, "domain")

        if domain:
            # Main domain analysis task
            main_task = PalentirTask(
                task_id=f"task_{uuid4().hex[:8]}",
                task_type=TaskType.DOMAIN_ANALYSIS,
                title=f"Domain Analysis: {domain}",
                description=f"Comprehensive analysis of {domain}",
                priority=TaskPriority.HIGH,
                assigned_agents=["DomainAnalysisAgent"],
                parameters={
                    "domain": domain,
                    "depth": "comprehensive",
                },
            )
            tasks.append(main_task)

            # Network analysis task
            network_task = PalentirTask(
                task_id=f"task_{uuid4().hex[:8]}",
                task_type=TaskType.NETWORK_ANALYSIS,
                title=f"Network Analysis: {domain}",
                description=f"Analyze network infrastructure for {domain}",
                priority=TaskPriority.MEDIUM,
                assigned_agents=["NetworkAnalyzerAgent"],
                parameters={
                    "domain": domain,
                },
                parent_task_id=main_task.task_id,
                dependencies=[main_task.task_id],
            )
            tasks.append(network_task)

        return tasks

    def _generate_network_tasks(self, query: str) -> List[PalentirTask]:
        """Generate network analysis tasks."""
        logger.info(f"Generating network tasks for: {query}")

        tasks = []

        # Extract IP or network
        ip_or_network = self._extract_entity(query, "network")

        if ip_or_network:
            # Main network analysis task
            main_task = PalentirTask(
                task_id=f"task_{uuid4().hex[:8]}",
                task_type=TaskType.NETWORK_ANALYSIS,
                title=f"Network Analysis: {ip_or_network}",
                description=f"Analyze network: {ip_or_network}",
                priority=TaskPriority.HIGH,
                assigned_agents=["NetworkAnalyzerAgent"],
                parameters={
                    "target": ip_or_network,
                    "depth": "comprehensive",
                },
            )
            tasks.append(main_task)

        return tasks

    def _generate_breach_tasks(self, query: str) -> List[PalentirTask]:
        """Generate breach research tasks."""
        logger.info(f"Generating breach tasks for: {query}")

        tasks = []

        # Extract email or domain
        target = self._extract_entity(query, "breach")

        if target:
            # Main breach research task
            main_task = PalentirTask(
                task_id=f"task_{uuid4().hex[:8]}",
                task_type=TaskType.BREACH_RESEARCH,
                title=f"Breach Research: {target}",
                description=f"Research breaches for {target}",
                priority=TaskPriority.HIGH,
                assigned_agents=["BreachIntelligenceAgent"],
                parameters={
                    "target": target,
                },
            )
            tasks.append(main_task)

        return tasks

    def _generate_relationship_tasks(self, query: str) -> List[PalentirTask]:
        """Generate relationship building tasks."""
        logger.info(f"Generating relationship tasks for: {query}")

        tasks = []

        # Relationship building task
        main_task = PalentirTask(
            task_id=f"task_{uuid4().hex[:8]}",
            task_type=TaskType.RELATIONSHIP_BUILDING,
            title="Relationship Building",
            description="Build and enhance relationship graph",
            priority=TaskPriority.MEDIUM,
            assigned_agents=["RelationshipBuilderAgent", "GraphBuilderAgent"],
            parameters={
                "query": query,
            },
        )
        tasks.append(main_task)

        return tasks

    def _prioritize_tasks(
        self,
        tasks: List[PalentirTask],
        current_graph: Dict[str, Any],
    ) -> List[PalentirTask]:
        """Prioritize tasks based on graph state.

        Args:
            tasks: List of tasks
            current_graph: Current graph state

        Returns:
            Prioritized tasks
        """
        logger.info("Prioritizing tasks based on graph state")

        # Get graph statistics
        node_count = current_graph.get("node_count", 0)
        edge_count = current_graph.get("edge_count", 0)
        avg_confidence = current_graph.get("avg_confidence", 0.5)

        # Adjust priorities
        for task in tasks:
            if node_count < 10:
                # Few nodes, prioritize reconnaissance
                if task.task_type == TaskType.RECONNAISSANCE:
                    task.priority = TaskPriority.CRITICAL
            elif node_count > 100 and edge_count < 50:
                # Many nodes but few edges, prioritize relationships
                if task.task_type == TaskType.RELATIONSHIP_BUILDING:
                    task.priority = TaskPriority.CRITICAL
            elif avg_confidence < 0.7:
                # Low confidence, prioritize verification
                if task.task_type == TaskType.GRAPH_ENRICHMENT:
                    task.priority = TaskPriority.HIGH

        # Sort by priority
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3,
        }

        tasks.sort(key=lambda t: priority_order[t.priority])

        return tasks

    def _extract_entity(self, query: str, entity_type: str) -> Optional[str]:
        """Extract entity from query.

        Args:
            query: Query string
            entity_type: Entity type

        Returns:
            Extracted entity or None
        """
        # Simple extraction logic
        # In production, use NLP/NER

        if entity_type == "company":
            # Look for company keywords
            keywords = ["company", "corporation", "corp", "inc", "ltd", "llc"]
            for keyword in keywords:
                if keyword in query.lower():
                    # Extract next word or quoted string
                    parts = query.split()
                    for i, part in enumerate(parts):
                        if keyword in part.lower() and i + 1 < len(parts):
                            return parts[i + 1].strip('"\',')

        elif entity_type == "person":
            # Look for person keywords
            keywords = ["person", "people", "user", "employee", "named"]
            for keyword in keywords:
                if keyword in query.lower():
                    parts = query.split()
                    for i, part in enumerate(parts):
                        if keyword in part.lower() and i + 1 < len(parts):
                            return parts[i + 1].strip('"\',')

        elif entity_type == "domain":
            # Look for domain patterns
            import re

            domain_pattern = r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}"
            matches = re.findall(domain_pattern, query)
            if matches:
                return matches[0]

        elif entity_type == "network":
            # Look for IP patterns
            import re

            ip_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"
            matches = re.findall(ip_pattern, query)
            if matches:
                return matches[0]

        elif entity_type == "breach":
            # Look for breach keywords
            keywords = ["breach", "leak", "exposed", "compromised"]
            for keyword in keywords:
                if keyword in query.lower():
                    parts = query.split()
                    for i, part in enumerate(parts):
                        if keyword in part.lower() and i + 1 < len(parts):
                            return parts[i + 1].strip('"\',')

        return None
