"""Graph-aware agents for OSINT intelligence."""

from typing import List, Dict, Any, Optional
from abc import ABC, abstractmethod


class GraphAwareAgent(ABC):
    """Base class for graph-aware agents."""

    def __init__(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[str] = None,
    ):
        """Initialize the agent."""
        self.name = name or self.__class__.__name__
        self.description = description or f"{self.__class__.__name__} agent"
        self.system_prompt = system_prompt or f"You are a {self.__class__.__name__}."

    async def query_graph(self, query: str) -> List[Dict[str, Any]]:
        """Query the graph."""
        return []

    async def get_node_context(self, node_id: str) -> Dict[str, Any]:
        """Get context for a node."""
        return {}
    
    async def find_missing_connections(self, node_id: str) -> List[Dict[str, Any]]:
        """Find missing connections for a node."""
        return []
    
    async def add_to_graph(
        self,
        node_type: str,
        name: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Add a node to the graph."""
        from uuid import uuid4
        return str(uuid4())
    
    async def create_relationship(
        self,
        source_id: str,
        target_id: str,
        rel_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Create a relationship in the graph."""
        return True


class IntelligenceEnhancerAgent(GraphAwareAgent):
    """Agent that enhances intelligence from graph data."""

    def __init__(self):
        """Initialize IntelligenceEnhancerAgent with defaults."""
        super().__init__(
            name="IntelligenceEnhancerAgent",
            description="Agent that enhances intelligence from graph data",
            system_prompt="You are an intelligence enhancer agent.",
        )
    
    async def analyze_and_enhance(self, node_id: str) -> Dict[str, Any]:
        """Analyze and enhance intelligence for a node."""
        missing = await self.find_missing_connections(node_id)
        suggested_tasks = [
            {"type": conn.get("type"), "description": f"Find {conn.get('type')}"}
            for conn in missing
        ]
        return {
            "node_id": node_id,
            "missing_connections": missing,
            "suggested_tasks": suggested_tasks,
        }


class RelationshipBuilderAgent(GraphAwareAgent):
    """Agent that builds relationships in the graph."""

    def __init__(self):
        """Initialize RelationshipBuilderAgent with defaults."""
        super().__init__(
            name="RelationshipBuilderAgent",
            description="Agent that builds relationships in the graph",
            system_prompt="You are a relationship builder agent.",
        )
    
    async def build_relationships(
        self,
        source_id: str,
        target_ids: List[str],
        rel_type: str,
    ) -> Dict[str, Any]:
        """Build relationships for a node."""
        created = []
        failed = []
        
        for target_id in target_ids:
            success = await self.create_relationship(
                source_id=source_id,
                target_id=target_id,
                rel_type=rel_type,
            )
            if success:
                created.append(target_id)
            else:
                failed.append(target_id)
        
        return {
            "source_id": source_id,
            "created_relationships": created,
            "failed_relationships": failed,
        }


class GraphQueryAgent(GraphAwareAgent):
    """Agent that queries the graph."""

    def __init__(self):
        """Initialize GraphQueryAgent with defaults."""
        super().__init__(
            name="GraphQueryAgent",
            description="Agent that queries the graph for intelligence",
            system_prompt="You are a graph query agent.",
        )
    
    async def search_intelligence(
        self,
        query: str,
        node_types: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Search intelligence in the graph."""
        results = await self.query_graph(query)
        analysis_str = self._analyze_results(results)
        return {
            "query": query,
            "results": results,
            "count": len(results),
            "analysis": {
                "summary": analysis_str,
                "insights": [],
            },
        }
    
    def _analyze_results(self, results: List[Dict[str, Any]]) -> str:
        """Analyze query results (internal method)."""
        if not results:
            return "No results found"
        
        entity_count = len(results)
        entity_types = {}
        for result in results:
            entity_type = result.get("type", "Unknown")
            entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
        
        type_summary = ", ".join([f"{count} {etype}" for etype, count in entity_types.items()])
        return f"Found {entity_count} entities: {type_summary}"
    
    async def analyze_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze query results."""
        entity_count = len(results)
        return {
            "total_results": entity_count,
            "summary": f"Found {entity_count} entities",
            "insights": [],
        }

