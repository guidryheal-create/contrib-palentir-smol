"""Palentir OSINT - Streamlit UI with Graphistry Graph Visualization.

Modern graph visualization with node detail views.
"""

import logging
import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    import graphistry
    GRAPHISTRY_AVAILABLE = True
except ImportError:
    GRAPHISTRY_AVAILABLE = False

from kitten_palentir.models.graph_nodes import (
    GraphNode,
    GraphEdge,
    NodeType,
    PersonNodeMetadata,
    CompanyNodeMetadata,
    IPAddressNodeMetadata,
    DomainNodeMetadata,
)
from kitten_palentir.services.graphistry_service import GraphistryService


logger = logging.getLogger(__name__)


class StreamlitGraphUI:
    """Streamlit UI for graph visualization and exploration."""

    def __init__(self):
        """Initialize Streamlit UI."""
        self.graphistry_service = GraphistryService()
        self._setup_page()

    def _setup_page(self) -> None:
        """Setup Streamlit page configuration."""
        st.set_page_config(
            page_title="Palentir OSINT - Graph Explorer",
            page_icon="🕸️",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        st.markdown("""
            <style>
            .main {
                padding-top: 2rem;
            }
            .metric-card {
                background-color: #f0f2f6;
                padding: 1rem;
                border-radius: 0.5rem;
                margin: 0.5rem 0;
            }
            </style>
        """, unsafe_allow_html=True)

    def render_header(self) -> None:
        """Render page header."""
        col1, col2, col3 = st.columns([1, 2, 1])

        with col1:
            st.image("🕸️", width=50)

        with col2:
            st.title("🕸️ Palentir OSINT - Graph Explorer")
            st.markdown("*Advanced OSINT Intelligence Platform with Knowledge Graph*")

        with col3:
            if st.button("🔄 Refresh"):
                st.rerun()

    def render_sidebar(self) -> Dict[str, Any]:
        """Render sidebar controls.

        Returns:
            Sidebar options
        """
        with st.sidebar:
            st.header("⚙️ Controls")

            options = {
                "view_mode": st.radio(
                    "View Mode",
                    ["Graph", "Table", "Details"],
                    index=0,
                ),
                "filter_type": st.multiselect(
                    "Filter by Node Type",
                    [nt.value for nt in NodeType],
                    default=[],
                ),
                "min_confidence": st.slider(
                    "Minimum Confidence",
                    0.0,
                    1.0,
                    0.5,
                ),
                "show_labels": st.checkbox("Show Labels", value=True),
                "show_metadata": st.checkbox("Show Metadata", value=True),
            }

            st.divider()

            st.header("📊 Statistics")
            if "nodes" in st.session_state:
                st.metric("Nodes", len(st.session_state.nodes))
            if "edges" in st.session_state:
                st.metric("Edges", len(st.session_state.edges))

            return options

    def render_graph_view(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        options: Dict[str, Any],
    ) -> None:
        """Render graph visualization.

        Args:
            nodes: List of nodes
            edges: List of edges
            options: View options
        """
        st.subheader("📈 Knowledge Graph")

        # Filter nodes
        filtered_nodes = nodes
        if options["filter_type"]:
            filtered_nodes = [
                n for n in nodes
                if n.metadata.node_type.value in options["filter_type"]
            ]

        # Filter by confidence
        filtered_nodes = [
            n for n in filtered_nodes
            if n.metadata.confidence >= options["min_confidence"]
        ]

        # Filter edges
        filtered_edge_ids = {
            edge.metadata.source_id
            for edge in edges
            if edge.metadata.source_id in {n.node_id for n in filtered_nodes}
        }
        filtered_edges = [
            e for e in edges
            if e.metadata.source_id in filtered_edge_ids
            and e.metadata.target_id in {n.node_id for n in filtered_nodes}
        ]

        if not filtered_nodes:
            st.warning("No nodes to display")
            return

        # Create Graphistry visualization
        if GRAPHISTRY_AVAILABLE and self.graphistry_service.authenticated:
            try:
                g = self.graphistry_service.create_graph(
                    filtered_nodes,
                    filtered_edges,
                    name="Palentir OSINT Knowledge Graph",
                )

                if g:
                    url = self.graphistry_service.plot_graph(g)
                    if url:
                        st.markdown(f"[View Full Graph]({url})")
                        st.info(
                            "Graph visualization requires Graphistry authentication. "
                            "Configure credentials in .env"
                        )

            except Exception as e:
                logger.error(f"Graph rendering failed: {e}")
                st.error(f"Graph rendering failed: {e}")

        # Display graph statistics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Nodes", len(filtered_nodes))

        with col2:
            st.metric("Total Edges", len(filtered_edges))

        with col3:
            avg_confidence = (
                sum(n.metadata.confidence for n in filtered_nodes) / len(filtered_nodes)
                if filtered_nodes
                else 0
            )
            st.metric("Avg Confidence", f"{avg_confidence:.2f}")

        with col4:
            node_types = {}
            for node in filtered_nodes:
                nt = node.metadata.node_type.value
                node_types[nt] = node_types.get(nt, 0) + 1
            st.metric("Node Types", len(node_types))

    def render_table_view(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        options: Dict[str, Any],
    ) -> None:
        """Render table view.

        Args:
            nodes: List of nodes
            edges: List of edges
            options: View options
        """
        st.subheader("📋 Nodes Table")

        # Prepare data
        data = []
        for node in nodes:
            if options["filter_type"] and node.metadata.node_type.value not in options["filter_type"]:
                continue
            if node.metadata.confidence < options["min_confidence"]:
                continue

            data.append({
                "ID": node.node_id,
                "Label": node.metadata.label,
                "Type": node.metadata.node_type.value,
                "Confidence": f"{node.metadata.confidence:.2f}",
                "Source": node.metadata.source,
                "Agent": node.metadata.agent_maker or "Unknown",
                "Created": node.metadata.created_at[:10],
            })

        if data:
            st.dataframe(data, use_container_width=True)
        else:
            st.info("No nodes to display")

        st.subheader("📊 Edges Table")

        # Prepare edge data
        edge_data = []
        for edge in edges:
            edge_data.append({
                "Source": edge.metadata.source_id,
                "Target": edge.metadata.target_id,
                "Relationship": edge.metadata.label,
                "Strength": f"{edge.metadata.strength:.2f}",
                "Confidence": f"{edge.metadata.confidence:.2f}",
                "Source System": edge.metadata.source,
            })

        if edge_data:
            st.dataframe(edge_data, use_container_width=True)
        else:
            st.info("No edges to display")

    def render_node_detail_view(self, node: GraphNode) -> None:
        """Render detailed node view.

        Args:
            node: Graph node
        """
        metadata = node.metadata
        view_data = node.get_display_data()

        # Header
        col1, col2, col3 = st.columns([1, 3, 1])

        with col1:
            icon = self.graphistry_service.get_node_icon(metadata.node_type)
            st.markdown(f"### {icon} {metadata.label}")

        with col3:
            if metadata.shareable_url:
                st.markdown(f"[🔗 Share]({metadata.shareable_url})")

        # Basic info
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Type", metadata.node_type.value)

        with col2:
            st.metric("Confidence", f"{metadata.confidence:.2f}")

        with col3:
            st.metric("Source", metadata.source)

        st.divider()

        # Type-specific views
        if isinstance(metadata, PersonNodeMetadata):
            self._render_person_view(view_data)
        elif isinstance(metadata, CompanyNodeMetadata):
            self._render_company_view(view_data)
        elif isinstance(metadata, IPAddressNodeMetadata):
            self._render_ip_view(view_data)
        elif isinstance(metadata, DomainNodeMetadata):
            self._render_domain_view(view_data)
        else:
            self._render_generic_view(view_data)

        # Common sections
        st.subheader("📝 Metadata")
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Created:** {metadata.created_at}")
            st.write(f"**Updated:** {metadata.updated_at}")
            st.write(f"**Agent:** {metadata.agent_maker or 'Unknown'}")

        with col2:
            st.write(f"**Sources:** {', '.join(metadata.sources) if metadata.sources else 'Unknown'}")
            st.write(f"**Tags:** {', '.join(metadata.tags) if metadata.tags else 'None'}")

        if metadata.notes:
            st.subheader("📌 Notes")
            st.write(metadata.notes)

    def _render_person_view(self, data: Dict[str, Any]) -> None:
        """Render person node view."""
        st.subheader("👤 Person Information")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Full Name:** {data.get('full_name', 'N/A')}")
            st.write(f"**Email:** {data.get('email', 'N/A')}")
            st.write(f"**Phone:** {data.get('phone', 'N/A')}")
            st.write(f"**Location:** {data.get('location', 'N/A')}")

        with col2:
            st.write(f"**Company:** {data.get('company', 'N/A')}")
            st.write(f"**Job Title:** {data.get('job_title', 'N/A')}")
            st.write(f"**Connections:** {data.get('connections', 0)}")
            st.write(f"**Followers:** {data.get('followers', 0)}")

        # Social profiles
        st.subheader("🌐 Social Profiles")

        col1, col2, col3 = st.columns(3)

        if data.get("linkedin"):
            with col1:
                st.markdown(f"[LinkedIn]({data['linkedin']})")

        if data.get("twitter"):
            with col2:
                st.markdown(f"[Twitter]({data['twitter']})")

        if data.get("github"):
            with col3:
                st.markdown(f"[GitHub]({data['github']})")

    def _render_company_view(self, data: Dict[str, Any]) -> None:
        """Render company node view."""
        st.subheader("🏢 Company Information")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Company Name:** {data.get('company_name', 'N/A')}")
            st.write(f"**Industry:** {data.get('industry', 'N/A')}")
            st.write(f"**Founded:** {data.get('founded_year', 'N/A')}")
            st.write(f"**Headquarters:** {data.get('headquarters', 'N/A')}")

        with col2:
            st.write(f"**Website:** {data.get('website', 'N/A')}")
            st.write(f"**Employees:** {data.get('employee_count', 'N/A')}")
            st.write(f"**Revenue:** {data.get('revenue', 'N/A')}")

        # Discovery metrics
        st.subheader("📊 Discovery Metrics")

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Employees Discovered", data.get("employees_discovered", 0))

        with col2:
            st.metric("Domains Discovered", data.get("domains_discovered", 0))

        with col3:
            st.metric("Technologies", len(data.get("technologies", [])))

    def _render_ip_view(self, data: Dict[str, Any]) -> None:
        """Render IP address node view."""
        st.subheader("🖥️ IP Address Information")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**IP Address:** {data.get('ip_address', 'N/A')}")
            st.write(f"**Country:** {data.get('country', 'N/A')}")
            st.write(f"**City:** {data.get('city', 'N/A')}")
            st.write(f"**ISP:** {data.get('isp', 'N/A')}")

        with col2:
            st.write(f"**ASN:** {data.get('asn', 'N/A')}")
            st.write(f"**Hosting:** {data.get('hosting_provider', 'N/A')}")
            st.write(f"**VPN:** {'Yes' if data.get('is_vpn') else 'No'}")
            st.write(f"**Proxy:** {'Yes' if data.get('is_proxy') else 'No'}")

        # Services
        if data.get("services"):
            st.subheader("🔧 Services")
            for service in data["services"]:
                st.write(f"- {service}")

        # Vulnerabilities
        if data.get("vulnerabilities"):
            st.subheader("⚠️ Vulnerabilities")
            for vuln in data["vulnerabilities"]:
                st.warning(vuln)

    def _render_domain_view(self, data: Dict[str, Any]) -> None:
        """Render domain node view."""
        st.subheader("🌐 Domain Information")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**Domain:** {data.get('domain_name', 'N/A')}")
            st.write(f"**Registrar:** {data.get('registrar', 'N/A')}")
            st.write(f"**Registration:** {data.get('registration_date', 'N/A')}")
            st.write(f"**Expiration:** {data.get('expiration_date', 'N/A')}")

        with col2:
            st.write(f"**Website Title:** {data.get('website_title', 'N/A')}")
            st.write(f"**SSL Certificate:** {data.get('ssl_certificate', 'N/A')}")
            st.write(f"**SSL Issuer:** {data.get('ssl_issuer', 'N/A')}")

    def _render_generic_view(self, data: Dict[str, Any]) -> None:
        """Render generic node view."""
        st.subheader("📄 Details")
        st.json(data)

    def render_details_view(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
        options: Dict[str, Any],
    ) -> None:
        """Render detailed view with node selection.

        Args:
            nodes: List of nodes
            edges: List of edges
            options: View options
        """
        st.subheader("🔍 Node Details")

        # Node selection
        node_options = {n.node_id: f"{n.metadata.label} ({n.metadata.node_type.value})" for n in nodes}

        selected_node_id = st.selectbox(
            "Select Node",
            options=list(node_options.keys()),
            format_func=lambda x: node_options[x],
        )

        if selected_node_id:
            selected_node = next((n for n in nodes if n.node_id == selected_node_id), None)

            if selected_node:
                self.render_node_detail_view(selected_node)

                # Related edges
                st.subheader("🔗 Related Connections")

                related_edges = [
                    e for e in edges
                    if e.metadata.source_id == selected_node_id
                    or e.metadata.target_id == selected_node_id
                ]

                if related_edges:
                    for edge in related_edges:
                        col1, col2, col3 = st.columns([1, 2, 1])

                        with col1:
                            st.write(edge.metadata.source_id)

                        with col2:
                            st.write(f"→ **{edge.metadata.label}** →")

                        with col3:
                            st.write(edge.metadata.target_id)

                        st.caption(f"Confidence: {edge.metadata.confidence:.2f}")
                else:
                    st.info("No related connections")

    def run(
        self,
        nodes: List[GraphNode],
        edges: List[GraphEdge],
    ) -> None:
        """Run the Streamlit UI.

        Args:
            nodes: List of graph nodes
            edges: List of graph edges
        """
        # Store in session state
        st.session_state.nodes = nodes
        st.session_state.edges = edges

        # Render header
        self.render_header()

        # Render sidebar
        options = self.render_sidebar()

        # Render main content
        if options["view_mode"] == "Graph":
            self.render_graph_view(nodes, edges, options)

        elif options["view_mode"] == "Table":
            self.render_table_view(nodes, edges, options)

        elif options["view_mode"] == "Details":
            self.render_details_view(nodes, edges, options)


def main():
    """Main entry point."""
    # Create sample data for demonstration
    from kitten_palentir.models.graph_nodes import (
        GraphNode,
        GraphEdge,
        PersonNodeMetadata,
        CompanyNodeMetadata,
        EdgeMetadata,
        RelationType,
    )

    # Sample nodes
    person_metadata = PersonNodeMetadata(
        node_id="person_1",
        label="John Doe",
        title="Senior Software Engineer",
        full_name="John Doe",
        email="john@example.com",
        company="Tech Corp",
        job_title="Senior Software Engineer",
        linkedin_profile="https://linkedin.com/in/johndoe",
    )

    company_metadata = CompanyNodeMetadata(
        node_id="company_1",
        label="Tech Corp",
        title="Tech Corporation",
        company_name="Tech Corp",
        industry="Technology",
        website="https://techcorp.com",
    )

    nodes = [
        GraphNode(node_id="person_1", metadata=person_metadata),
        GraphNode(node_id="company_1", metadata=company_metadata),
    ]

    # Sample edges
    edge_metadata = EdgeMetadata(
        edge_id="edge_1",
        source_id="person_1",
        target_id="company_1",
        label="Works At",
        relationship_type=RelationType.WORKS_AT,
        strength=0.9,
    )

    edges = [
        GraphEdge(edge_id="edge_1", metadata=edge_metadata),
    ]

    # Run UI
    ui = StreamlitGraphUI()
    ui.run(nodes, edges)


if __name__ == "__main__":
    main()
