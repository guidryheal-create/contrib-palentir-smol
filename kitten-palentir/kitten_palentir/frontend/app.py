"""Palentir OSINT - Streamlit Frontend Application.

Main Streamlit app that integrates workforce and displays real-time graph updates.
"""

import asyncio
import logging
import streamlit as st
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from kitten_palentir.config.settings import get_settings
from kitten_palentir.workforce.camel_integrated_workforce import PalentirCAMELWorkforce
from kitten_palentir.services.graph_visualization import GraphVisualizationService

logger = logging.getLogger(__name__)

# Lazy load settings to avoid validation errors in tests
def _get_settings():
    """Get settings instance (lazy loaded)."""
    return get_settings()

# Page configuration
st.set_page_config(
    page_title="Palentir OSINT - Intelligence Platform",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "workforce" not in st.session_state:
    st.session_state.workforce = None
if "graph_service" not in st.session_state:
    st.session_state.graph_service = GraphVisualizationService()
if "task_history" not in st.session_state:
    st.session_state.task_history = []
if "graph_updates" not in st.session_state:
    st.session_state.graph_updates = []
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []
if "auto_refresh" not in st.session_state:
    st.session_state.auto_refresh = True


def initialize_workforce() -> Optional[PalentirCAMELWorkforce]:
    """Initialize workforce if not already initialized."""
    if st.session_state.workforce is None:
        try:
            settings = _get_settings()
            workforce = PalentirCAMELWorkforce(
                description="Palentir OSINT Workforce",
                enable_mcp=False,  # Can be enabled via UI
                share_memory=True,
                neo4j_url=settings.effective_neo4j_uri,
                neo4j_username=settings.neo4j_username,
                neo4j_password=settings.neo4j_password,
            )
            st.session_state.workforce = workforce
            return workforce
        except Exception as e:
            st.error(f"Failed to initialize workforce: {e}")
            logger.error(f"Workforce initialization failed: {e}")
            return None
    return st.session_state.workforce


def render_sidebar() -> Dict[str, Any]:
    """Render sidebar with controls."""
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Workforce controls
        st.subheader("Workforce")
        enable_mcp = st.checkbox("Enable MCP", value=False)
        share_memory = st.checkbox("Share Memory", value=True)
        
        if st.button("🔄 Reinitialize Workforce"):
            st.session_state.workforce = None
            initialize_workforce()
            st.success("Workforce reinitialized")
        
        st.divider()
        
        # Graph controls
        st.subheader("Graph View")
        view_mode = st.radio(
            "View Mode",
            ["Dashboard", "Graph Visualization", "Task Monitor", "Agent Status", "Chat Logs"],
            index=0,
        )
        
        auto_refresh = st.checkbox("Auto-refresh", value=st.session_state.auto_refresh)
        st.session_state.auto_refresh = auto_refresh
        
        if auto_refresh:
            refresh_interval = st.slider("Refresh Interval (seconds)", 1, 60, 5)
        else:
            refresh_interval = 5
        
        st.divider()
        
        # Statistics
        st.subheader("📊 Statistics")
        if st.session_state.workforce:
            info = st.session_state.workforce.get_workforce_info()
            st.metric("Agents", info.get("agent_count", 0))
            st.metric("Tasks Completed", len(st.session_state.task_history))
            st.metric("Graph Updates", len(st.session_state.graph_updates))
        
        return {
            "view_mode": view_mode,
            "enable_mcp": enable_mcp,
            "share_memory": share_memory,
            "refresh_interval": refresh_interval,
        }


def render_dashboard(workforce: PalentirCAMELWorkforce):
    """Render main dashboard."""
    st.title("🕸️ Palentir OSINT - Intelligence Dashboard")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Active Agents", len(workforce.list_agents()))
    
    with col2:
        st.metric("Tasks Completed", len(st.session_state.task_history))
    
    with col3:
        st.metric("Graph Nodes", len(st.session_state.graph_updates))
    
    st.divider()
    
    # Task input
    st.subheader("📝 New Task")
    task_input = st.text_area(
        "Enter OSINT task query:",
        placeholder="e.g., Investigate company 'Acme Corp' and find related domains",
        height=100,
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 Execute Task", type="primary"):
            if task_input:
                execute_task(workforce, task_input)
            else:
                st.warning("Please enter a task query")
    
    with col2:
        if st.button("🔄 Refresh Graph"):
            refresh_graph_view()
    
    st.divider()
    
    # Recent tasks
    st.subheader("📋 Recent Tasks")
    if st.session_state.task_history:
        for task in st.session_state.task_history[-10:]:
            with st.expander(f"Task: {task.get('query', 'Unknown')[:50]}..."):
                st.json(task)
    else:
        st.info("No tasks executed yet")


def render_graph_visualization():
    """Render graph visualization with improved display."""
    st.title("📈 Knowledge Graph Visualization")
    
    # Get graph data
    graph_data = get_graph_data()
    
    if not graph_data or not graph_data.get("nodes"):
        st.info("No graph data available. Execute some tasks first.")
        return
    
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])
    
    # Display graph statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Nodes", len(nodes))
    with col2:
        st.metric("Total Edges", len(edges))
    with col3:
        # Count node types
        node_types = {}
        for node in nodes:
            node_type = node.get("type", "unknown")
            node_types[node_type] = node_types.get(node_type, 0) + 1
        st.metric("Node Types", len(node_types))
    with col4:
        st.metric("Last Update", datetime.now().strftime("%H:%M:%S"))
    
    st.divider()
    
    # Graph visualization using GraphVisualizationService
    st.subheader("🕸️ Interactive Graph")
    try:
        # Use the graph visualization service
        from kitten_palentir.frontend.streamlit_graph_ui import StreamlitGraphUI
        
        # Convert dict nodes/edges to GraphNode/GraphEdge objects if needed
        # For now, display as JSON but with better formatting
        with st.expander("📊 View Graph Data", expanded=True):
            tab1, tab2 = st.tabs(["Nodes", "Edges"])
            
            with tab1:
                if nodes:
                    # Display nodes in a table format
                    try:
                        import pandas as pd
                    except ImportError:
                        st.warning("pandas not available, displaying as JSON")
                        st.json(nodes[:20])
                        return
                    
                    node_data = []
                    for node in nodes[:50]:  # Limit to 50 for performance
                        node_data.append({
                            "ID": node.get("id", node.get("node_id", "unknown")),
                            "Label": node.get("label", "N/A"),
                            "Type": node.get("type", "unknown"),
                            "Confidence": node.get("confidence", 0.0),
                            "Source": node.get("source", "unknown"),
                        })
                    if node_data:
                        df = pd.DataFrame(node_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No nodes to display")
                else:
                    st.info("No nodes available")
            
            with tab2:
                if edges:
                    try:
                        import pandas as pd
                    except ImportError:
                        st.warning("pandas not available, displaying as JSON")
                        st.json(edges[:20])
                        return
                    
                    edge_data = []
                    for edge in edges[:50]:  # Limit to 50 for performance
                        edge_data.append({
                            "Source": edge.get("source", edge.get("source_id", "unknown")),
                            "Target": edge.get("target", edge.get("target_id", "unknown")),
                            "Relationship": edge.get("label", edge.get("relationship_type", "unknown")),
                            "Strength": edge.get("strength", 0.0),
                            "Confidence": edge.get("confidence", 0.0),
                        })
                    if edge_data:
                        df = pd.DataFrame(edge_data)
                        st.dataframe(df, use_container_width=True, hide_index=True)
                    else:
                        st.info("No edges to display")
                else:
                    st.info("No edges available")
        
        # Node type breakdown
        if node_types:
            try:
                import pandas as pd
                st.subheader("📊 Node Type Breakdown")
                type_df = pd.DataFrame([
                    {"Type": k, "Count": v} for k, v in sorted(node_types.items(), key=lambda x: x[1], reverse=True)
                ])
                st.bar_chart(type_df.set_index("Type"))
            except ImportError:
                st.subheader("📊 Node Type Breakdown")
                for node_type, count in sorted(node_types.items(), key=lambda x: x[1], reverse=True):
                    st.write(f"- **{node_type}**: {count}")
    
    except Exception as e:
        logger.error(f"Graph visualization error: {e}")
        st.error(f"Graph visualization error: {e}")
        # Fallback to JSON display
        with st.expander("View Raw Graph Data"):
            st.json(graph_data)
    
    # Node browser
    st.divider()
    st.subheader("🔍 Node Browser")
    if nodes:
        node_options = {
            f"{node.get('label', node.get('id', 'unknown'))} ({node.get('type', 'unknown')})": node.get("id", node.get("node_id", "unknown"))
            for node in nodes[:100]
        }
        selected_label = st.selectbox("Select Node", options=list(node_options.keys()))
        if selected_label:
            selected_id = node_options[selected_label]
            node_details = next(
                (n for n in nodes if n.get("id", n.get("node_id")) == selected_id),
                None
            )
            if node_details:
                st.json(node_details)


def render_task_monitor():
    """Render task monitoring view."""
    st.title("📊 Task Monitor")
    
    if not st.session_state.task_history:
        st.info("No tasks executed yet")
        return
    
    # Task timeline
    st.subheader("Task Timeline")
    for idx, task in enumerate(reversed(st.session_state.task_history[-20:])):
        with st.expander(
            f"Task #{len(st.session_state.task_history) - idx}: "
            f"{task.get('query', 'Unknown')[:50]}"
        ):
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Status:**", task.get("status", "unknown"))
                st.write("**Timestamp:**", task.get("timestamp", "unknown"))
            with col2:
                st.write("**Agent:**", task.get("agent", "unknown"))
                st.write("**Duration:**", task.get("duration", "N/A"))
            
            if task.get("result"):
                st.json(task.get("result"))


def render_agent_status(workforce: PalentirCAMELWorkforce):
    """Render agent status view."""
    st.title("🤖 Agent Status")
    
    agents = workforce.list_agents()
    
    if not agents:
        st.warning("No agents available")
        return
    
    for agent_name in agents:
        with st.expander(f"Agent: {agent_name}"):
            agent = workforce.get_agent(agent_name)
            if agent:
                tools = workforce.get_agent_tools(agent_name)
                st.write(f"**Tools Available:** {len(tools)}")
                if tools:
                    st.json([{"name": str(tool)} for tool in tools[:5]])


def render_chat_logs():
    """Render chat logs view with CAMEL-style message display."""
    st.title("💬 Chat Logs")
    
    if not st.session_state.chat_messages:
        st.info("No chat messages yet. Start a conversation by executing a task.")
        return
    
    # Chat display container
    chat_container = st.container()
    
    with chat_container:
        # Display all messages
        for idx, msg in enumerate(st.session_state.chat_messages):
            role = msg.get("role", "user")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            status = msg.get("status", "success")
            
            # Format timestamp
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    time_str = dt.strftime("%H:%M:%S")
                except:
                    time_str = timestamp[:8] if len(timestamp) > 8 else timestamp
            else:
                time_str = ""
            
            # Display message based on role
            if role == "user":
                with st.chat_message("user"):
                    st.markdown(content)
                    if time_str:
                        st.caption(f"🕐 {time_str}")
            else:
                with st.chat_message("assistant"):
                    # Show status badge
                    if status == "error":
                        st.error("❌ Error occurred")
                    elif status == "success":
                        st.success("✅ Success")
                    
                    # Display content
                    if isinstance(content, str) and len(content) > 500:
                        with st.expander("View full response"):
                            st.markdown(content)
                        st.markdown(content[:500] + "...")
                    else:
                        st.markdown(content)
                    
                    # Show metadata
                    col1, col2 = st.columns(2)
                    with col1:
                        if time_str:
                            st.caption(f"🕐 {time_str}")
                    with col2:
                        if msg.get("duration"):
                            st.caption(f"⏱️ {msg.get('duration')}")
    
    # Clear chat button
    st.divider()
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_messages = []
        st.rerun()


async def execute_task_async(workforce: PalentirCAMELWorkforce, query: str):
    """Execute task asynchronously."""
    start_time = datetime.now()
    
    # Add user message to chat
    st.session_state.chat_messages.append({
        "role": "user",
        "content": query,
        "timestamp": datetime.now().isoformat(),
    })
    
    try:
        result = await workforce.process_task(query)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Extract response content
        response_content = result.get("result", {}).get("content", str(result))
        if isinstance(response_content, dict):
            response_content = json.dumps(response_content, indent=2)
        
        # Add assistant response to chat
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": response_content,
            "timestamp": datetime.now().isoformat(),
            "status": result.get("status", "unknown"),
            "duration": f"{duration:.2f}s",
        })
        
        task_record = {
            "query": query,
            "status": result.get("status", "unknown"),
            "result": result,
            "timestamp": datetime.now().isoformat(),
            "duration": f"{duration:.2f}s",
            "agent": "workforce",
        }
        
        st.session_state.task_history.append(task_record)
        
        # Update graph if result contains graph data
        if result.get("status") == "success":
            update_graph_from_result(result)
        
        return result
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        error_msg = str(e)
        
        # Add error message to chat
        st.session_state.chat_messages.append({
            "role": "assistant",
            "content": f"Error: {error_msg}",
            "timestamp": datetime.now().isoformat(),
            "status": "error",
        })
        
        st.error(f"Task execution failed: {e}")
        return {"status": "error", "error": error_msg}


def execute_task(workforce: PalentirCAMELWorkforce, query: str):
    """Execute task synchronously."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(execute_task_async(workforce, query))
        st.success("Task executed successfully!")
        return result
    finally:
        loop.close()


def get_graph_data() -> Dict[str, Any]:
    """Get current graph data."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            graph_data = loop.run_until_complete(
                st.session_state.graph_service.get_graphistry_data()
            )
            return graph_data
        finally:
            loop.close()
    except Exception as e:
        logger.error(f"Failed to get graph data: {e}")
        return {"nodes": [], "edges": []}


def refresh_graph_view():
    """Refresh graph view."""
    graph_data = get_graph_data()
    st.session_state.graph_updates.append({
        "timestamp": datetime.now().isoformat(),
        "node_count": len(graph_data.get("nodes", [])),
        "edge_count": len(graph_data.get("edges", [])),
    })
    st.rerun()


def update_graph_from_result(result: Dict[str, Any]):
    """Update graph from task result."""
    # Extract graph-related data from result
    if result.get("result") and isinstance(result.get("result"), dict):
        graph_update = {
            "timestamp": datetime.now().isoformat(),
            "source": "task_execution",
            "data": result.get("result"),
        }
        st.session_state.graph_updates.append(graph_update)


def main():
    """Main application entry point."""
    # Initialize workforce
    workforce = initialize_workforce()
    
    if not workforce:
        st.error("Failed to initialize workforce. Please check configuration.")
        return
    
    # Render sidebar
    options = render_sidebar()
    
    # Render main content based on view mode
    view_mode = options["view_mode"]
    
    if view_mode == "Dashboard":
        render_dashboard(workforce)
    elif view_mode == "Graph Visualization":
        render_graph_visualization()
    elif view_mode == "Task Monitor":
        render_task_monitor()
    elif view_mode == "Agent Status":
        render_agent_status(workforce)
    elif view_mode == "Chat Logs":
        render_chat_logs()
    
    # Auto-refresh if enabled
    if options.get("auto_refresh", False):
        import time
        time.sleep(options.get("refresh_interval", 5))
        st.rerun()


if __name__ == "__main__":
    main()

