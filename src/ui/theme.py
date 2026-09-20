"""
SoLEXS / Aditya-L1 Mission Control Theme & Styling
Aerospace Scientific Design System
Color System:
--void: #05060f;
--deep-indigo: #0a0c22;
--nebula-violet: #241a4a;
--nebula-teal: #113238;
--ion-cyan: #5fd4c9;
--solar-gold: #f5a94e;
--solar-flare: #ff8a3d;
--hairline: rgba(150, 165, 210, 0.14);
--text-primary: #eef0fb;
--text-muted: #8891b0;
--text-dim: #565f7d;
"""

import plotly.graph_objects as go

MISSION_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
    --void: #05060f;
    --deep-indigo: #0a0c22;
    --nebula-violet: #241a4a;
    --nebula-teal: #113238;
    --ion-cyan: #5fd4c9;
    --solar-gold: #f5a94e;
    --solar-flare: #ff8a3d;
    --hairline: rgba(150, 165, 210, 0.14);
    --hairline-gold: rgba(245, 169, 78, 0.45);
    --hairline-cyan: rgba(95, 212, 201, 0.45);
    --text-primary: #eef0fb;
    --text-muted: #8891b0;
    --text-dim: #565f7d;
}

/* Global Container and Cosmic Starfield Background */
.stApp {
    background-color: var(--void) !important;
    background-image: 
        radial-gradient(1px 1px at 30px 40px, #ffffff, rgba(0,0,0,0)),
        radial-gradient(1.5px 1.5px at 70px 110px, rgba(238,240,251,0.85), rgba(0,0,0,0)),
        radial-gradient(1px 1px at 150px 60px, #8891b0, rgba(0,0,0,0)),
        radial-gradient(2px 2px at 220px 170px, rgba(95,212,201,0.7), rgba(0,0,0,0)),
        radial-gradient(1px 1px at 310px 250px, #ffffff, rgba(0,0,0,0)),
        radial-gradient(1.5px 1.5px at 380px 120px, rgba(245,169,78,0.7), rgba(0,0,0,0)),
        radial-gradient(ellipse at 88% 8%, rgba(245, 169, 78, 0.08) 0%, transparent 48%),
        radial-gradient(ellipse at 12% 16%, rgba(17, 50, 56, 0.22) 0%, transparent 52%),
        radial-gradient(ellipse at 50% 96%, rgba(36, 26, 74, 0.20) 0%, transparent 55%) !important;
    background-size: 380px 380px, 420px 420px, 320px 320px, 520px 520px, 460px 460px, 400px 400px, 100% 100%, 100% 100%, 100% 100% !important;
    background-attachment: fixed !important;
    font-family: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: var(--text-primary) !important;
}

.block-container {
    padding-top: 0.5rem !important;
    padding-bottom: 2rem !important;
    padding-left: 1.25rem !important;
    padding-right: 1.25rem !important;
    max-width: 99% !important;
}

/* Hide default streamlit decoration header */
header[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: 1px solid var(--hairline) !important;
}

/* Breadcrumb & Navigation Bar in Module View */
.aerospace-nav-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: linear-gradient(180deg, #090b1b 0%, #060714 100%);
    border: 1px solid var(--hairline);
    border-top: 2px solid var(--ion-cyan);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.05), inset 0 -1px 0 rgba(0,0,0,0.7), 0 4px 18px rgba(0,0,0,0.5);
    padding: 0.6rem 1.2rem;
    margin-bottom: 1rem;
    clip-path: polygon(0 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%);
}

.nav-return-btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: #0d1027;
    border: 1px solid var(--hairline-gold);
    color: var(--solar-gold) !important;
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    padding: 0.42rem 0.95rem;
    cursor: pointer;
    text-decoration: none !important;
    transition: all 0.25s ease;
    clip-path: polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px));
}

.nav-return-btn:hover {
    background: #14193d;
    border-color: var(--solar-gold);
    color: #ffffff !important;
    transform: translateY(-1px);
    box-shadow: 0 0 12px rgba(245, 169, 78, 0.35);
}

.nav-status-badge {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.76rem;
    color: var(--ion-cyan);
    display: flex;
    align-items: center;
    gap: 8px;
}

/* Section Mission Header */
.section-mission-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 1px solid var(--hairline);
    padding-bottom: 0.5rem;
    margin-top: 0.4rem;
    margin-bottom: 1.2rem;
}

.section-mission-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: 0.04em;
    text-shadow: 0 0 12px rgba(238, 240, 251, 0.2);
}

.section-mission-subtitle {
    font-family: 'IBM Plex Sans', sans-serif;
    font-size: 0.88rem;
    color: var(--text-muted);
    margin-top: 0.2rem;
}

.section-mission-meta {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: var(--text-dim);
    text-align: right;
}

.section-mission-meta span {
    color: var(--ion-cyan);
    font-weight: 600;
}

/* Aerospace Machined Instrument Card */
.aerospace-panel {
    background: #090b1b;
    border: 1px solid var(--hairline);
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.05), inset 0 -1px 0 rgba(0,0,0,0.7), inset 1px 0 0 rgba(255,255,255,0.025), 0 6px 20px rgba(0,0,0,0.5);
    background-image: linear-gradient(rgba(255,255,255,0.012) 1px, transparent 1px);
    background-size: 100% 4px;
    padding: 1.2rem;
    position: relative;
    clip-path: polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px));
}

/* Rack Header Bar */
.rack-header {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.76rem;
    font-weight: 600;
    color: var(--text-muted);
    letter-spacing: 0.08em;
    padding: 0.35rem 0.6rem;
    background: #0a0c22;
    border: 1px solid var(--hairline);
    border-left: 3px solid var(--ion-cyan);
    margin-bottom: 0.5rem;
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

/* Metric Units */
div[data-testid="stMetric"] {
    background: #090b1b !important;
    border: 1px solid var(--hairline) !important;
    border-top: 2px solid var(--ion-cyan) !important;
    padding: 0.6rem 0.85rem !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.04), inset 0 -1px 0 rgba(0,0,0,0.6) !important;
    clip-path: polygon(0 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%);
}

div[data-testid="stMetricLabel"] {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.72rem !important;
    color: var(--text-muted) !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
}

div[data-testid="stMetricValue"] {
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 1.45rem !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
}

/* Streamlit Buttons Restyling */
button[kind="primary"], .stButton > button {
    background: linear-gradient(180deg, #101432 0%, #090b1b 100%) !important;
    border: 1px solid var(--hairline-gold) !important;
    color: var(--solar-gold) !important;
    font-family: 'Space Grotesk', sans-serif !important;
    font-size: 0.84rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.06em !important;
    padding: 0.45rem 1.1rem !important;
    border-radius: 0px !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.05), inset 0 -1px 0 rgba(0,0,0,0.7) !important;
    clip-path: polygon(0 0, calc(100% - 6px) 0, 100% 6px, 100% 100%, 6px 100%, 0 calc(100% - 6px)) !important;
    transition: all 0.25s ease !important;
}

button[kind="primary"]:hover, .stButton > button:hover {
    background: linear-gradient(180deg, #171d47 0%, #0d1027 100%) !important;
    border-color: var(--solar-gold) !important;
    color: #ffffff !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 0 12px rgba(245, 169, 78, 0.4) !important;
}

/* Sidebar Custom Styling */
section[data-testid="stSidebar"] {
    background-color: #05060f !important;
    border-right: 1px solid var(--hairline) !important;
}

section[data-testid="stSidebar"] hr {
    border-color: var(--hairline) !important;
}

div[data-testid="stRadio"] > div {
    gap: 0.25rem !important;
}

div[data-testid="stRadio"] label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 0.82rem !important;
    color: var(--text-muted) !important;
    background: #090b1b !important;
    border: 1px solid var(--hairline) !important;
    border-left: 3px solid transparent !important;
    padding: 0.5rem 0.8rem !important;
    margin-bottom: 0.15rem !important;
    transition: all 0.2s ease !important;
    display: flex !important;
    align-items: center !important;
    cursor: pointer !important;
}

div[data-testid="stRadio"] label:hover {
    background: #0d1027 !important;
    color: var(--text-primary) !important;
    border-color: var(--hairline-gold) !important;
    border-left: 3px solid var(--solar-gold) !important;
}

/* Alert Boxes */
.mission-alert-cyan {
    background: rgba(17, 50, 56, 0.45);
    border: 1px solid rgba(95, 212, 201, 0.4);
    border-left: 3px solid var(--ion-cyan);
    padding: 0.75rem 1rem;
    font-size: 0.86rem;
    color: var(--text-primary);
    margin-bottom: 1rem;
    box-shadow: inset 0 0 10px rgba(95, 212, 201, 0.05);
}

.mission-alert-gold {
    background: rgba(45, 28, 15, 0.45);
    border: 1px solid rgba(245, 169, 78, 0.4);
    border-left: 3px solid var(--solar-gold);
    padding: 0.75rem 1rem;
    font-size: 0.86rem;
    color: var(--text-primary);
    margin-bottom: 1rem;
    box-shadow: inset 0 0 10px rgba(245, 169, 78, 0.05);
}

/* Continuity Progress Bar */
.continuity-container {
    background: #090b1b;
    border: 1px solid var(--hairline);
    padding: 0.9rem;
    margin-bottom: 1rem;
}

.continuity-bar {
    width: 100%;
    height: 14px;
    background: #05060f;
    border: 1px solid var(--hairline);
    margin: 8px 0;
    display: flex;
    overflow: hidden;
}

.seg-active {
    background: linear-gradient(90deg, #113238 0%, #5fd4c9 100%);
    height: 100%;
}

.seg-gap {
    background: #ff4d4d;
    height: 100%;
}

/* Table and DataFrame Styling */
div[data-testid="stDataFrame"] {
    border: 1px solid var(--hairline) !important;
    background: #090b1b !important;
}

/* Responsive adjustments */
@media (max-width: 768px) {
    .section-mission-header {
        flex-direction: column;
        align-items: flex-start;
        gap: 6px;
    }
    .section-mission-meta {
        text-align: left;
    }
}
</style>
"""

def apply_mission_control_theme(fig, is_heatmap=False):
    """
    Applies strict aerospace scientific theme to any Plotly figure:
    Dark void background, hairline gridlines, Space Grotesk / IBM Plex Mono typography,
    subtle cyan / solar gold accents.
    """
    font_spec = dict(
        family="IBM Plex Sans, -apple-system, BlinkMacSystemFont, sans-serif",
        size=11,
        color="#eef0fb"
    )
    title_font_spec = dict(
        family="Space Grotesk, sans-serif",
        size=14,
        color="#eef0fb"
    )
    
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(5, 6, 15, 0)",
        plot_bgcolor="#080a1d" if not is_heatmap else "rgba(5, 6, 15, 0.85)",
        font=font_spec,
        title_font=title_font_spec,
        hoverlabel=dict(
            bgcolor="#0a0c22",
            bordercolor="rgba(95, 212, 201, 0.6)",
            font=dict(family="IBM Plex Mono", size=11, color="#eef0fb")
        ),
        xaxis=dict(
            gridcolor="rgba(150, 165, 210, 0.12)",
            gridwidth=0.8,
            zerolinecolor="rgba(150, 165, 210, 0.2)",
            tickfont=dict(family="IBM Plex Mono", size=10, color="#8891b0"),
            title_font=dict(family="Space Grotesk", size=11, color="#eef0fb"),
            showline=True,
            linecolor="rgba(150, 165, 210, 0.25)",
            mirror=True
        ),
        yaxis=dict(
            gridcolor="rgba(150, 165, 210, 0.12)",
            gridwidth=0.8,
            zerolinecolor="rgba(150, 165, 210, 0.2)",
            tickfont=dict(family="IBM Plex Mono", size=10, color="#8891b0"),
            title_font=dict(family="Space Grotesk", size=11, color="#eef0fb"),
            showline=True,
            linecolor="rgba(150, 165, 210, 0.25)",
            mirror=True
        )
    )
    
    # Check for secondary y-axis
    if hasattr(fig, 'layout') and 'yaxis2' in fig.layout:
        fig.update_layout(
            yaxis2=dict(
                gridcolor="rgba(150, 165, 210, 0.08)",
                tickfont=dict(family="IBM Plex Mono", size=10, color="#f5a94e"),
                title_font=dict(family="Space Grotesk", size=11, color="#f5a94e"),
                showline=True,
                linecolor="rgba(245, 169, 78, 0.35)",
                mirror=True
            )
        )

    return fig
