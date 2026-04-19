"""
Disaster Response Coordinator - Professional Streamlit UI
Interactive dashboard for emergency response simulation
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import time
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Disaster Response Coordinator",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for professional styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 2rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
        box-shadow: 0 10px 30px rgba(0,0,0,0.2);
    }
    .metric-card {
        background: linear-gradient(135deg, #0f3460 0%, #16213e 100%);
        padding: 1.2rem;
        border-radius: 15px;
        text-align: center;
        color: white;
        transition: transform 0.3s ease;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .victim-card {
        background: linear-gradient(135deg, #e94560 0%, #c72a48 100%);
        padding: 0.8rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: white;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .victim-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(233,69,96,0.3);
    }
    .resource-card {
        background: linear-gradient(135deg, #533483 0%, #3b1f6e 100%);
        padding: 0.8rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        color: white;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    .resource-card:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(83,52,131,0.3);
    }
    .status-badge {
        display: inline-block;
        padding: 0.2rem 0.6rem;
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: bold;
    }
    .status-rescued { background: #4CAF50; color: white; }
    .status-pending { background: #FF9800; color: white; }
    .status-in-progress { background: #2196F3; color: white; }
    .status-deceased { background: #f44336; color: white; }
    .priority-high { color: #ff4757; font-weight: bold; }
    .priority-medium { color: #ffa502; font-weight: bold; }
    .priority-low { color: #4CAF50; font-weight: bold; }
    .info-box {
        background: #1e1e2e;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
        border-left: 4px solid #667eea;
    }
</style>
""", unsafe_allow_html=True)

# API Configuration
BASE_URL = "http://localhost:8000"

# Session state initialization
if 'session_id' not in st.session_state:
    st.session_state.session_id = None
if 'observation' not in st.session_state:
    st.session_state.observation = None
if 'current_tab' not in st.session_state:
    st.session_state.current_tab = "dashboard"
if 'selected_victim' not in st.session_state:
    st.session_state.selected_victim = None
if 'selected_resource' not in st.session_state:
    st.session_state.selected_resource = None

# Helper functions
def call_api(endpoint, method="GET", data=None, session_id=None):
    """Generic API caller"""
    url = f"{BASE_URL}/{endpoint}"
    if session_id and "?" not in url:
        url = f"{url}?session_id={session_id}"
    
    try:
        if method == "POST":
            response = requests.post(url, json=data, timeout=15)
        else:
            response = requests.get(url, timeout=15)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None

def fetch_metrics():
    """Fetch metrics from API"""
    return call_api("metrics")

def fetch_tasks():
    """Fetch available tasks"""
    return call_api("tasks")

def get_priority_class(priority):
    """Get CSS class for priority"""
    if priority >= 8:
        return "priority-high"
    elif priority >= 5:
        return "priority-medium"
    return "priority-low"

def get_status_badge(status):
    """Get status badge HTML"""
    badges = {
        "discovered": '<span class="status-badge status-pending">⚠️ Pending</span>',
        "assigned": '<span class="status-badge status-in-progress">🚑 In Progress</span>',
        "rescued": '<span class="status-badge status-rescued">✅ Rescued</span>',
        "deceased": '<span class="status-badge status-deceased">💀 Deceased</span>'
    }
    return badges.get(status, '<span class="status-badge status-pending">⚠️ Unknown</span>')

# Header
st.markdown("""
<div class="main-header">
    <h1>🌊 Disaster Response Coordinator</h1>
    <p>Multi-agent AI system for emergency response coordination</p>
    <p style="font-size: 0.9rem; opacity: 0.8;">🌪️ Earthquake | 🌊 Flood | 🌀 Hurricane</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🎮 Control Panel")
    st.markdown("---")
    
    # Task selection
    st.markdown("#### 📋 Task Difficulty")
    difficulty = st.selectbox(
        "Select Difficulty",
        ["easy", "medium", "hard"],
        format_func=lambda x: x.upper(),
        help="Easy: 15 victims, 24h | Medium: 35 victims, 48h | Hard: 75 victims, 72h"
    )
    
    # Task info
    tasks_data = fetch_tasks()
    if tasks_data:
        for task in tasks_data.get("tasks", []):
            if task["id"] == difficulty:
                st.info(f"📖 {task['description'][:100]}...")
                st.caption(f"⏱️ Time Limit: {task['time_limit_hours']} hours")
    
    st.markdown("---")
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Reset Episode", type="primary", use_container_width=True):
            result = call_api(f"reset?difficulty={difficulty}", "POST")
            if result:
                st.session_state.session_id = result["session_id"]
                st.session_state.observation = result["observation"]
                st.session_state.selected_victim = None
                st.session_state.selected_resource = None
                st.success("✅ Episode reset!")
                time.sleep(0.5)
                st.rerun()
    
    with col2:
        if st.button("📊 Get Metrics", use_container_width=True):
            metrics = fetch_metrics()
            if metrics:
                st.session_state.metrics = metrics
                st.success("Metrics refreshed!")
    
    st.markdown("---")
    
    # Stats
    st.markdown("#### 📊 Stats")
    metrics = fetch_metrics()
    if metrics:
        st.metric("Total Episodes", metrics.get("total_episodes", 0))
        st.metric("Avg Score (Easy)", f"{metrics.get('average_scores', {}).get('easy', 0):.3f}")
        st.metric("Total Lives Saved", metrics.get("total_lives_saved", {}).get(difficulty, 0))
    
    st.markdown("---")
    st.caption("💡 Tip: Click on victims/resources to select them for allocation")

# Main content tabs
tab1, tab2, tab3, tab4 = st.tabs(["🎯 Dashboard", "📋 Victims", "🚒 Resources", "📈 Analytics"])

# ============================================================================
# TAB 1: DASHBOARD
# ============================================================================
with tab1:
    if st.session_state.observation:
        obs = st.session_state.observation
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            progress = obs.get('rescued_victims', 0) / max(1, obs.get('total_victims', 1))
            st.markdown(f"""
            <div class="metric-card">
                <h3>⏱️ Time Elapsed</h3>
                <h2>{obs.get('time_elapsed_hours', 0):.1f}h</h2>
                <small>of {obs.get('time_remaining_hours', 0) + obs.get('time_elapsed_hours', 0):.0f}h</small>
                <progress value="{progress}" max="1" style="width:100%; height:8px; border-radius:4px;"></progress>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>✅ Rescued</h3>
                <h2 style="color:#4CAF50;">{obs.get('rescued_victims', 0)}</h2>
                <small>of {obs.get('total_victims', 0)}</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>⚠️ Pending</h3>
                <h2 style="color:#FFA500;">{len(obs.get('pending_victims', []))}</h2>
                <small>awaiting rescue</small>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            st.markdown(f"""
            <div class="metric-card">
                <h3>💀 Deceased</h3>
                <h2 style="color:#e94560;">{obs.get('deceased_victims', 0)}</h2>
                <small>critical</small>
            </div>
            """, unsafe_allow_html=True)
        
        # Progress bar
        st.progress(obs.get('rescued_victims', 0) / max(1, obs.get('total_victims', 1)))
        
        # Action panel
        st.markdown("### 🎯 Take Action")
        
        col_left, col_right = st.columns([1, 1])
        
        with col_left:
            st.markdown("#### 👥 Select Victim")
            pending = obs.get('pending_victims', [])
            if pending:
                victim_options = {f"{v['id']} (P{v.get('priority', 5)})": v['id'] for v in pending[:10]}
                selected_victim_display = st.selectbox("Victims", list(victim_options.keys()))
                selected_victim_id = victim_options[selected_victim_display]
            else:
                st.info("No pending victims")
                selected_victim_id = None
        
        with col_right:
            st.markdown("#### 🚒 Select Resource")
            available = obs.get('available_resources', [])
            if available:
                resource_options = {f"{r['id']} ({r['type']})": r['id'] for r in available}
                selected_resource_display = st.selectbox("Resources", list(resource_options.keys()))
                selected_resource_id = resource_options[selected_resource_display]
            else:
                st.warning("No available resources")
                selected_resource_id = None
        
        # Priority and confidence
        col_a, col_b = st.columns(2)
        with col_a:
            priority = st.slider("Priority (1=Lowest, 10=Highest)", 1, 10, 8)
        with col_b:
            confidence = st.slider("Confidence", 0.0, 1.0, 0.85, 0.05)
        
        # Dispatch button
        if st.button("🚑 Dispatch Resource", type="primary", use_container_width=True):
            if selected_victim_id and selected_resource_id and st.session_state.session_id:
                action = {
                    "allocations": [{
                        "resource_id": selected_resource_id,
                        "victim_id": selected_victim_id,
                        "priority": priority
                    }],
                    "strategic": None,
                    "confidence": confidence
                }
                
                result = call_api("step", "POST", action, st.session_state.session_id)
                if result:
                    st.session_state.observation = result.get("observation")
                    st.success(f"✅ Resource dispatched! Reward: {result.get('observation', {}).get('current_reward', 0):.3f}")
                    time.sleep(0.5)
                    st.rerun()
            else:
                st.error("Please select both a victim and a resource")
        
        # Score display
        st.markdown("---")
        st.markdown("### 📊 Performance Score")
        
        score = obs.get('cumulative_reward', 0)
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=score * 100,
            title={"text": "Current Score (%)"},
            delta={"reference": 80, "increasing": {"color": "green"}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#4CAF50"},
                "steps": [
                    {"range": [0, 33], "color": "#ff4d4d"},
                    {"range": [33, 66], "color": "#ffa500"},
                    {"range": [66, 100], "color": "#4CAF50"}
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": 85
                }
            }
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("👈 Click 'Reset Episode' in the sidebar to start a new disaster response simulation")
        
        # Feature showcase
        st.markdown("""
        ### 🌟 Features
        
        | Feature | Description |
        |---------|-------------|
        | **3 Difficulty Levels** | Easy (15 victims), Medium (35), Hard (75) |
        | **Real-time Simulation** | Physics-based movement with terrain/weather effects |
        | **Multi-step Rescue** | Resources take time to reach victims |
        | **Priority System** | Higher priority victims should be rescued first |
        | **Dynamic Events** | Aftershocks, weather changes, road blockages |
        | **Performance Metrics** | Track lives saved, response time, efficiency |
        """)

# ============================================================================
# TAB 2: VICTIMS
# ============================================================================
with tab2:
    if st.session_state.observation:
        obs = st.session_state.observation
        pending = obs.get('pending_victims', [])
        
        st.markdown("### 👥 Victim List")
        st.caption(f"Total: {obs.get('total_victims', 0)} | Rescued: {obs.get('rescued_victims', 0)} | Pending: {len(pending)}")
        
        if pending:
            for victim in pending:
                priority = victim.get('priority', 5)
                priority_class = get_priority_class(priority)
                in_progress = victim.get('in_progress', False)
                
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    st.markdown(f"**{victim['id']}**")
                with col2:
                    st.markdown(f'<span class="{priority_class}">P{priority}</span>', unsafe_allow_html=True)
                with col3:
                    st.markdown(victim.get('triage', 'Unknown'))
                with col4:
                    if in_progress:
                        st.markdown("🚑 In Progress")
                    else:
                        if st.button(f"Select", key=f"select_{victim['id']}"):
                            st.session_state.selected_victim = victim['id']
                            st.success(f"Selected victim: {victim['id']}")
        else:
            st.success("🎉 All victims have been rescued!")
    else:
        st.info("Start an episode to see victims")

# ============================================================================
# TAB 3: RESOURCES
# ============================================================================
with tab3:
    if st.session_state.observation:
        obs = st.session_state.observation
        available = obs.get('available_resources', [])
        deployed = obs.get('deployed_resources', [])
        
        st.markdown("### 🚒 Available Resources")
        st.caption(f"Available: {len(available)} | Deployed: {len(deployed)}")
        
        if available:
            for resource in available:
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    st.markdown(f"**{resource['id']}**")
                with col2:
                    st.markdown(resource['type'])
                with col3:
                    if st.button(f"Select", key=f"select_res_{resource['id']}"):
                        st.session_state.selected_resource = resource['id']
                        st.success(f"Selected resource: {resource['id']}")
        else:
            st.warning("No available resources")
        
        st.markdown("---")
        st.markdown("### 🚑 Deployed Resources")
        if deployed:
            for resource in deployed:
                st.markdown(f"**{resource['id']}** - {resource['type']} - {resource.get('current_task', 'En route')}")
        else:
            st.info("No resources deployed")
    else:
        st.info("Start an episode to see resources")

# ============================================================================
# TAB 4: ANALYTICS
# ============================================================================
with tab4:
    st.markdown("### 📈 Performance Analytics")
    
    metrics = fetch_metrics()
    if metrics:
        # Average scores chart
        scores = metrics.get('average_scores', {})
        if scores:
            df = pd.DataFrame([
                {"Task": k.upper(), "Score": v} for k, v in scores.items()
            ])
            fig = px.bar(df, x="Task", y="Score", title="Average Scores by Difficulty",
                        color="Score", range_y=[0, 1], color_continuous_scale="Viridis")
            st.plotly_chart(fig, use_container_width=True)
        
        # Total lives saved
        lives = metrics.get('total_lives_saved', {})
        if lives:
            df2 = pd.DataFrame([
                {"Task": k.upper(), "Lives Saved": v} for k, v in lives.items()
            ])
            fig2 = px.bar(df2, x="Task", y="Lives Saved", title="Total Lives Saved by Difficulty",
                         color="Lives Saved", color_continuous_scale="Reds")
            st.plotly_chart(fig2, use_container_width=True)
        
        # Response times
        times = metrics.get('average_response_times', {})
        if times:
            df3 = pd.DataFrame([
                {"Task": k.upper(), "Response Time (s)": v} for k, v in times.items()
            ])
            fig3 = px.line(df3, x="Task", y="Response Time (s)", title="Average Response Times",
                          markers=True)
            st.plotly_chart(fig3, use_container_width=True)
        
        # Summary metrics
        st.markdown("### 📊 Summary Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Episodes", metrics.get('total_episodes', 0))
        with col2:
            avg_score = sum(scores.values()) / len(scores) if scores else 0
            st.metric("Overall Avg Score", f"{avg_score:.3f}")
        with col3:
            total_lives = sum(lives.values()) if lives else 0
            st.metric("Total Lives Saved", total_lives)
    else:
        st.info("Run some episodes to see analytics")

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #666; padding: 20px;">
    <p>🚀 Powered by <strong>OpenEnv</strong> | 🤖 Multi-Agent RL | 🌊 Disaster Response</p>
    <p style="font-size: 12px;">3 Difficulty Levels • Physics-based Movement • Dynamic Events • Real-time Metrics</p>
</div>
""", unsafe_allow_html=True)