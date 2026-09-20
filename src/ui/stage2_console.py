"""
Stage 2: Interactive SOLEXS Mission Console
Features:
- Procedural starfield + Matter.js active solar environment with top-right glowing Sun and orbiting bodies
- Real gravitational physics, mouse disturbances, force ripples, and particle trails
- Aerospace 3x3 machined hardware module interface with chamfered edges, bevel/emboss, internal frames
- Mini-visualizations for each of the 9 scientific modules
- Active hover scans, edge lighting, mouse perspective tilt, and reactive background physics
- Live telemetry panel (Nominal status, Flux, Active Regions, Energy, Latency, Mode)
- Full keyboard shortcut support (1-9 for modules, ESC for console, Space for pause, R for reset)
- Timed 500-800ms click transitions into scientific dashboard modules
"""

def render_stage2_mission_console_html(latest_flare="M2.1 at 22:05:59 UTC", flux_str="2.41e-06"):
    """
    Renders the Stage 2 SOLEXS Mission Console HTML/JS application.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SOLEXS Mission Console</title>
        <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500;600&family=Space+Grotesk:wght@400;500;600;700&display=swap" rel="stylesheet">
        <script src="https://cdnjs.cloudflare.com/ajax/libs/matter-js/0.19.0/matter.min.js"></script>
        <style>
            :root {{
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
            }}

            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}

            html, body {{
                width: 100%;
                min-height: 100vh;
                background-color: var(--void);
                color: var(--text-primary);
                font-family: 'IBM Plex Sans', sans-serif;
                overflow-x: hidden;
                overflow-y: auto;
                user-select: none;
            }}

            /* Canvas Backgrounds (Starfield + Matter.js Physics) */
            #star-canvas, #physics-canvas {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
            }}

            #star-canvas {{
                z-index: 1;
            }}

            #physics-canvas {{
                z-index: 2;
                pointer-events: auto;
            }}

            /* Main Console Layout */
            .console-wrapper {{
                position: relative;
                z-index: 3;
                max-width: 1540px;
                margin: 0 auto;
                padding: 1.2rem 2rem 3rem 2rem;
                display: flex;
                flex-direction: column;
                gap: 1.2rem;
                pointer-events: none;
            }}

            .interactive {{
                pointer-events: auto;
            }}

            /* Top Main Header */
            .console-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid var(--hairline);
                padding-bottom: 0.85rem;
            }}

            .header-brand-box {{
                display: flex;
                flex-direction: column;
                gap: 2px;
            }}

            .header-main-title {{
                font-family: 'Space Grotesk', sans-serif;
                font-size: 1.18rem;
                font-weight: 700;
                letter-spacing: 0.08em;
                color: #ffffff;
                display: flex;
                align-items: center;
                gap: 8px;
            }}

            .brand-led {{
                width: 8px;
                height: 8px;
                border-radius: 50%;
                background: var(--solar-gold);
                box-shadow: 0 0 10px var(--solar-gold);
            }}

            .header-subline {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.74rem;
                color: var(--text-muted);
                letter-spacing: 0.06em;
            }}

            .header-right-telemetry {{
                display: flex;
                align-items: center;
                gap: 1.6rem;
                font-family: 'IBM Plex Mono', monospace;
            }}

            .orbit-coord-tag {{
                font-size: 0.74rem;
                color: var(--text-dim);
                text-align: right;
            }}

            .orbit-coord-tag span {{
                color: var(--ion-cyan);
                font-weight: 500;
            }}

            .telemetry-badge {{
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 0.74rem;
                font-weight: 600;
                padding: 0.35rem 0.75rem;
                background: rgba(95, 212, 201, 0.12);
                border: 1px solid rgba(95, 212, 201, 0.4);
                color: var(--ion-cyan);
                clip-path: polygon(0 0, calc(100% - 5px) 0, 100% 5px, 100% 100%, 5px 100%, 0 calc(100% - 5px));
            }}

            .physics-toggle-btn {{
                background: rgba(10, 12, 34, 0.8);
                border: 1px solid var(--hairline);
                color: var(--text-muted);
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.72rem;
                padding: 0.35rem 0.75rem;
                cursor: pointer;
                transition: all 0.2s ease;
            }}

            .physics-toggle-btn:hover {{
                border-color: var(--ion-cyan);
                color: #ffffff;
            }}

            /* Sub-Header & Live Telemetry Strip */
            .console-title-strip {{
                display: flex;
                justify-content: space-between;
                align-items: flex-end;
                margin-top: 0.4rem;
                margin-bottom: 0.4rem;
            }}

            .title-area {{
                display: flex;
                flex-direction: column;
                gap: 3px;
            }}

            .title-tag {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.68rem;
                color: var(--solar-gold);
                letter-spacing: 0.18em;
                text-transform: uppercase;
            }}

            .mission-console-heading {{
                font-family: 'Space Grotesk', sans-serif;
                font-size: 2.2rem;
                font-weight: 700;
                letter-spacing: 0.05em;
                color: var(--text-primary);
                line-height: 1.1;
            }}

            .console-desc {{
                font-family: 'IBM Plex Sans', sans-serif;
                font-size: 0.86rem;
                color: var(--text-muted);
                max-width: 620px;
                margin-top: 2px;
            }}

            /* Telemetry HUD Panel */
            .telemetry-rack {{
                display: grid;
                grid-template-columns: repeat(6, auto);
                gap: 1.2rem;
                background: rgba(9, 11, 27, 0.75);
                backdrop-filter: blur(8px);
                border: 1px solid var(--hairline);
                border-top: 2px solid var(--solar-gold);
                padding: 0.6rem 1.2rem;
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.05), inset 0 -1px 0 rgba(0,0,0,0.7);
                clip-path: polygon(0 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%);
            }}

            .telemetry-rack-item {{
                display: flex;
                flex-direction: column;
                gap: 2px;
            }}

            .rack-lbl {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.6rem;
                color: var(--text-dim);
                letter-spacing: 0.08em;
                text-transform: uppercase;
            }}

            .rack-val {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.78rem;
                font-weight: 600;
                color: var(--ion-cyan);
            }}

            .rack-val.gold {{
                color: var(--solar-gold);
            }}

            /* 3x3 Spacecraft Hardware Module Grid */
            .modules-grid {{
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 1.3rem;
                margin-top: 0.6rem;
                perspective: 1200px;
            }}

            /* Machined Aerospace Control Panel */
            .instrument-module {{
                position: relative;
                background: #090b1b;
                border: 1px solid var(--hairline);
                box-shadow: 
                    inset 0 1px 0 rgba(255,255,255,0.05),
                    inset 0 -1px 0 rgba(0,0,0,0.7),
                    inset 1px 0 0 rgba(255,255,255,0.025),
                    0 8px 24px rgba(0, 0, 0, 0.6);
                background-image: linear-gradient(rgba(255,255,255,0.012) 1px, transparent 1px);
                background-size: 100% 4px;
                padding: 1.15rem 1.25rem 1.15rem 1.25rem;
                cursor: pointer;
                transition: transform 0.28s cubic-bezier(0.16, 1, 0.3, 1), 
                            background-color 0.28s ease, 
                            border-color 0.28s ease,
                            box-shadow 0.28s ease;
                clip-path: polygon(
                    0 0, 
                    calc(100% - 12px) 0, 
                    100% 12px, 
                    100% 100%, 
                    12px 100%, 
                    0 calc(100% - 12px)
                );
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                min-height: 205px;
                overflow: hidden;
            }}

            /* Subtle Machined Corner Markings */
            .instrument-module::before {{
                content: '';
                position: absolute;
                top: 0;
                right: 0;
                width: 12px;
                height: 12px;
                border-left: 1px solid rgba(150, 165, 210, 0.25);
                pointer-events: none;
            }}

            .instrument-module::after {{
                content: '';
                position: absolute;
                bottom: 0;
                left: 0;
                width: 12px;
                height: 12px;
                border-right: 1px solid rgba(150, 165, 210, 0.25);
                pointer-events: none;
            }}

            /* Hover State */
            .instrument-module:hover {{
                transform: translateY(-3px) scale(1.006);
                background-color: #0d1027;
                border-color: var(--hairline-gold);
                box-shadow: 
                    inset 0 1px 0 rgba(255,255,255,0.1),
                    inset 0 -1px 0 rgba(0,0,0,0.8),
                    0 14px 32px rgba(0, 0, 0, 0.7),
                    0 0 18px rgba(245, 169, 78, 0.25);
            }}

            /* Edge Light Active on Hover */
            .edge-light {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 2px;
                background: linear-gradient(90deg, transparent, var(--solar-gold), transparent);
                opacity: 0;
                transition: opacity 0.3s ease;
                pointer-events: none;
            }}

            .instrument-module:hover .edge-light {{
                opacity: 1;
            }}

            /* Horizontal Scan Line Traveling through Module (2-3s) */
            .scan-line {{
                position: absolute;
                top: -100%;
                left: 0;
                width: 100%;
                height: 30%;
                background: linear-gradient(180deg, transparent, rgba(95, 212, 201, 0.08), transparent);
                pointer-events: none;
                opacity: 0;
            }}

            .instrument-module:hover .scan-line {{
                opacity: 1;
                animation: module-scan 2.4s infinite linear;
            }}

            @keyframes module-scan {{
                0% {{ top: -30%; }}
                100% {{ top: 130%; }}
            }}

            /* Internal Technical Panel Frame */
            .module-top-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 0.6rem;
            }}

            .module-index {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.74rem;
                font-weight: 600;
                color: var(--ion-cyan);
                letter-spacing: 0.08em;
                transition: color 0.2s ease;
                display: flex;
                align-items: center;
                gap: 6px;
            }}

            .instrument-module:hover .module-index {{
                color: #ffffff;
                text-shadow: 0 0 8px var(--ion-cyan);
            }}

            .module-led {{
                width: 6px;
                height: 6px;
                border-radius: 50%;
                background: #3a4260;
                transition: all 0.3s ease;
            }}

            .instrument-module:hover .module-led {{
                background: var(--ion-cyan);
                box-shadow: 0 0 8px var(--ion-cyan);
            }}

            .module-name {{
                font-family: 'Space Grotesk', sans-serif;
                font-size: 1.15rem;
                font-weight: 700;
                letter-spacing: 0.04em;
                color: var(--text-primary);
                margin-bottom: 0.25rem;
            }}

            .module-desc {{
                font-family: 'IBM Plex Sans', sans-serif;
                font-size: 0.78rem;
                color: var(--text-muted);
                line-height: 1.35;
                margin-bottom: 0.8rem;
            }}

            /* Mini Visualization Container */
            .mini-vis-box {{
                width: 100%;
                height: 48px;
                background: rgba(5, 7, 20, 0.75);
                border: 1px solid var(--hairline);
                position: relative;
                overflow: hidden;
                margin-bottom: 0.8rem;
            }}

            .mini-canvas {{
                width: 100%;
                height: 100%;
                display: block;
            }}

            /* Module Bottom Bar */
            .module-bottom-bar {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-top: 1px solid var(--hairline);
                padding-top: 0.55rem;
            }}

            .access-label {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.72rem;
                font-weight: 500;
                color: var(--text-dim);
                letter-spacing: 0.08em;
                display: flex;
                align-items: center;
                gap: 6px;
                transition: color 0.2s ease;
            }}

            .instrument-module:hover .access-label {{
                color: var(--solar-gold);
            }}

            .shortcut-pill {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.65rem;
                color: var(--text-dim);
                background: rgba(150, 165, 210, 0.08);
                border: 1px solid var(--hairline);
                padding: 1px 6px;
                border-radius: 2px;
            }}

            /* Keyboard Shortcuts Legend Strip */
            .shortcuts-legend-strip {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: rgba(9, 11, 27, 0.7);
                border: 1px solid var(--hairline);
                padding: 0.65rem 1.4rem;
                margin-top: 0.5rem;
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.72rem;
                color: var(--text-dim);
            }}

            .legend-item span {{
                color: var(--solar-gold);
                font-weight: 600;
            }}

            /* Activation Flash State on Click */
            .instrument-module.activating {{
                border-color: var(--solar-gold) !important;
                box-shadow: 0 0 28px rgba(245, 169, 78, 0.8) !important;
            }}

            .instrument-module.activating .edge-light {{
                opacity: 1 !important;
                background: #ffffff !important;
            }}

            /* Responsive */
            @media (max-width: 1100px) {{
                .modules-grid {{
                    grid-template-columns: repeat(2, 1fr);
                }}
                .telemetry-rack {{
                    grid-template-columns: repeat(3, auto);
                }}
            }}

            @media (max-width: 720px) {{
                .modules-grid {{
                    grid-template-columns: 1fr;
                }}
                .console-header {{
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 10px;
                }}
                .console-title-strip {{
                    flex-direction: column;
                    align-items: flex-start;
                    gap: 12px;
                }}
                .telemetry-rack {{
                    grid-template-columns: repeat(2, auto);
                }}
            }}
        </style>
    </head>
    <body>
        <!-- Procedural Starfield Canvas -->
        <canvas id="star-canvas"></canvas>

        <!-- Persistent Matter.js Solar Physics Canvas -->
        <canvas id="physics-canvas"></canvas>

        <!-- Main Mission Console Interface -->
        <div class="console-wrapper">
            <!-- Top Main Header -->
            <header class="console-header interactive">
                <div class="header-brand-box">
                    <div class="header-main-title">
                        <span class="brand-led"></span>
                        <span>SOLEXS / L1 CONSOLE</span>
                    </div>
                    <div class="header-subline">SOLAR LOW ENERGY X-RAY SPECTROMETER</div>
                </div>

                <div class="header-right-telemetry">
                    <div class="orbit-coord-tag">
                        ADITYA-L1<br>
                        <span>LAGRANGE POINT 1 · ~1.5M KM FROM EARTH</span>
                    </div>
                    <div class="telemetry-badge">
                        ● TELEMETRY NOMINAL
                    </div>
                    <button class="physics-toggle-btn" id="physics-btn" onclick="togglePhysics()">
                        PHYSICS ● ACTIVE
                    </button>
                </div>
            </header>

            <!-- Console Title & Live Telemetry Panel -->
            <div class="console-title-strip interactive">
                <div class="title-area">
                    <div class="title-tag">AEROSPACE INSTRUMENT SELECTION</div>
                    <h1 class="mission-console-heading">MISSION CONSOLE</h1>
                    <p class="console-desc">
                        Select an instrument module to explore solar X-ray observations, flare activity,
                        spectral signatures and predictive analysis.
                    </p>
                </div>

                <!-- Telemetry Panel -->
                <div class="telemetry-rack">
                    <div class="telemetry-rack-item">
                        <span class="rack-lbl">STATUS</span>
                        <span class="rack-val">● NOMINAL</span>
                    </div>
                    <div class="telemetry-rack-item">
                        <span class="rack-lbl">X-RAY FLUX</span>
                        <span class="rack-val gold">{flux_str} W/m²</span>
                    </div>
                    <div class="telemetry-rack-item">
                        <span class="rack-lbl">ACTIVE REGIONS</span>
                        <span class="rack-val">03</span>
                    </div>
                    <div class="telemetry-rack-item">
                        <span class="rack-lbl">ENERGY</span>
                        <span class="rack-val">6.4 keV</span>
                    </div>
                    <div class="telemetry-rack-item">
                        <span class="rack-lbl">DATA LATENCY</span>
                        <span class="rack-val">1.8 s</span>
                    </div>
                    <div class="telemetry-rack-item">
                        <span class="rack-lbl">LAST EVENT</span>
                        <span class="rack-val gold">{latest_flare}</span>
                    </div>
                </div>
            </div>

            <!-- 3x3 Spacecraft Hardware Module Grid -->
            <div class="modules-grid interactive" id="modules-grid">
                <!-- 01 OVERVIEW -->
                <div class="instrument-module" onclick="selectModule('01')" onmouseenter="onModuleHover('01', this)" onmouseleave="onModuleLeave(this)" data-id="01">
                    <div class="edge-light"></div>
                    <div class="scan-line"></div>
                    <div>
                        <div class="module-top-row">
                            <span class="module-index">01 / SYS</span>
                            <span class="module-led"></span>
                        </div>
                        <div class="module-name">OVERVIEW</div>
                        <div class="module-desc">Solar observation status, primary detectors & telemetry aggregate metrics.</div>
                    </div>
                    <div class="mini-vis-box">
                        <canvas class="mini-canvas" id="mini-01"></canvas>
                    </div>
                    <div class="module-bottom-bar">
                        <span class="access-label">ACCESS MODULE →</span>
                        <span class="shortcut-pill">[1]</span>
                    </div>
                </div>

                <!-- 02 LIGHT CURVE -->
                <div class="instrument-module" onclick="selectModule('02')" onmouseenter="onModuleHover('02', this)" onmouseleave="onModuleLeave(this)" data-id="02">
                    <div class="edge-light"></div>
                    <div class="scan-line"></div>
                    <div>
                        <div class="module-top-row">
                            <span class="module-index">02 / DATA</span>
                            <span class="module-led"></span>
                        </div>
                        <div class="module-name">LIGHT CURVE</div>
                        <div class="module-desc">Continuous high-resolution flux counts & tagged flare peak transients.</div>
                    </div>
                    <div class="mini-vis-box">
                        <canvas class="mini-canvas" id="mini-02"></canvas>
                    </div>
                    <div class="module-bottom-bar">
                        <span class="access-label">ACCESS MODULE →</span>
                        <span class="shortcut-pill">[2]</span>
                    </div>
                </div>

                <!-- 03 PER-DAY GRID -->
                <div class="instrument-module" onclick="selectModule('03')" onmouseenter="onModuleHover('03', this)" onmouseleave="onModuleLeave(this)" data-id="03">
                    <div class="edge-light"></div>
                    <div class="scan-line"></div>
                    <div>
                        <div class="module-top-row">
                            <span class="module-index">03 / GRID</span>
                            <span class="module-led"></span>
                        </div>
                        <div class="module-name">PER-DAY GRID</div>
                        <div class="module-desc">Multi-day small multiples for continuous solar monitoring calendar.</div>
                    </div>
                    <div class="mini-vis-box">
                        <canvas class="mini-canvas" id="mini-03"></canvas>
                    </div>
                    <div class="module-bottom-bar">
                        <span class="access-label">ACCESS MODULE →</span>
                        <span class="shortcut-pill">[3]</span>
                    </div>
                </div>

                <!-- 04 FLARE EVENT EXPLORER -->
                <div class="instrument-module" onclick="selectModule('04')" onmouseenter="onModuleHover('04', this)" onmouseleave="onModuleLeave(this)" data-id="04">
                    <div class="edge-light"></div>
                    <div class="scan-line"></div>
                    <div>
                        <div class="module-top-row">
                            <span class="module-index">04 / EVENT</span>
                            <span class="module-led"></span>
                        </div>
                        <div class="module-name">FLARE EVENT EXPLORER</div>
                        <div class="module-desc">Detailed ±15 min analysis window & candidate spectra parameters.</div>
                    </div>
                    <div class="mini-vis-box">
                        <canvas class="mini-canvas" id="mini-04"></canvas>
                    </div>
                    <div class="module-bottom-bar">
                        <span class="access-label">ACCESS MODULE →</span>
                        <span class="shortcut-pill">[4]</span>
                    </div>
                </div>

                <!-- 05 ENERGY SPECTROGRAM -->
                <div class="instrument-module" onclick="selectModule('05')" onmouseenter="onModuleHover('05', this)" onmouseleave="onModuleLeave(this)" data-id="05">
                    <div class="edge-light"></div>
                    <div class="scan-line"></div>
                    <div>
                        <div class="module-top-row">
                            <span class="module-index">05 / SPEC</span>
                            <span class="module-led"></span>
                        </div>
                        <div class="module-name">ENERGY SPECTROGRAM</div>
                        <div class="module-desc">2D SDD2 time-energy visualization across 512 spectral channels.</div>
                    </div>
                    <div class="mini-vis-box">
                        <canvas class="mini-canvas" id="mini-05"></canvas>
                    </div>
                    <div class="module-bottom-bar">
                        <span class="access-label">ACCESS MODULE →</span>
                        <span class="shortcut-pill">[5]</span>
                    </div>
                </div>

                <!-- 06 DAILY SUMMARY -->
                <div class="instrument-module" onclick="selectModule('06')" onmouseenter="onModuleHover('06', this)" onmouseleave="onModuleLeave(this)" data-id="06">
                    <div class="edge-light"></div>
                    <div class="scan-line"></div>
                    <div>
                        <div class="module-top-row">
                            <span class="module-index">06 / SUM</span>
                            <span class="module-led"></span>
                        </div>
                        <div class="module-name">DAILY SUMMARY</div>
                        <div class="module-desc">Observational statistics, peak counts, completeness and summaries.</div>
                    </div>
                    <div class="mini-vis-box">
                        <canvas class="mini-canvas" id="mini-06"></canvas>
                    </div>
                    <div class="module-bottom-bar">
                        <span class="access-label">ACCESS MODULE →</span>
                        <span class="shortcut-pill">[6]</span>
                    </div>
                </div>

                <!-- 07 DATA QUALITY & GAPS -->
                <div class="instrument-module" onclick="selectModule('07')" onmouseenter="onModuleHover('07', this)" onmouseleave="onModuleLeave(this)" data-id="07">
                    <div class="edge-light"></div>
                    <div class="scan-line"></div>
                    <div>
                        <div class="module-top-row">
                            <span class="module-index">07 / QA</span>
                            <span class="module-led"></span>
                        </div>
                        <div class="module-name">DATA QUALITY & GAPS</div>
                        <div class="module-desc">Continuity visualization, telemetry dropouts & engineering diagnostics.</div>
                    </div>
                    <div class="mini-vis-box">
                        <canvas class="mini-canvas" id="mini-07"></canvas>
                    </div>
                    <div class="module-bottom-bar">
                        <span class="access-label">ACCESS MODULE →</span>
                        <span class="shortcut-pill">[7]</span>
                    </div>
                </div>

                <!-- 08 PREDICTIVE ANALYSIS -->
                <div class="instrument-module" onclick="selectModule('08')" onmouseenter="onModuleHover('08', this)" onmouseleave="onModuleLeave(this)" data-id="08">
                    <div class="edge-light"></div>
                    <div class="scan-line"></div>
                    <div>
                        <div class="module-top-row">
                            <span class="module-index">08 / ML</span>
                            <span class="module-led"></span>
                        </div>
                        <div class="module-name">PREDICTIVE ANALYSIS</div>
                        <div class="module-desc">XGBoost 15-min lead-time probability risk classification model.</div>
                    </div>
                    <div class="mini-vis-box">
                        <canvas class="mini-canvas" id="mini-08"></canvas>
                    </div>
                    <div class="module-bottom-bar">
                        <span class="access-label">ACCESS MODULE →</span>
                        <span class="shortcut-pill">[8]</span>
                    </div>
                </div>

                <!-- 09 NOWCASTING CONSOLE -->
                <div class="instrument-module" onclick="selectModule('09')" onmouseenter="onModuleHover('09', this)" onmouseleave="onModuleLeave(this)" data-id="09">
                    <div class="edge-light"></div>
                    <div class="scan-line"></div>
                    <div>
                        <div class="module-top-row">
                            <span class="module-index">09 / NOW</span>
                            <span class="module-led"></span>
                        </div>
                        <div class="module-name">NOWCASTING CONSOLE</div>
                        <div class="module-desc">Multi-instrument flare detection pipeline & GOES ground-truth comparison.</div>
                    </div>
                    <div class="mini-vis-box">
                        <canvas class="mini-canvas" id="mini-09"></canvas>
                    </div>
                    <div class="module-bottom-bar">
                        <span class="access-label">ACCESS MODULE →</span>
                        <span class="shortcut-pill">[9]</span>
                    </div>
                </div>
            </div>

            <!-- Shortcuts Legend -->
            <div class="shortcuts-legend-strip interactive">
                <div class="legend-item">SHORTCUTS: <span>[1-9]</span> SELECT MODULE</div>
                <div class="legend-item"><span>[ESC]</span> RETURN TO CONSOLE</div>
                <div class="legend-item"><span>[SPACE]</span> PAUSE/RESUME PHYSICS</div>
                <div class="legend-item"><span>[R]</span> RESET PHYSICS</div>
                <div class="legend-item" style="color: #5fd4c9;">DATA MODE: SIMULATED / HISTORICAL</div>
            </div>
        </div>

        <script>
            // -----------------------------------------------------------------
            // 1. Procedural Starfield Canvas
            // -----------------------------------------------------------------
            const starCanvas = document.getElementById('star-canvas');
            const starCtx = starCanvas.getContext('2d');
            let stars = [];

            function resizeStarCanvas() {{
                starCanvas.width = window.innerWidth;
                starCanvas.height = window.innerHeight;
                initStars();
            }}

            function initStars() {{
                stars = [];
                const numStars = Math.floor((starCanvas.width * starCanvas.height) / 8500);
                for (let i = 0; i < numStars; i++) {{
                    stars.push({{
                        x: Math.random() * starCanvas.width,
                        y: Math.random() * starCanvas.height,
                        size: Math.random() * 1.4 + 0.3,
                        alpha: Math.random() * 0.7 + 0.2,
                        speed: (Math.random() * 0.15 + 0.04),
                        colorType: Math.random() > 0.85 ? '#5fd4c9' : (Math.random() > 0.7 ? '#f5a94e' : '#ffffff')
                    }});
                }}
            }}
            resizeStarCanvas();
            window.addEventListener('resize', resizeStarCanvas);

            function renderStars() {{
                starCtx.clearRect(0, 0, starCanvas.width, starCanvas.height);
                stars.forEach(s => {{
                    starCtx.beginPath();
                    starCtx.arc(s.x, s.y, s.size, 0, Math.PI * 2);
                    starCtx.fillStyle = s.colorType;
                    starCtx.globalAlpha = s.alpha;
                    starCtx.fill();

                    // Slow drift
                    s.y -= s.speed;
                    if (s.y < 0) {{
                        s.y = starCanvas.height;
                        s.x = Math.random() * starCanvas.width;
                    }}
                }});
                starCtx.globalAlpha = 1.0;
                requestAnimationFrame(renderStars);
            }}
            requestAnimationFrame(renderStars);

            // -----------------------------------------------------------------
            // 2. Matter.js Solar Physics Environment (Sun in Top-Right)
            // -----------------------------------------------------------------
            const {{ Engine, Bodies, Composite, Body, Mouse, MouseConstraint, Events }} = Matter;
            const physCanvas = document.getElementById('physics-canvas');
            const physCtx = physCanvas.getContext('2d');

            function resizePhysCanvas() {{
                physCanvas.width = window.innerWidth;
                physCanvas.height = window.innerHeight;
                sunPos = {{ x: physCanvas.width * 0.88, y: physCanvas.height * 0.12 }};
            }}

            const engine = Engine.create({{
                gravity: {{ x: 0, y: 0 }}
            }});

            let sunPos = {{ x: window.innerWidth * 0.88, y: window.innerHeight * 0.12 }};
            const SUN_RADIUS = 32;
            const SUN_MASS = 9000;
            const SPEED_SCALE = 0.6;
            let isPhysicsPaused = false;
            let flarePulse = 0;

            const particleConfigs = [
                {{ radius: 65,  size: 2.4, color: '#f5a94e', trailColor: 'rgba(245, 169, 78, ' }},
                {{ radius: 110, size: 2.8, color: '#5fd4c9', trailColor: 'rgba(95, 212, 201, ' }},
                {{ radius: 165, size: 2.5, color: '#ffd58a', trailColor: 'rgba(255, 213, 138, ' }},
                {{ radius: 225, size: 3.2, color: '#5fd4c9', trailColor: 'rgba(95, 212, 201, ' }},
                {{ radius: 290, size: 2.6, color: '#f5a94e', trailColor: 'rgba(245, 169, 78, ' }},
                {{ radius: 360, size: 2.4, color: '#5fd4c9', trailColor: 'rgba(95, 212, 201, ' }}
            ];

            let particles = [];
            let trails = [];
            const MAX_TRAIL_LENGTH = 48;

            function initOrbitalBodies() {{
                particles.forEach(p => Composite.remove(engine.world, p));
                particles = [];
                trails = [];

                particleConfigs.forEach((cfg, idx) => {{
                    const angle = (idx / particleConfigs.length) * Math.PI * 2 + 0.5;
                    const px = sunPos.x + Math.cos(angle) * cfg.radius;
                    const py = sunPos.y + Math.sin(angle) * cfg.radius;

                    const body = Bodies.circle(px, py, cfg.size, {{
                        frictionAir: 0,
                        restitution: 1,
                        density: 0.001,
                        collisionFilter: {{ group: -1 }}
                    }});

                    const vMag = Math.sqrt((0.00045 * SUN_MASS) / cfg.radius) * SPEED_SCALE * 45;
                    const vx = -Math.sin(angle) * vMag;
                    const vy =  Math.cos(angle) * vMag;

                    Body.setVelocity(body, {{ x: vx, y: vy }});
                    body.renderConfig = cfg;
                    body.baseRadius = cfg.radius;
                    particles.push(body);
                    trails.push([]);
                    Composite.add(engine.world, body);
                }});
            }}
            resizePhysCanvas();
            initOrbitalBodies();
            window.addEventListener('resize', () => {{
                resizePhysCanvas();
                initOrbitalBodies();
            }});

            // Mouse Drag Constraint
            const mouse = Mouse.create(physCanvas);
            const mouseConstraint = MouseConstraint.create(engine, {{
                mouse: mouse,
                constraint: {{ stiffness: 0.12, render: {{ visible: false }} }}
            }});
            Composite.add(engine.world, mouseConstraint);

            // Mouse Gravitational disturbance
            let mousePos = {{ x: -9999, y: -9999 }};
            window.addEventListener('mousemove', (e) => {{
                mousePos.x = e.clientX;
                mousePos.y = e.clientY;
            }});

            let ripples = [];
            window.addEventListener('click', (e) => {{
                if (e.target.closest('.instrument-module') || e.target.closest('button')) return;
                ripples.push({{
                    x: e.clientX,
                    y: e.clientY,
                    radius: 2,
                    maxRadius: 200,
                    alpha: 0.7
                }});
            }});

            Events.on(engine, 'beforeUpdate', () => {{
                if (isPhysicsPaused) return;

                particles.forEach(body => {{
                    const dx = sunPos.x - body.position.x;
                    const dy = sunPos.y - body.position.y;
                    const distSq = dx * dx + dy * dy;
                    const dist = Math.sqrt(distSq);

                    if (dist > 15) {{
                        const forceMag = (0.00045 * SUN_MASS * body.mass) / distSq;
                        Body.applyForce(body, body.position, {{
                            x: (dx / dist) * forceMag,
                            y: (dy / dist) * forceMag
                        }});
                    }}

                    // Mouse gravity
                    const mdx = mousePos.x - body.position.x;
                    const mdy = mousePos.y - body.position.y;
                    const mDistSq = mdx * mdx + mdy * mdy;
                    if (mDistSq < 50000 && mDistSq > 100) {{
                        const mDist = Math.sqrt(mDistSq);
                        const mForce = (0.00009 * body.mass) / mDist;
                        Body.applyForce(body, body.position, {{
                            x: (mdx / mDist) * mForce,
                            y: (mdy / mDist) * mForce
                        }});
                    }}

                    // Ripples
                    ripples.forEach(r => {{
                        const rdx = body.position.x - r.x;
                        const rdy = body.position.y - r.y;
                        const rDist = Math.sqrt(rdx * rdx + rdy * rdy);
                        if (Math.abs(rDist - r.radius) < 28) {{
                            const push = 0.00018 * r.alpha;
                            Body.applyForce(body, body.position, {{
                                x: (rdx / (rDist || 1)) * push,
                                y: (rdy / (rDist || 1)) * push
                            }});
                        }}
                    }});
                }});
            }});

            let frame = 0;
            let activeHoverLine = null; // Thin connection line to Sun on hover

            function renderPhysicsLoop() {{
                if (!isPhysicsPaused) {{
                    Engine.update(engine, 1000 / 60);
                }}
                frame++;

                physCtx.clearRect(0, 0, physCanvas.width, physCanvas.height);

                // Connecting Line to Sun on hover
                if (activeHoverLine) {{
                    physCtx.save();
                    physCtx.beginPath();
                    physCtx.moveTo(activeHoverLine.x, activeHoverLine.y);
                    physCtx.lineTo(sunPos.x, sunPos.y);
                    physCtx.strokeStyle = 'rgba(245, 169, 78, 0.18)';
                    physCtx.lineWidth = 1;
                    physCtx.setLineDash([4, 6]);
                    physCtx.stroke();
                    physCtx.restore();
                }}

                // Ripples
                for (let i = ripples.length - 1; i >= 0; i--) {{
                    const r = ripples[i];
                    physCtx.save();
                    physCtx.beginPath();
                    physCtx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
                    physCtx.strokeStyle = `rgba(95, 212, 201, ${{r.alpha * 0.4}})`;
                    physCtx.lineWidth = 1.2;
                    physCtx.stroke();
                    physCtx.restore();

                    r.radius += 3.8;
                    r.alpha *= 0.95;
                    if (r.radius > r.maxRadius || r.alpha < 0.01) {{
                        ripples.splice(i, 1);
                    }}
                }}

                // Render Sun Corona Rings
                physCtx.save();
                for (let r = 1; r <= 3; r++) {{
                    const ringR = SUN_RADIUS + r * 28 + Math.sin(frame * 0.02 + r) * 3 + flarePulse * 15;
                    physCtx.beginPath();
                    physCtx.arc(sunPos.x, sunPos.y, ringR, 0, Math.PI * 2);
                    physCtx.strokeStyle = `rgba(245, 169, 78, ${{0.08 + flarePulse * 0.15 - r * 0.02}})`;
                    physCtx.lineWidth = 1;
                    physCtx.setLineDash([3, 7]);
                    physCtx.stroke();
                }}
                physCtx.restore();

                // Trails
                particles.forEach((body, idx) => {{
                    if (!isPhysicsPaused) {{
                        const tr = trails[idx];
                        tr.push({{ x: body.position.x, y: body.position.y }});
                        if (tr.length > MAX_TRAIL_LENGTH) tr.shift();
                    }}

                    const tr = trails[idx];
                    if (tr.length > 2) {{
                        for (let i = 1; i < tr.length; i++) {{
                            const progress = i / tr.length;
                            const alpha = progress * 0.55;
                            physCtx.beginPath();
                            physCtx.moveTo(tr[i - 1].x, tr[i - 1].y);
                            physCtx.lineTo(tr[i].x, tr[i].y);
                            physCtx.strokeStyle = body.renderConfig.trailColor + alpha + ')';
                            physCtx.lineWidth = 0.8 + progress * 0.9;
                            physCtx.stroke();
                        }}
                    }}
                }});

                // Particles
                particles.forEach(body => {{
                    physCtx.beginPath();
                    physCtx.arc(body.position.x, body.position.y, body.renderConfig.size, 0, Math.PI * 2);
                    physCtx.fillStyle = body.renderConfig.color;
                    physCtx.shadowColor = body.renderConfig.color;
                    physCtx.shadowBlur = 8;
                    physCtx.fill();
                    physCtx.shadowBlur = 0;
                }});

                // Sun Outer Radial Glow
                physCtx.save();
                const sunGlow = physCtx.createRadialGradient(
                    sunPos.x, sunPos.y, SUN_RADIUS * 0.2,
                    sunPos.x, sunPos.y, SUN_RADIUS * (3.2 + flarePulse * 1.5)
                );
                sunGlow.addColorStop(0, 'rgba(255, 213, 138, 0.9)');
                sunGlow.addColorStop(0.35, 'rgba(245, 169, 78, 0.45)');
                sunGlow.addColorStop(0.7, 'rgba(255, 138, 61, 0.12)');
                sunGlow.addColorStop(1, 'rgba(5, 6, 15, 0)');

                physCtx.fillStyle = sunGlow;
                physCtx.beginPath();
                physCtx.arc(sunPos.x, sunPos.y, SUN_RADIUS * (3.2 + flarePulse * 1.5), 0, Math.PI * 2);
                physCtx.fill();

                // Sun Core
                const sunCore = physCtx.createRadialGradient(
                    sunPos.x - SUN_RADIUS * 0.25, sunPos.y - SUN_RADIUS * 0.25, 2,
                    sunPos.x, sunPos.y, SUN_RADIUS
                );
                sunCore.addColorStop(0, '#ffffff');
                sunCore.addColorStop(0.2, '#ffd58a');
                sunCore.addColorStop(0.65, '#f5a94e');
                sunCore.addColorStop(1, '#ff8a3d');

                physCtx.fillStyle = sunCore;
                physCtx.beginPath();
                physCtx.arc(sunPos.x, sunPos.y, SUN_RADIUS, 0, Math.PI * 2);
                physCtx.fill();
                physCtx.restore();

                if (flarePulse > 0) {{
                    flarePulse *= 0.95;
                    if (flarePulse < 0.01) flarePulse = 0;
                }}

                requestAnimationFrame(renderPhysicsLoop);
            }}
            requestAnimationFrame(renderPhysicsLoop);

            // -----------------------------------------------------------------
            // 3. Mini Visualizations for All 9 Modules
            // -----------------------------------------------------------------
            function drawMiniVisuals() {{
                // 01 OVERVIEW: Mini Sun + orbital particle
                const c1 = document.getElementById('mini-01');
                if (c1) {{
                    const ctx1 = c1.getContext('2d');
                    c1.width = c1.clientWidth; c1.height = c1.clientHeight;
                    ctx1.clearRect(0,0,c1.width,c1.height);
                    const cx = c1.width/2, cy = c1.height/2;
                    ctx1.beginPath(); ctx1.arc(cx, cy, 6, 0, Math.PI*2);
                    ctx1.fillStyle = '#f5a94e'; ctx1.shadowColor='#f5a94e'; ctx1.shadowBlur=8; ctx1.fill();
                    ctx1.shadowBlur=0;
                    ctx1.beginPath(); ctx1.arc(cx, cy, 16, 0, Math.PI*2);
                    ctx1.strokeStyle = 'rgba(95, 212, 201, 0.4)'; ctx1.stroke();
                    ctx1.beginPath(); ctx1.arc(cx+16, cy, 2.5, 0, Math.PI*2);
                    ctx1.fillStyle = '#5fd4c9'; ctx1.fill();
                }}

                // 02 LIGHT CURVE: Mini waveform
                const c2 = document.getElementById('mini-02');
                if (c2) {{
                    const ctx2 = c2.getContext('2d');
                    c2.width = c2.clientWidth; c2.height = c2.clientHeight;
                    ctx2.clearRect(0,0,c2.width,c2.height);
                    ctx2.beginPath();
                    ctx2.moveTo(8, c2.height*0.65);
                    for (let x = 8; x < c2.width - 8; x += 4) {{
                        const isPeak = (x > c2.width*0.45 && x < c2.width*0.65);
                        const y = isPeak ? c2.height*0.25 - Math.sin((x - c2.width*0.45)/10)*12 : c2.height*0.65 + Math.sin(x*0.18)*3;
                        ctx2.lineTo(x, y);
                    }}
                    ctx2.strokeStyle = '#5fd4c9'; ctx2.lineWidth = 1.6; ctx2.stroke();
                }}

                // 03 PER-DAY GRID: Mini activity grid
                const c3 = document.getElementById('mini-03');
                if (c3) {{
                    const ctx3 = c3.getContext('2d');
                    c3.width = c3.clientWidth; c3.height = c3.clientHeight;
                    ctx3.clearRect(0,0,c3.width,c3.height);
                    const cols = 8, rows = 3, cellW = 10, cellH = 10, gap = 4;
                    const startX = (c3.width - (cols*(cellW+gap))) / 2;
                    const startY = (c3.height - (rows*(cellH+gap))) / 2;
                    for (let r=0; r<rows; r++) {{
                        for (let c=0; c<cols; c++) {{
                            const intensity = (r*cols+c)%5 === 0 ? '#f5a94e' : ((r*cols+c)%3 === 0 ? '#5fd4c9' : 'rgba(150, 165, 210, 0.15)');
                            ctx3.fillStyle = intensity;
                            ctx3.fillRect(startX + c*(cellW+gap), startY + r*(cellH+gap), cellW, cellH);
                        }}
                    }}
                }}

                // 04 FLARE EVENT EXPLORER: Mini flare pulse
                const c4 = document.getElementById('mini-04');
                if (c4) {{
                    const ctx4 = c4.getContext('2d');
                    c4.width = c4.clientWidth; c4.height = c4.clientHeight;
                    ctx4.clearRect(0,0,c4.width,c4.height);
                    const cx = c4.width/2, cy = c4.height/2;
                    ctx4.beginPath(); ctx4.arc(cx, cy, 14, 0, Math.PI*2);
                    ctx4.strokeStyle = 'rgba(255, 138, 61, 0.4)'; ctx4.lineWidth = 1; ctx4.stroke();
                    ctx4.beginPath(); ctx4.arc(cx, cy, 6, 0, Math.PI*2);
                    ctx4.fillStyle = '#ff8a3d'; ctx4.shadowColor = '#ff8a3d'; ctx4.shadowBlur = 10; ctx4.fill();
                    ctx4.shadowBlur = 0;
                }}

                // 05 ENERGY SPECTROGRAM: Mini horizontal energy bands
                const c5 = document.getElementById('mini-05');
                if (c5) {{
                    const ctx5 = c5.getContext('2d');
                    c5.width = c5.clientWidth; c5.height = c5.clientHeight;
                    ctx5.clearRect(0,0,c5.width,c5.height);
                    const bands = [
                        {{ y: 8, col: 'rgba(95, 212, 201, 0.4)' }},
                        {{ y: 16, col: 'rgba(95, 212, 201, 0.8)' }},
                        {{ y: 24, col: 'rgba(245, 169, 78, 0.9)' }},
                        {{ y: 32, col: 'rgba(255, 138, 61, 0.7)' }},
                        {{ y: 40, col: 'rgba(36, 26, 74, 0.5)' }}
                    ];
                    bands.forEach(b => {{
                        ctx5.fillStyle = b.col;
                        ctx5.fillRect(8, b.y, c5.width - 16, 4);
                    }});
                }}

                // 06 DAILY SUMMARY: Mini telemetry bars
                const c6 = document.getElementById('mini-06');
                if (c6) {{
                    const ctx6 = c6.getContext('2d');
                    c6.width = c6.clientWidth; c6.height = c6.clientHeight;
                    ctx6.clearRect(0,0,c6.width,c6.height);
                    const bars = [14, 22, 18, 38, 28, 19, 32, 12, 26];
                    const bw = 8, gap = 5;
                    const sx = (c6.width - (bars.length*(bw+gap))) / 2;
                    bars.forEach((h, i) => {{
                        ctx6.fillStyle = h > 30 ? '#f5a94e' : '#5fd4c9';
                        ctx6.fillRect(sx + i*(bw+gap), c6.height - h - 4, bw, h);
                    }});
                }}

                // 07 DATA QUALITY: Signal line with gap
                const c7 = document.getElementById('mini-07');
                if (c7) {{
                    const ctx7 = c7.getContext('2d');
                    c7.width = c7.clientWidth; c7.height = c7.clientHeight;
                    ctx7.clearRect(0,0,c7.width,c7.height);
                    ctx7.strokeStyle = '#5fd4c9'; ctx7.lineWidth = 2;
                    ctx7.beginPath(); ctx7.moveTo(12, c7.height/2); ctx7.lineTo(c7.width*0.4, c7.height/2); ctx7.stroke();
                    ctx7.strokeStyle = '#ff4d4d'; ctx7.setLineDash([2, 3]);
                    ctx7.beginPath(); ctx7.moveTo(c7.width*0.4, c7.height/2); ctx7.lineTo(c7.width*0.6, c7.height/2); ctx7.stroke();
                    ctx7.setLineDash([]);
                    ctx7.strokeStyle = '#5fd4c9';
                    ctx7.beginPath(); ctx7.moveTo(c7.width*0.6, c7.height/2); ctx7.lineTo(c7.width - 12, c7.height/2); ctx7.stroke();
                }}

                // 08 PREDICTIVE ANALYSIS: Probability curve
                const c8 = document.getElementById('mini-08');
                if (c8) {{
                    const ctx8 = c8.getContext('2d');
                    c8.width = c8.clientWidth; c8.height = c8.clientHeight;
                    ctx8.clearRect(0,0,c8.width,c8.height);
                    ctx8.beginPath();
                    ctx8.moveTo(10, c8.height*0.8);
                    ctx8.bezierCurveTo(c8.width*0.35, c8.height*0.8, c8.width*0.5, c8.height*0.2, c8.width - 10, c8.height*0.2);
                    ctx8.strokeStyle = '#ff8a3d'; ctx8.lineWidth = 1.8; ctx8.stroke();
                }}

                // 09 NOWCASTING CONSOLE: Moving observation indicator
                const c9 = document.getElementById('mini-09');
                if (c9) {{
                    const ctx9 = c9.getContext('2d');
                    c9.width = c9.clientWidth; c9.height = c9.clientHeight;
                    ctx9.clearRect(0,0,c9.width,c9.height);
                    ctx9.strokeStyle = 'rgba(150, 165, 210, 0.2)'; ctx9.lineWidth = 1;
                    ctx9.beginPath(); ctx9.moveTo(8, c9.height/2); ctx9.lineTo(c9.width - 8, c9.height/2); ctx9.stroke();
                    const markerX = c9.width*0.62;
                    ctx9.beginPath(); ctx9.arc(markerX, c9.height/2, 5, 0, Math.PI*2);
                    ctx9.fillStyle = '#f5a94e'; ctx9.shadowColor = '#f5a94e'; ctx9.shadowBlur = 8; ctx9.fill();
                    ctx9.shadowBlur = 0;
                }}
            }}
            setTimeout(drawMiniVisuals, 100);
            window.addEventListener('resize', drawMiniVisuals);

            // -----------------------------------------------------------------
            // 4. Module Hover Perspective Tilt & Physics Reactions
            // -----------------------------------------------------------------
            document.querySelectorAll('.instrument-module').forEach(mod => {{
                mod.addEventListener('mousemove', (e) => {{
                    const rect = mod.getBoundingClientRect();
                    const x = e.clientX - rect.left - rect.width / 2;
                    const y = e.clientY - rect.top - rect.height / 2;
                    const rotX = -(y / (rect.height / 2)) * 1.2;
                    const rotY = (x / (rect.width / 2)) * 1.2;
                    mod.style.transform = `translateY(-3px) rotateX(${{rotX}}deg) rotateY(${{rotY}}deg)`;
                }});
            }});

            function onModuleHover(modId, el) {{
                const rect = el.getBoundingClientRect();
                activeHoverLine = {{
                    x: rect.left + rect.width / 2,
                    y: rect.top + rect.height / 2
                }};

                // Reaction in Matter.js physics environment based on module
                switch(modId) {{
                    case '01': // Overview: accelerated orbital activity
                        particles.forEach(b => Body.setVelocity(b, {{ x: b.velocity.x * 1.25, y: b.velocity.y * 1.25 }}));
                        break;
                    case '02': // Light curve: waveform ripple disturbance
                        ripples.push({{ x: sunPos.x, y: sunPos.y, radius: 4, maxRadius: 180, alpha: 0.7 }});
                        break;
                    case '04': // Flare explorer: small solar pulse
                        flarePulse = 0.8;
                        break;
                    case '05': // Spectrogram: horizontal particle perturbation
                        particles.forEach(b => Body.applyForce(b, b.position, {{ x: (Math.random()-0.5)*0.0003, y: 0 }}));
                        break;
                    case '08': // Predictive: forward push along trajectory
                        particles.forEach(b => Body.applyForce(b, b.position, {{ x: b.velocity.x * 0.00008, y: b.velocity.y * 0.00008 }}));
                        break;
                    case '09': // Nowcasting: subtle acceleration in observation direction
                        flarePulse = 0.4;
                        particles.forEach(b => Body.setVelocity(b, {{ x: b.velocity.x * 1.15, y: b.velocity.y * 1.15 }}));
                        break;
                }}
            }}

            function onModuleLeave(el) {{
                activeHoverLine = null;
                el.style.transform = '';
            }}

            // -----------------------------------------------------------------
            // 5. Module Click Activation & Transition (500 - 800ms)
            // -----------------------------------------------------------------
            let isNavigating = false;
            function selectModule(modId) {{
                if (isNavigating) return;
                isNavigating = true;

                const modEl = document.querySelector(`.instrument-module[data-id="${{modId}}"]`);
                if (modEl) {{
                    modEl.classList.add('activating');
                }}

                setTimeout(() => {{
                    try {{
                        window.top.location.href = window.top.location.pathname + "?stage=module&module=" + modId;
                    }} catch(e) {{
                        window.parent.postMessage({{ type: "streamlit:setComponentValue", stage: "module", module: modId }}, "*");
                    }}
                }}, 550);
            }}

            // -----------------------------------------------------------------
            // 6. Physics Active / Pause Control & Keyboard Shortcuts
            // -----------------------------------------------------------------
            function togglePhysics() {{
                isPhysicsPaused = !isPhysicsPaused;
                const btn = document.getElementById('physics-btn');
                btn.innerText = isPhysicsPaused ? 'PHYSICS ○ PAUSED' : 'PHYSICS ● ACTIVE';
                btn.style.color = isPhysicsPaused ? 'var(--solar-gold)' : 'var(--text-muted)';
            }}

            window.addEventListener('keydown', (e) => {{
                const key = e.key;
                if (key >= '1' && key <= '9') {{
                    const modPad = key.padStart(2, '0');
                    selectModule(modPad);
                }} else if (key === ' ' || e.code === 'Space') {{
                    e.preventDefault();
                    togglePhysics();
                }} else if (key.toLowerCase() === 'r') {{
                    initOrbitalBodies();
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html_content
