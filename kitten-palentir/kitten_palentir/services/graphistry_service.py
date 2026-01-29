"""Palentir OSINT - Graphistry Integration Service.

Provides Graphistry visualization for knowledge graphs.
"""

import logging
import os
from typing import Dict, List, Any, Optional, Tuple

import pandas as pd

try:
    import graphistry
    from graphistry import PyGraphistry
    GRAPHISTRY_AVAILABLE = True
except ImportError:
    GRAPHISTRY_AVAILABLE = False

from models.graph_nodes import (
    GraphNode,
    GraphEdge,
    NodeMetadata,
    EdgeMetadata,
    NodeType,
    RelationType,
)


logger = logging.getLogger(__name__)


class GraphistryService:
    """Service for Graphistry visualization integration."""

    def __init__(self):
        """Initialize Graphistry service."""
        self.authenticated = False
        self.config = {}

        if GRAPHISTRY_AVAILABLE:
            self._setup_graphistry()
        else:
            logger.warning("Graphistry not available, install with: pip install graphistry")

    def _setup_graphistry(self) -> None:
        """Setup Graphistry configuration."""
        try:
            # Get credentials from environment
            self.config = {
                "api": 3,
            }

            if "GRAPHISTRY_USERNAME" in os.environ:
                self.config["username"] = os.environ["GRAPHISTRY_USERNAME"]

            if "GRAPHISTRY_PASSWORD" in os.environ:
                self.config["password"] = os.environ["GRAPHISTRY_PASSWORD"]

            if "GRAPHISTRY_TOKEN" in os.environ:
                self.config["token"] = os.environ["GRAPHISTRY_TOKEN"]

            if "GRAPHISTRY_SERVER" in os.environ:
                self.config["server"] = os.environ["GRAPHISTRY_SERVER"]

            if "GRAPHISTRY_PROTOCOL" in os.environ:
                self.config["protocol"] = os.environ["GRAPHISTRY_PROTOCOL"]

            # Set privacy mode
            privacy_mode = os.environ.get("GRAPHISTRY_PRIVACY", "private")
            graphistry.privacy(mode=privacy_mode)

            # Register if credentials available
            if self.config.get("username") or self.config.get("token"):
                graphistry.register(**self.config)
                self.authenticated = PyGraphistry._is_authenticated
                logger.info("Graphistry authenticated")
            else:
                logger.info("Graphistry credentials not provided")

        except Exception as e:
            logger.error(f"Graphistry setup failed: {e}")

    def nodes_to_dataframe(
        self,
        nodes: List[GraphNode],
    ) -> pd.DataFrame:
        """Convert nodes to Graphistry DataFrame.

        Args:
            nodes: List of graph nodes

        Returns:
            DataFrame with node data
        """
        data = []

        for node in nodes:
            node_dict = node.to_dict()
            data.append(node_dict)

        df = pd.DataFrame(data)

        # Ensure required columns
        if "id" not in df.columns:
            df["id"] = df.index.astype(str)
        if "label" not in df.columns:
            df["label"] = df.get("title", "Node")

        logger.info(f"Created nodes DataFrame with {len(df)} rows")
        return df

    def edges_to_dataframe(
        self,
        edges: List[GraphEdge],
    ) -> pd.DataFrame:
        """Convert edges to Graphistry DataFrame.

        Args:
            edges: List of graph edges

        Returns:
            DataFrame with edge data
        """
        data = []

        for edge in edges:
            edge_dict = edge.to_dict()
            data.append(edge_dict)

        df = pd.DataFrame(data)

        # Ensure required columns
        if "id" not in df.columns:
            df["id"] = df.index.astype(str)
        if "label" not in df.columns:
            df["label"] = df.get("relationship_type", "Related")
        if "source" not in df.columns:
            df["source"] = ""
        if "target" not in df.columns:
            df["target"] = ""

        logger.info(f"Created edges DataFrame with {len(df)} rows")
        return df

    def create_graph(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        name: str = "Palentir OSINT Graph",
    ) -> Optional[Any]:
        """Create Graphistry visualization.

        Args:
            nodes: List of nodes
            edges: List of edges
            name: Graph name

        Returns:
            Graphistry graph object or None
        """
        if not GRAPHISTRY_AVAILABLE:
            logger.warning("Graphistry not available")
            return None

        try:
            # Convert to DataFrames
            nodes_df = self.nodes_to_dataframe(nodes)
            edges_df = self.edges_to_dataframe(edges)

            # Create graph
            g = graphistry.edges(
                edges_df,
                "source",
                "target",
            ).nodes(nodes_df, "id").settings(
                url_title=name,
                height=800,
            )

            logger.info(f"Created Graphistry graph: {name}")
            return g

        except Exception as e:
            logger.error(f"Graph creation failed: {e}")
            return None

    def plot_graph(
        self,
        g: Any,
        as_files: bool = True,
    ) -> Optional[str]:
        """Plot Graphistry graph and return URL.

        Args:
            g: Graphistry graph object
            as_files: Whether to render as files

        Returns:
            Graph URL or None
        """
        if not self.authenticated or g is None:
            logger.warning("Cannot plot: Graphistry not authenticated or graph is None")
            return None

        try:
            url = g.plot(as_files=as_files, render=False)
            logger.info(f"Graph plotted: {url}")
            return url

        except Exception as e:
            logger.error(f"Graph plotting failed: {e}")
            return None

    def create_node_view_data(
        self,
        node: GraphNode,
    ) -> Dict[str, Any]:
        """Create data for node detail view.

        Args:
            node: Graph node

        Returns:
            Node view data
        """
        return node.get_display_data()

    def create_edge_view_data(
        self,
        edge: GraphEdge,
    ) -> Dict[str, Any]:
        """Create data for edge detail view.

        Args:
            edge: Graph edge

        Returns:
            Edge view data
        """
        return {
            "id": edge.edge_id,
            "label": edge.metadata.label,
            "relationship_type": edge.metadata.relationship_type.value,
            "source_id": edge.metadata.source_id,
            "target_id": edge.metadata.target_id,
            "strength": edge.metadata.strength,
            "confidence": edge.metadata.confidence,
            "source": edge.metadata.source,
            "evidence": edge.metadata.evidence,
            "agent_maker": edge.metadata.agent_maker,
            "created_at": edge.metadata.created_at,
            "tags": edge.metadata.tags,
        }

    def get_node_icon(self, node_type: NodeType) -> str:
        """Get icon for node type.

        Args:
            node_type: Node type

        Returns:
            Icon name
        """
        icon_map = {
            NodeType.COMPANY: "building",
            NodeType.PERSON: "user",
            NodeType.DOMAIN: "globe",
            NodeType.IP_ADDRESS: "server",
            NodeType.EMAIL: "envelope",
            NodeType.PHONE: "phone",
            NodeType.TECHNOLOGY: "cog",
            NodeType.SOCIAL_PROFILE: "share-alt",
            NodeType.DOCUMENT: "file",
            NodeType.LOCATION: "map-marker",
            NodeType.ORGANIZATION: "sitemap",
            NodeType.EVENT: "calendar",
        }

        return icon_map.get(node_type, "circle")

    def get_node_color(self, node_type: NodeType) -> str:
        """Get color for node type.

        Args:
            node_type: Node type

        Returns:
            Color hex code
        """
        color_map = {
            NodeType.COMPANY: "#FF6B6B",
            NodeType.PERSON: "#4ECDC4",
            NodeType.DOMAIN: "#45B7D1",
            NodeType.IP_ADDRESS: "#FFA07A",
            NodeType.EMAIL: "#98D8C8",
            NodeType.PHONE: "#F7DC6F",
            NodeType.TECHNOLOGY: "#BB8FCE",
            NodeType.SOCIAL_PROFILE: "#85C1E2",
            NodeType.DOCUMENT: "#F8B88B",
            NodeType.LOCATION: "#52C41A",
            NodeType.ORGANIZATION: "#1890FF",
            NodeType.EVENT: "#FF85C0",
        }

        return color_map.get(node_type, "#1f77b4")

    def get_edge_color(self, relationship_type: RelationType) -> str:
        """Get color for relationship type.

        Args:
            relationship_type: Relationship type

        Returns:
            Color hex code
        """
        color_map = {
            RelationType.OWNS: "#FF6B6B",
            RelationType.WORKS_AT: "#4ECDC4",
            RelationType.MANAGES: "#45B7D1",
            RelationType.USES: "#FFA07A",
            RelationType.LOCATED_IN: "#52C41A",
            RelationType.HAS_EMAIL: "#98D8C8",
            RelationType.HAS_PHONE: "#F7DC6F",
            RelationType.HAS_SOCIAL: "#85C1E2",
            RelationType.REFERENCES: "#F8B88B",
            RelationType.RELATED_TO: "#1890FF",
            RelationType.COMMUNICATES: "#FF85C0",
            RelationType.FOUNDED_BY: "#FFD700",
            RelationType.ACQUIRED_BY: "#FF4500",
            RelationType.CONNECTED_TO: "#9370DB",
        }

        return color_map.get(relationship_type, "#999")

    def format_shareable_url(
        self,
        node_id: str,
        node_type: NodeType,
    ) -> str:
        """Format shareable URL for node.

        Args:
            node_id: Node ID
            node_type: Node type

        Returns:
            Shareable URL
        """
        base_url = os.environ.get(
            "PALENTIR_BASE_URL",
            "http://localhost:8501",
        )

        return f"{base_url}/node/{node_type.value}/{node_id}"

    def validate_graph_data(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
    ) -> Tuple[bool, List[str]]:
        """Validate graph data for visualization.

        Args:
            nodes: List of nodes
            edges: List of edges

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check nodes
        if not nodes:
            errors.append("No nodes provided")

        # Check edges
        if not edges:
            errors.append("No edges provided")

        # Check node IDs
        node_ids = {node.node_id for node in nodes}
        for edge in edges:
            if edge.metadata.source_id not in node_ids:
                errors.append(f"Edge source not found: {edge.metadata.source_id}")
            if edge.metadata.target_id not in node_ids:
                errors.append(f"Edge target not found: {edge.metadata.target_id}")

        return len(errors) == 0, errors
