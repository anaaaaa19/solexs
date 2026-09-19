"""
SoLEXS / Aditya-L1 Mission Control Theme & Styling
Color System:
--void: #05060f
--deep-indigo: #0a0c22
--nebula-violet: #241a4a
--nebula-teal: #113238
--ion-cyan: #5fd4c9
--solar-gold: #f5a94e
--solar-flare: #ff8a3d
--hairline: rgba(150,165,210,0.14)
--text-primary: #eef0fb
--text-muted: #8891b0
--text-dim: #565f7d
"""

import plotly.graph_objects as go

MISSION_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Sans:wght@300;400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap');

:root {
    --void: #05060f;
    --deep-indigo: #0a0c22;
    --nebula-violet: #241a4a;
    --nebula-teal: #113238;
    --ion-cyan: #5fd4c9;
    --solar-gold: #f5a94e;
    --solar-flare: #ff8a3d;
    --hairline: rgba(150, 165, 210, 0.14);
    --hairline-gold: rgba(245, 169, 78, 0.3);
    --hairline-cyan: rgba(95, 212, 201, 0.3);
    --text-primary: #eef0fb;
    --text-muted: #8891b0;
    --text-dim: #565f7d;
}

/* Global Container and Background */
.stApp {
    background-color: #05060f !important;
    background-image: 
        radial-gradient(ellipse at 90% 5%, rgba(245, 169, 78, 0.05) 0%, transparent 45%),
        radial-gradient(ellipse at 10% 12%, rgba(17, 50, 56, 0.18) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 98%, rgba(36, 26, 74, 0.15) 0%, transparent 55%) !important;
    font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: #eef0fb !important;
}

/* Hide default streamlit decoration header */
header[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: 1px solid var(--hairline) !important;
}

/* Top Mission Control Bar */
.mission-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.75rem 1.25rem;
    background: #0a0c22;
    border: 1px solid var(--hairline);
    border-radius: 2px;
    margin-bottom: 1.25rem;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

.mission-left {
    display: flex;
    flex-direction: column;
}

.mission-brand {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.15rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    color: #eef0fb;
    display: flex;
    align-items: center;
    gap: 0.55rem;
}

.status-dot-gold {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: var(--solar-gold);
    box-shadow: 0 0 10px var(--solar-gold);
    display: inline-block;
    animation: pulse-dot 2.5s infinite ease-in-out;
}

.status-dot-cyan {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background-color: var(--ion-cyan);
    box-shadow: 0 0 8px var(--ion-cyan);
    display: inline-block;
    animation: pulse-dot 2s infinite ease-in-out;
}

@keyframes pulse-dot {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.45; transform: scale(0.85); }
}

.mission-sub {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: var(--text-muted);
    letter-spacing: 0.06em;
    margin-top: 0.15rem;
}

.mission-right {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.2rem;
}

.mission-orbit-tag {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: var(--ion-cyan);
    letter-spacing: 0.05em;
}

.mission-telemetry-badge {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.72rem;
    color: var(--solar-gold);
    background: rgba(245, 169, 78, 0.08);
    border: 1px solid var(--hairline-gold);
    padding: 0.2rem 0.55rem;
    border-radius: 2px;
}

/* Mission Section Header */
.section-mission-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 1px solid var(--hairline);
    padding-bottom: 0.5rem;
    margin-top: 0.5rem;
    margin-bottom: 1.25rem;
}

.section-mission-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.35rem;
    font-weight: 600;
    color: #eef0fb;
    letter-spacing: 0.03em;
}

.section-mission-subtitle {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.85rem;
    color: var(--text-muted);
    margin-top: 0.15rem;
}

.section-mission-meta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: var(--text-dim);
    text-align: right;
}

.section-mission-meta span {
    color: var(--ion-cyan);
}

/* Sidebar Custom Styling */
section[data-testid="stSidebar"] {
    background-color: #080a1c !important;
    border-right: 1px solid var(--hairline) !important;
}

section[data-testid="stSidebar"] hr {
    border-color: var(--hairline) !important;
}

/* Sidebar Radio Buttons -> Mission Console Navigation */
div[data-testid="stRadio"] > div {
    gap: 0.25rem !important;
}

div[data-testid="stRadio"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
    color: var(--text-muted) !important;
    background: #0a0c22 !important;
    border: 1px solid var(--hairline) !important;
    border-left: 3px solid transparent !important;
    border-radius: 2px !important;
    padding: 0.55rem 0.8rem !important;
    margin-bottom: 0.2rem !important;
    transition: all 0.2s ease !important;
    display: flex !important;
    align-items: center !important;
    cursor: pointer !important;
}

div[data-testid="stRadio"] label:hover {
    background: #111536 !important;
    color: #eef0fb !important;
    border-color: var(--hairline-gold) !important;
    border-left: 3px solid var(--solar-gold) !important;
}

div[data-testid="stRadio"] label[data-checked="true"],
div[data-testid="stRadio"] div[aria-checked="true"] {
    background: #12173b !important;
    color: #eef0fb !important;
    border-color: var(--hairline-gold) !important;
    border-left: 3px solid var(--solar-gold) !important;
    font-weight: 600 !important;
    box-shadow: inset 0 0 12px rgba(245, 169, 78, 0.08) !important;
}

/* Hide default radio circle */
div[data-testid="stRadio"] input[type="radio"] {
    accent-color: var(--solar-gold) !important;
}

/* KPI Telemetry Strip */
.kpi-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem;
    margin-bottom: 1.25rem;
}

.kpi-card {
    background: #0a0c22;
    border: 1px solid var(--hairline);
    border-radius: 2px;
    padding: 0.75rem 1rem;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s ease;
}

.kpi-card:hover {
    border-color: var(--hairline-cyan);
}

.kpi-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 24px;
    height: 2px;
    background: var(--ion-cyan);
}

.kpi-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.45rem;
    font-weight: 700;
    color: #eef0fb;
    line-height: 1.2;
    margin-top: 0.2rem;
}

.kpi-label {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    color: var(--text-muted);
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.kpi-status {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.68rem;
    color: var(--ion-cyan);
    margin-top: 0.35rem;
    display: flex;
    align-items: center;
    gap: 0.35rem;
}

/* Rack Instrument Panel */
.rack-panel {
    background: #0a0c22;
    border: 1px solid var(--hairline);
    border-radius: 2px;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
}

.rack-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    border-bottom: 1px solid var(--hairline);
    padding-bottom: 0.45rem;
    margin-bottom: 0.85rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.rack-header-gold {
    color: var(--solar-gold);
}

.rack-header-cyan {
    color: var(--ion-cyan);
}

/* Metric styling override */
div[data-testid="stMetric"] {
    background: #0a0c22 !important;
    border: 1px solid var(--hairline) !important;
    border-radius: 2px !important;
    padding: 0.65rem 0.85rem !important;
}

div[data-testid="stMetricLabel"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    color: var(--text-muted) !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}

div[data-testid="stMetricValue"] {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 1.35rem !important;
    font-weight: 700 !important;
    color: #eef0fb !important;
}

/* Dataframe styling */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--hairline) !important;
    border-radius: 2px !important;
    background: #0a0c22 !important;
}

/* Tabs styling */
div[data-testid="stTabs"] button[role="tab"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
    color: var(--text-muted) !important;
    background: transparent !important;
    border-bottom: 2px solid transparent !important;
    padding: 0.5rem 1rem !important;
}

div[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    color: var(--solar-gold) !important;
    border-bottom: 2px solid var(--solar-gold) !important;
    font-weight: 600 !important;
}

div[data-testid="stTabs"] button[role="tab"]:hover {
    color: #eef0fb !important;
}

/* Buttons */
.stButton > button {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
    background: #0e1338 !important;
    color: #eef0fb !important;
    border: 1px solid var(--hairline) !important;
    border-radius: 2px !important;
    padding: 0.45rem 0.95rem !important;
    transition: all 0.2s ease !important;
}

.stButton > button:hover {
    border-color: var(--ion-cyan) !important;
    color: var(--ion-cyan) !important;
    box-shadow: 0 0 10px rgba(95, 212, 201, 0.2) !important;
}

.stDownloadButton > button {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.8rem !important;
    background: #0a0c22 !important;
    color: var(--ion-cyan) !important;
    border: 1px solid var(--hairline-cyan) !important;
    border-radius: 2px !important;
}

/* Inputs & Selectboxes */
div[data-testid="stSelectbox"] > div,
div[data-testid="stDateInput"] > div,
div[data-testid="stTextInput"] > div,
div[data-testid="stNumberInput"] > div {
    background: #0a0c22 !important;
    border: 1px solid var(--hairline) !important;
    border-radius: 2px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    color: #eef0fb !important;
}

/* Caveat / Diagnostic Alert */
.mission-alert {
    background: rgba(36, 26, 74, 0.4);
    border: 1px solid var(--hairline);
    border-left: 3px solid var(--solar-flare);
    padding: 0.65rem 0.95rem;
    border-radius: 2px;
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.82rem;
    color: #ffd5b5;
    margin-bottom: 1rem;
}

.mission-alert-cyan {
    background: rgba(17, 50, 56, 0.4);
    border: 1px solid var(--hairline);
    border-left: 3px solid var(--ion-cyan);
    padding: 0.65rem 0.95rem;
    border-radius: 2px;
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.82rem;
    color: #bdf5f0;
    margin-bottom: 1rem;
}

/* Flare Event Tag */
.badge-flare {
    display: inline-block;
    padding: 0.15rem 0.45rem;
    border-radius: 2px;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
}
.badge-x { background: rgba(255, 60, 60, 0.2); border: 1px solid #ff4d4d; color: #ff8080; }
.badge-m { background: rgba(245, 169, 78, 0.2); border: 1px solid var(--solar-gold); color: var(--solar-gold); }
.badge-c { background: rgba(95, 212, 201, 0.2); border: 1px solid var(--ion-cyan); color: var(--ion-cyan); }
.badge-b { background: rgba(136, 145, 176, 0.2); border: 1px solid var(--text-muted); color: var(--text-primary); }

/* Compact event row */
.event-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.45rem 0.75rem;
    border-bottom: 1px solid var(--hairline);
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
}
.event-row:hover {
    background: rgba(245, 169, 78, 0.05);
}

/* Telemetry Continuity Bar */
.continuity-container {
    background: #0a0c22;
    border: 1px solid var(--hairline);
    padding: 0.75rem 1rem;
    border-radius: 2px;
    margin-bottom: 1rem;
}
.continuity-bar {
    display: flex;
    height: 16px;
    border-radius: 2px;
    overflow: hidden;
    margin: 0.5rem 0;
    background: #111536;
    border: 1px solid var(--hairline);
}
.seg-active {
    background: var(--ion-cyan);
    height: 100%;
}
.seg-gap {
    background: #ff5252;
    height: 100%;
}
</style>
"""

def apply_mission_control_theme(fig, is_heatmap=False):
    """
    Applies the SoLEXS / Aditya-L1 scientific instrument console theme to any Plotly figure.
    """
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0, 0, 0, 0)",
        plot_bgcolor="#0a0c22",
        font=dict(
            family="IBM Plex Mono, monospace",
            size=11,
            color="#8891b0"
        ),
        margin=dict(l=40, r=25, t=35, b=35),
        xaxis=dict(
            gridcolor="rgba(150, 165, 210, 0.08)",
            linecolor="rgba(150, 165, 210, 0.2)",
            zerolinecolor="rgba(150, 165, 210, 0.15)",
            tickfont=dict(family="IBM Plex Mono, monospace", size=10, color="#8891b0"),
            title_font=dict(family="IBM Plex Mono, monospace", size=11, color="#eef0fb"),
        ),
        yaxis=dict(
            gridcolor="rgba(150, 165, 210, 0.08)",
            linecolor="rgba(150, 165, 210, 0.2)",
            zerolinecolor="rgba(150, 165, 210, 0.15)",
            tickfont=dict(family="IBM Plex Mono, monospace", size=10, color="#8891b0"),
            title_font=dict(family="IBM Plex Mono, monospace", size=11, color="#eef0fb"),
        ),
        hoverlabel=dict(
            bgcolor="#0a0c22",
            bordercolor="#5fd4c9",
            font=dict(family="IBM Plex Mono, monospace", size=11, color="#eef0fb")
        ),
        legend=dict(
            bgcolor="rgba(10, 12, 34, 0.8)",
            bordercolor="rgba(150, 165, 210, 0.2)",
            borderwidth=1,
            font=dict(family="IBM Plex Mono, monospace", size=10, color="#eef0fb")
        )
    )
    if is_heatmap:
        fig.update_layout(
            coloraxis_colorbar=dict(
                tickfont=dict(family="IBM Plex Mono, monospace", size=10, color="#8891b0"),
                title_font=dict(family="IBM Plex Mono, monospace", size=11, color="#eef0fb"),
            )
        )
    return fig
