"""Palentir OSINT - Real-time Graph Update Component for Streamlit.

Handles real-time updates from Graph Builder Agent to Streamlit UI.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

import streamlit as st
from streamlit_autorefresh import rerun_script

from kitten_palentir.models.graph_nodes import GraphNode, GraphEdge
from kitten_palentir.agents.graph_builder_agent import GraphBuilderAgent, IntelligenceEvent
from kitten_palentir.services.graphistry_service import GraphistryService


logger = logging.getLogger(__name__)


class RealtimeGraphComponent:
    """Real-time graph update component for Streamlit."""

    def __init__(self, graph_builder: GraphBuilderAgent):
        """Initialize real-time component.

        Args:
            graph_builder: Graph Builder Agent instance
        """
        self.graph_builder = graph_builder
        self.graphistry_service = GraphistryService()
        self.update_history: List[Dict[str, Any]] = []
        self.max_history = 100

        # Register update callback
        graph_builder.register_update_callback(self._on_graph_update)

    async def _on_graph_update(self, result: Dict[str, Any]) -> None:
        """Handle graph update from agent.

        Args:
            result: Update result
        """
        logger.info(f"Graph update received: {result}")

        # Add to history
        update_event = {
            "timestamp": datetime.utcnow().isoformat(),
            "result": result,
            "status": result.get("status", "unknown"),
        }

        self.update_history.append(update_event)

        # Keep history size manageable
        if len(self.update_history) > self.max_history:
            self.update_history.pop(0)

    def render_update_feed(self) -> None:
        """Render update feed in Streamlit."""
        st.subheader("📡 Real-time Updates")

        if not self.update_history:
            st.info("No updates yet")
            return

        # Display recent updates
        for event in reversed(self.update_history[-10:]):
            with st.container():
                col1, col2, col3 = st.columns([1, 3, 1])

                with col1:
                    timestamp = event["timestamp"][:19]
                    st.caption(timestamp)

                with col2:
                    result = event["result"]
                    status = event["status"]

                    if status == "success":
                        st.success(
                            f"✓ {result.get('node_type', 'unknown')} "
                            f"({result.get('action', 'created')})"
                        )
                    else:
                        st.error(f"✗ {status}")

                    st.caption(f"ID: {result.get('node_id', result.get('edge_id', 'N/A'))}")

                with col3:
                    if result.get("status") == "success":
                        st.markdown("✓")

                st.divider()

    def render_graph_statistics(self) -> None:
        """Render graph statistics."""
        st.subheader("📊 Graph Statistics")

        col1, col2, col3, col4 = st.columns(4)

        # Get current graph
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        nodes, edges = loop.run_until_complete(
            self.graph_builder.get_graph_snapshot()
        )

        with col1:
            st.metric("Total Nodes", len(nodes))

        with col2:
            st.metric("Total Edges", len(edges))

        with col3:
            # Count by type
            node_types = {}
            for node in nodes:
                nt = node.metadata.node_type.value
                node_types[nt] = node_types.get(nt, 0) + 1

            st.metric("Node Types", len(node_types))

        with col4:
            # Average confidence
            avg_conf = (
                sum(n.metadata.confidence for n in nodes) / len(nodes)
                if nodes
                else 0
            )
            st.metric("Avg Confidence", f"{avg_conf:.2f}")

        # Node type breakdown
        if node_types:
            st.write("**Node Type Breakdown:**")
            for nt, count in sorted(node_types.items()):
                st.write(f"- {nt}: {count}")

    def render_graph_visualization(self) -> None:
        """Render graph visualization."""
        st.subheader("📈 Knowledge Graph Visualization")

        # Get current graph
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        nodes, edges = loop.run_until_complete(
            self.graph_builder.get_graph_snapshot()
        )

        if not nodes:
            st.info("No nodes to visualize yet")
            return

        # Validate data
        is_valid, errors = self.graphistry_service.validate_graph_data(nodes, edges)

        if not is_valid:
            st.error("Graph validation failed:")
            for error in errors:
                st.write(f"- {error}")
            return

        # Create graph
        try:
            g = self.graphistry_service.create_graph(nodes, edges)

            if g and self.graphistry_service.authenticated:
                url = self.graphistry_service.plot_graph(g)

                if url:
                    st.markdown(f"[🔗 View Full Graph]({url})")
                else:
                    st.warning("Could not generate Graphistry URL")
            else:
                st.info("Graphistry not authenticated or graph creation failed")

        except Exception as e:
            logger.error(f"Graph visualization failed: {e}")
            st.error(f"Graph visualization failed: {e}")

    def render_node_browser(self) -> None:
        """Render node browser."""
        st.subheader("🔍 Node Browser")

        # Get current graph
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        nodes, edges = loop.run_until_complete(
            self.graph_builder.get_graph_snapshot()
        )

        if not nodes:
            st.info("No nodes to browse")
            return

        # Filter options
        col1, col2, col3 = st.columns(3)

        with col1:
            node_types = list(set(n.metadata.node_type.value for n in nodes))
            selected_type = st.selectbox("Filter by Type", ["All"] + node_types)

        with col2:
            min_confidence = st.slider("Minimum Confidence", 0.0, 1.0, 0.0)

        with col3:
            search_term = st.text_input("Search", "")

        # Filter nodes
        filtered_nodes = nodes

        if selected_type != "All":
            filtered_nodes = [
                n for n in filtered_nodes
                if n.metadata.node_type.value == selected_type
            ]

        filtered_nodes = [
            n for n in filtered_nodes
            if n.metadata.confidence >= min_confidence
        ]

        if search_term:
            search_lower = search_term.lower()
            filtered_nodes = [
                n for n in filtered_nodes
                if search_lower in n.metadata.label.lower()
                or search_lower in str(n.metadata.properties).lower()
            ]

        # Display nodes
        st.write(f"**Found {len(filtered_nodes)} nodes**")

        for node in filtered_nodes[:20]:  # Show first 20
            with st.expander(f"{node.metadata.label} ({node.metadata.node_type.value})"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**ID:** {node.node_id}")
                    st.write(f"**Type:** {node.metadata.node_type.value}")
                    st.write(f"**Confidence:** {node.metadata.confidence:.2f}")

                with col2:
                    st.write(f"**Source:** {node.metadata.source}")
                    st.write(f"**Agent:** {node.metadata.agent_maker}")
                    st.write(f"**Created:** {node.metadata.created_at[:10]}")

                # Display metadata
                if node.metadata.properties:
                    st.write("**Properties:**")
                    st.json(node.metadata.properties)

    def render_relationship_browser(self) -> None:
        """Render relationship browser."""
        st.subheader("🔗 Relationship Browser")

        # Get current graph
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        nodes, edges = loop.run_until_complete(
            self.graph_builder.get_graph_snapshot()
        )

        if not edges:
            st.info("No relationships to browse")
            return

        # Display relationships
        st.write(f"**Found {len(edges)} relationships**")

        for edge in edges[:20]:  # Show first 20
            with st.expander(
                f"{edge.metadata.source_id} → {edge.metadata.label} → "
                f"{edge.metadata.target_id}"
            ):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Relationship Type:** {edge.metadata.relationship_type.value}")
                    st.write(f"**Strength:** {edge.metadata.strength:.2f}")
                    st.write(f"**Confidence:** {edge.metadata.confidence:.2f}")

                with col2:
                    st.write(f"**Source:** {edge.metadata.source}")
                    st.write(f"**Agent:** {edge.metadata.agent_maker}")
                    st.write(f"**Created:** {edge.metadata.created_at[:10]}")

                if edge.metadata.evidence:
                    st.write(f"**Evidence:** {edge.metadata.evidence}")

    def render_export_options(self) -> None:
        """Render export options."""
        st.subheader("📥 Export Options")

        col1, col2, col3 = st.columns(3)

        # Get current graph
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        nodes, edges = loop.run_until_complete(
            self.graph_builder.get_graph_snapshot()
        )

        with col1:
            if st.button("📊 Export as JSON"):
                export_data = {
                    "nodes": [n.to_dict() for n in nodes],
                    "edges": [e.to_dict() for e in edges],
                    "timestamp": datetime.utcnow().isoformat(),
                }

                st.json(export_data)

        with col2:
            if st.button("📈 Export as CSV"):
                import pandas as pd

                nodes_df = pd.DataFrame([n.to_dict() for n in nodes])
                edges_df = pd.DataFrame([e.to_dict() for e in edges])

                st.write("**Nodes:**")
                st.dataframe(nodes_df)

                st.write("**Edges:**")
                st.dataframe(edges_df)

        with col3:
            if st.button("🔗 Get Graphistry URL"):
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                url = loop.run_until_complete(
                    self.graph_builder.get_graphistry_url()
                )

                if url:
                    st.success(f"[View Graph]({url})")
                else:
                    st.error("Could not generate Graphistry URL")

    def run(self) -> None:
        """Run the real-time component."""
        # Auto-refresh every 5 seconds
        st.set_page_config(
            page_title="Palentir OSINT - Real-time Graph",
            page_icon="🕸️",
            layout="wide",
        )

        st.title("🕸️ Palentir OSINT - Real-time Graph Builder")

        # Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📡 Updates",
            "📊 Statistics",
            "📈 Visualization",
            "🔍 Browse",
            "📥 Export",
        ])

        with tab1:
            self.render_update_feed()

        with tab2:
            self.render_graph_statistics()

        with tab3:
            self.render_graph_visualization()

        with tab4:
            col1, col2 = st.columns(2)

            with col1:
                self.render_node_browser()

            with col2:
                self.render_relationship_browser()

        with tab5:
            self.render_export_options()

        # Auto-refresh
        st.markdown("---")
        st.caption("Auto-refreshing every 5 seconds...")


async def main():
    """Main entry point."""
    from kitten_palentir.config.settings import get_settings

    settings = get_settings()

    # Initialize Graph Builder Agent
    graph_builder = GraphBuilderAgent(
        neo4j_url=settings.neo4j_uri,
        neo4j_user=settings.neo4j_username,
        neo4j_password=settings.neo4j_password,
    )

    # Create component
    component = RealtimeGraphComponent(graph_builder)

    # Run
    component.run()


if __name__ == "__main__":
    asyncio.run(main())
