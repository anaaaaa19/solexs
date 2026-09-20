"""
Stage 1: Cinematic SOLEXS Opening Experience
Full-viewport hero screen featuring:
- Dynamic user-provided video (or dark cosmic fallback)
- Space Grotesk SOLEXS identity
- IBM Plex Mono scientific metadata readouts
- Real Matter.js gravitational orbital physics overlay with interactive mouse perturbations
- Aerospace CTA button with 700-1200ms cinematic transition into Stage 2 Mission Console
"""

def render_stage1_opening_html(video_src=None, last_flare="M2.1 at 22:05:59 UTC", flux_val="2.41e-06"):
    """
    Renders the dedicated, full-screen Stage 1 cinematic opening.
    If video_src is provided (e.g. data:video/mp4;base64,...), it is used as hero background.
    Otherwise, a rich dark cosmic fallback canvas runs seamlessly.
    """
    has_video = video_src is not None and len(video_src) > 0
    video_tag = ""
    if has_video:
        video_tag = f"""
        <video id="hero-video" class="hero-video" autoplay loop muted playsinline>
            <source src="{video_src}" type="video/mp4">
        </video>
        """

    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SOLEXS | Aditya-L1 Opening</title>
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
                height: 100vh;
                overflow: hidden;
                background-color: var(--void);
                font-family: 'IBM Plex Sans', sans-serif;
                color: var(--text-primary);
                user-select: none;
            }}

            /* Video Hero Background */
            .video-container {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 1;
                overflow: hidden;
            }}

            .hero-video {{
                width: 100%;
                height: 100%;
                object-fit: cover;
                opacity: 0.88;
                transition: filter 0.8s ease, opacity 0.8s ease;
            }}

            /* Cinematic Dark & Solar Overlay */
            .cinematic-overlay {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 2;
                background: radial-gradient(circle at 50% 48%, rgba(245, 169, 78, 0.08) 0%, rgba(5, 6, 15, 0.48) 55%, rgba(5, 6, 15, 0.78) 100%);
                pointer-events: none;
                transition: background 0.8s ease;
            }}

            /* Matter.js Canvas Overlay */
            #physics-canvas {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 3;
                pointer-events: auto;
                cursor: crosshair;
            }}

            /* Stage 1 UI Layer */
            .ui-layer {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                z-index: 4;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                padding: 2.5rem 3.5rem;
                pointer-events: none;
                transition: opacity 0.7s ease, transform 0.7s ease;
            }}

            /* Top Scientific Metadata Header */
            .top-telemetry-bar {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                pointer-events: auto;
            }}

            .meta-grid {{
                display: grid;
                grid-template-columns: repeat(5, auto);
                gap: 2rem;
                background: rgba(9, 11, 27, 0.65);
                backdrop-filter: blur(8px);
                border: 1px solid var(--hairline);
                border-top: 2px solid var(--ion-cyan);
                padding: 0.7rem 1.4rem;
                clip-path: polygon(0 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%);
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.05), inset 0 -1px 0 rgba(0,0,0,0.7);
            }}

            .meta-cell {{
                display: flex;
                flex-direction: column;
                gap: 2px;
            }}

            .meta-label {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.62rem;
                color: var(--text-dim);
                letter-spacing: 0.1em;
                text-transform: uppercase;
            }}

            .meta-value {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.82rem;
                font-weight: 500;
                color: var(--ion-cyan);
                letter-spacing: 0.05em;
            }}

            .meta-value.gold {{
                color: var(--solar-gold);
            }}

            /* Center Identity */
            .center-identity {{
                display: flex;
                flex-direction: column;
                align-items: center;
                text-align: center;
                margin-top: auto;
                margin-bottom: auto;
                pointer-events: auto;
            }}

            .mission-agency-tag {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.76rem;
                font-weight: 500;
                letter-spacing: 0.28em;
                color: var(--solar-gold);
                text-transform: uppercase;
                margin-bottom: 0.6rem;
                display: flex;
                align-items: center;
                gap: 12px;
            }}

            .agency-line {{
                width: 32px;
                height: 1px;
                background: var(--solar-gold);
                opacity: 0.6;
            }}

            .main-title {{
                font-family: 'Space Grotesk', sans-serif;
                font-size: 5rem;
                font-weight: 700;
                letter-spacing: 0.18em;
                color: #ffffff;
                line-height: 1;
                margin-bottom: 0.8rem;
                text-shadow: 0 0 35px rgba(245, 169, 78, 0.3), 0 0 70px rgba(95, 212, 201, 0.15);
                position: relative;
            }}

            .title-subline {{
                font-family: 'Space Grotesk', sans-serif;
                font-size: 1.05rem;
                font-weight: 600;
                letter-spacing: 0.22em;
                color: var(--text-primary);
                text-transform: uppercase;
                margin-bottom: 0.6rem;
            }}

            .spacecraft-name {{
                font-family: 'Space Grotesk', sans-serif;
                font-size: 1.45rem;
                font-weight: 700;
                letter-spacing: 0.25em;
                color: var(--solar-gold);
                text-transform: uppercase;
                margin-bottom: 0.6rem;
                text-shadow: 0 0 16px rgba(245, 169, 78, 0.4);
            }}

            .mission-motto {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.85rem;
                font-weight: 400;
                letter-spacing: 0.16em;
                color: var(--text-muted);
                text-transform: uppercase;
                margin-bottom: 2.2rem;
            }}

            /* Primary CTA Button */
            .cta-btn {{
                position: relative;
                display: inline-flex;
                align-items: center;
                gap: 12px;
                background: linear-gradient(180deg, #f7b360 0%, #f5a94e 100%);
                color: #05060f;
                font-family: 'Space Grotesk', sans-serif;
                font-size: 0.95rem;
                font-weight: 700;
                letter-spacing: 0.12em;
                text-transform: uppercase;
                padding: 0.9rem 2.4rem;
                border: 1px solid rgba(255, 220, 150, 0.6);
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.4), inset 0 -1px 0 rgba(0,0,0,0.4), 0 0 25px rgba(245, 169, 78, 0.35);
                cursor: pointer;
                transition: all 0.3s ease;
                clip-path: polygon(0 0, calc(100% - 10px) 0, 100% 10px, 100% 100%, 10px 100%, 0 calc(100% - 10px));
                overflow: hidden;
            }}

            .cta-btn:hover {{
                transform: translateY(-2px);
                background: linear-gradient(180deg, #ffd38a 0%, #f5a94e 100%);
                box-shadow: inset 0 1px 0 rgba(255,255,255,0.6), 0 0 35px rgba(245, 169, 78, 0.6);
            }}

            .cta-btn::after {{
                content: '';
                position: absolute;
                top: 0;
                left: -120%;
                width: 60%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
                transform: skewX(-20deg);
                transition: left 0.75s ease;
            }}

            .cta-btn:hover::after {{
                left: 140%;
            }}

            .cta-hint {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.68rem;
                color: var(--text-dim);
                margin-top: 0.7rem;
                letter-spacing: 0.08em;
            }}

            /* Bottom Secondary Information */
            .bottom-telemetry-bar {{
                display: flex;
                justify-content: space-between;
                align-items: flex-end;
                border-top: 1px solid var(--hairline);
                padding-top: 1rem;
                pointer-events: auto;
            }}

            .status-block {{
                display: flex;
                gap: 2.5rem;
            }}

            .status-item {{
                display: flex;
                flex-direction: column;
                gap: 3px;
            }}

            .status-label {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.62rem;
                color: var(--text-dim);
                letter-spacing: 0.1em;
                text-transform: uppercase;
            }}

            .status-indicator {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.78rem;
                font-weight: 600;
                display: flex;
                align-items: center;
                gap: 6px;
            }}

            .dot-green {{
                width: 7px;
                height: 7px;
                border-radius: 50%;
                background: #5fd4c9;
                box-shadow: 0 0 8px #5fd4c9;
            }}

            .dot-gold {{
                width: 7px;
                height: 7px;
                border-radius: 50%;
                background: #f5a94e;
                box-shadow: 0 0 8px #f5a94e;
            }}

            .physics-badge {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.7rem;
                color: var(--text-dim);
                letter-spacing: 0.06em;
            }}

            /* Light Sweep Flash for Transition */
            .light-sweep-overlay {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: radial-gradient(circle at 50% 50%, rgba(245, 169, 78, 0.8) 0%, rgba(5, 6, 15, 0.95) 75%);
                opacity: 0;
                pointer-events: none;
                z-index: 10;
                transition: opacity 0.6s ease-in-out;
            }}

            /* Transition Darkening State */
            body.transitioning .hero-video {{
                filter: brightness(0.3) blur(4px);
            }}

            body.transitioning .ui-layer {{
                opacity: 0;
                transform: scale(0.96);
            }}

            body.transitioning .light-sweep-overlay {{
                opacity: 1;
            }}

            /* Media queries */
            @media (max-width: 900px) {{
                .main-title {{
                    font-size: 3.2rem;
                }}
                .meta-grid {{
                    grid-template-columns: repeat(2, auto);
                    gap: 1rem;
                }}
                .ui-layer {{
                    padding: 1.5rem;
                }}
            }}
        </style>
    </head>
    <body>
        <!-- Background Hero Video -->
        <div class="video-container">
            {video_tag}
        </div>

        <!-- Cinematic Solar Tint Overlay -->
        <div class="cinematic-overlay" id="cinematic-overlay"></div>

        <!-- Matter.js Interactive Solar Physics Canvas -->
        <canvas id="physics-canvas"></canvas>

        <!-- Stage 1 UI Layer -->
        <div class="ui-layer" id="ui-layer">
            <!-- Top Scientific Telemetry Bar -->
            <div class="top-telemetry-bar">
                <div class="meta-grid">
                    <div class="meta-cell">
                        <span class="meta-label">MISSION</span>
                        <span class="meta-value">ADITYA-L1</span>
                    </div>
                    <div class="meta-cell">
                        <span class="meta-label">INSTRUMENT</span>
                        <span class="meta-value">SOLEXS</span>
                    </div>
                    <div class="meta-cell">
                        <span class="meta-label">ORBIT</span>
                        <span class="meta-value">L1 HALO</span>
                    </div>
                    <div class="meta-cell">
                        <span class="meta-label">DISTANCE</span>
                        <span class="meta-value">~1.5M KM</span>
                    </div>
                    <div class="meta-cell">
                        <span class="meta-label">OBSERVATION</span>
                        <span class="meta-value gold">SOLAR X-RAY</span>
                    </div>
                </div>

                <div class="meta-cell" style="text-align: right;">
                    <span class="meta-label">LAST CATALOGUED EVENT</span>
                    <span class="meta-value gold">{last_flare}</span>
                </div>
            </div>

            <!-- Center Identity Block -->
            <div class="center-identity">
                <div class="mission-agency-tag">
                    <span class="agency-line"></span>
                    <span>ISRO · SOLAR SCIENTIFIC OBSERVATORY</span>
                    <span class="agency-line"></span>
                </div>
                <h1 class="main-title">SOLEXS</h1>
                <div class="title-subline">SOLAR LOW ENERGY X-RAY SPECTROMETER</div>
                <div class="spacecraft-name">ADITYA-L1</div>
                <div class="mission-motto">OBSERVING THE HIGH-ENERGY SUN</div>

                <button class="cta-btn" id="enter-btn" onclick="executeCinematicEnter()">
                    <span>ENTER SOLEXS CONSOLE</span>
                    <span>→</span>
                </button>
                <div class="cta-hint">PRESS [ENTER] OR CLICK TO INITIALIZE FLIGHT DECK</div>
            </div>

            <!-- Bottom Secondary Telemetry Readout -->
            <div class="bottom-telemetry-bar">
                <div class="status-block">
                    <div class="status-item">
                        <span class="status-label">MISSION SYSTEM</span>
                        <span class="status-indicator" style="color: #5fd4c9;"><span class="dot-green"></span> READY</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">TELEMETRY</span>
                        <span class="status-indicator" style="color: #5fd4c9;"><span class="dot-green"></span> NOMINAL</span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">DATA MODE</span>
                        <span class="status-indicator" style="color: #f5a94e;"><span class="dot-gold"></span> SIMULATED / HISTORICAL</span>
                    </div>
                </div>

                <div class="physics-badge">
                    MATTER.JS REAL GRAVITATIONAL PARTICLES (MOVE / DRAG / CLICK)
                </div>
            </div>
        </div>

        <!-- Light Sweep Flash Overlay -->
        <div class="light-sweep-overlay" id="sweep-overlay"></div>

        <script>
            // -----------------------------------------------------------------
            // Matter.js Real Gravitational Solar Physics Overlay
            // -----------------------------------------------------------------
            const {{ Engine, Bodies, Composite, Body, Mouse, MouseConstraint, Events, Vector }} = Matter;

            const canvas = document.getElementById('physics-canvas');
            const ctx = canvas.getContext('2d');

            function resizeCanvas() {{
                canvas.width = window.innerWidth;
                canvas.height = window.innerHeight;
            }}
            resizeCanvas();
            window.addEventListener('resize', resizeCanvas);

            const engine = Engine.create({{
                gravity: {{ x: 0, y: 0 }}
            }});

            let sunPos = {{ x: canvas.width * 0.5, y: canvas.height * 0.48 }};
            const G = 0.00045;
            const SUN_MASS = 9200;
            let speedScale = 0.58;
            let isAccelerating = false;

            const particleConfigs = [
                {{ radius: 120, size: 2.2, color: '#f5a94e', trailColor: 'rgba(245, 169, 78, ' }},
                {{ radius: 170, size: 2.6, color: '#5fd4c9', trailColor: 'rgba(95, 212, 201, ' }},
                {{ radius: 230, size: 2.4, color: '#ffd58a', trailColor: 'rgba(255, 213, 138, ' }},
                {{ radius: 300, size: 3.0, color: '#5fd4c9', trailColor: 'rgba(95, 212, 201, ' }},
                {{ radius: 380, size: 2.5, color: '#f5a94e', trailColor: 'rgba(245, 169, 78, ' }},
                {{ radius: 460, size: 2.8, color: '#ff8a3d', trailColor: 'rgba(255, 138, 61, ' }},
                {{ radius: 540, size: 2.2, color: '#5fd4c9', trailColor: 'rgba(95, 212, 201, ' }}
            ];

            let particles = [];
            let trails = [];
            const MAX_TRAIL_LENGTH = 48;

            function initParticles() {{
                particles.forEach(p => Composite.remove(engine.world, p));
                particles = [];
                trails = [];

                particleConfigs.forEach((cfg, idx) => {{
                    const angle = (idx / particleConfigs.length) * Math.PI * 2 + 0.3;
                    const px = sunPos.x + Math.cos(angle) * cfg.radius;
                    const py = sunPos.y + Math.sin(angle) * cfg.radius;

                    const body = Bodies.circle(px, py, cfg.size, {{
                        frictionAir: 0,
                        restitution: 1,
                        density: 0.001,
                        collisionFilter: {{ group: -1 }}
                    }});

                    const vMag = Math.sqrt((G * SUN_MASS) / cfg.radius) * speedScale * 45;
                    const vx = -Math.sin(angle) * vMag;
                    const vy =  Math.cos(angle) * vMag;

                    Body.setVelocity(body, {{ x: vx, y: vy }});
                    body.renderConfig = cfg;
                    body.targetRadius = cfg.radius;
                    particles.push(body);
                    trails.push([]);
                    Composite.add(engine.world, body);
                }});
            }}
            initParticles();

            // Mouse Drag Constraint
            const mouse = Mouse.create(canvas);
            const mouseConstraint = MouseConstraint.create(engine, {{
                mouse: mouse,
                constraint: {{ stiffness: 0.12, render: {{ visible: false }} }}
            }});
            Composite.add(engine.world, mouseConstraint);

            // Gravitational disturbance from cursor & Solar Center Attraction
            let mouseDisturbance = {{ x: -9999, y: -9999 }};
            window.addEventListener('mousemove', (e) => {{
                mouseDisturbance.x = e.clientX;
                mouseDisturbance.y = e.clientY;
            }});

            let rippleWaves = [];
            window.addEventListener('click', (e) => {{
                // Ignore clicks on CTA button
                if (e.target.closest('#enter-btn')) return;
                rippleWaves.push({{
                    x: e.clientX,
                    y: e.clientY,
                    radius: 2,
                    maxRadius: 180,
                    alpha: 0.8
                }});
            }});

            Events.on(engine, 'beforeUpdate', () => {{
                particles.forEach(body => {{
                    // Attraction to Sun: F = G * M * m / r^2
                    const dx = sunPos.x - body.position.x;
                    const dy = sunPos.y - body.position.y;
                    const distSq = dx * dx + dy * dy;
                    const dist = Math.sqrt(distSq);

                    if (dist > 15) {{
                        const currentG = isAccelerating ? G * 4.5 : G;
                        const forceMag = (currentG * SUN_MASS * body.mass) / distSq;
                        Body.applyForce(body, body.position, {{
                            x: (dx / dist) * forceMag,
                            y: (dy / dist) * forceMag
                        }});
                    }}

                    // Weak cursor gravitational disturbance
                    const mdx = mouseDisturbance.x - body.position.x;
                    const mdy = mouseDisturbance.y - body.position.y;
                    const mDistSq = mdx * mdx + mdy * mdy;
                    if (mDistSq < 40000 && mDistSq > 200) {{
                        const mDist = Math.sqrt(mDistSq);
                        const mForce = (0.00008 * body.mass) / mDist;
                        Body.applyForce(body, body.position, {{
                            x: (mdx / mDist) * mForce,
                            y: (mdy / mDist) * mForce
                        }});
                    }}

                    // Ripple disturbances
                    rippleWaves.forEach(w => {{
                        const rdx = body.position.x - w.x;
                        const rdy = body.position.y - w.y;
                        const rDist = Math.sqrt(rdx * rdx + rdy * rdy);
                        if (Math.abs(rDist - w.radius) < 25) {{
                            const pushMag = 0.00015 * w.alpha;
                            Body.applyForce(body, body.position, {{
                                x: (rdx / (rDist || 1)) * pushMag,
                                y: (rdy / (rDist || 1)) * pushMag
                            }});
                        }}
                    }});
                }});
            }});

            // Render loop
            function renderLoop() {{
                Engine.update(engine, 1000 / 60);

                ctx.clearRect(0, 0, canvas.width, canvas.height);

                // Draw ripples
                for (let i = rippleWaves.length - 1; i >= 0; i--) {{
                    const w = rippleWaves[i];
                    ctx.save();
                    ctx.beginPath();
                    ctx.arc(w.x, w.y, w.radius, 0, Math.PI * 2);
                    ctx.strokeStyle = `rgba(95, 212, 201, ${{w.alpha * 0.45}})`;
                    ctx.lineWidth = 1.2;
                    ctx.stroke();
                    ctx.restore();

                    w.radius += 4.5;
                    w.alpha *= 0.94;
                    if (w.radius > w.maxRadius || w.alpha < 0.01) {{
                        rippleWaves.splice(i, 1);
                    }}
                }}

                // Draw Trails (Continuous gradient)
                particles.forEach((body, idx) => {{
                    const tr = trails[idx];
                    tr.push({{ x: body.position.x, y: body.position.y }});
                    if (tr.length > MAX_TRAIL_LENGTH) tr.shift();

                    if (tr.length > 2) {{
                        for (let i = 1; i < tr.length; i++) {{
                            const progress = i / tr.length;
                            const alpha = progress * (isAccelerating ? 0.85 : 0.45);
                            ctx.beginPath();
                            ctx.moveTo(tr[i - 1].x, tr[i - 1].y);
                            ctx.lineTo(tr[i].x, tr[i].y);
                            ctx.strokeStyle = body.renderConfig.trailColor + alpha + ')';
                            ctx.lineWidth = 0.8 + progress * 0.8;
                            ctx.stroke();
                        }}
                    }}
                }});

                // Draw Orbiting Bodies
                particles.forEach(body => {{
                    ctx.beginPath();
                    ctx.arc(body.position.x, body.position.y, body.renderConfig.size, 0, Math.PI * 2);
                    ctx.fillStyle = body.renderConfig.color;
                    ctx.shadowColor = body.renderConfig.color;
                    ctx.shadowBlur = 8;
                    ctx.fill();
                    ctx.shadowBlur = 0;
                }});

                requestAnimationFrame(renderLoop);
            }}
            requestAnimationFrame(renderLoop);

            // -----------------------------------------------------------------
            // Cinematic Enter Transition Sequence (700 - 1200ms)
            // Sequence: User Clicks -> Video darkens -> Particles accelerate ->
            // Solar-gold light sweep -> UI fades -> Mission Console loads
            // -----------------------------------------------------------------
            let transitionStarted = false;
            function executeCinematicEnter() {{
                if (transitionStarted) return;
                transitionStarted = true;

                document.body.classList.add('transitioning');
                isAccelerating = true;

                // Accelerate particles
                particles.forEach(body => {{
                    const vel = body.velocity;
                    Body.setVelocity(body, {{ x: vel.x * 2.8, y: vel.y * 2.8 }});
                }});

                // Trigger navigation after 950ms transition
                setTimeout(() => {{
                    try {{
                        window.top.location.href = window.top.location.pathname + "?stage=console";
                    }} catch(e) {{
                        window.parent.postMessage({{ type: "streamlit:setComponentValue", stage: "console" }}, "*");
                    }}
                }}, 950);
            }}

            // Keyboard Shortcut for Enter
            window.addEventListener('keydown', (e) => {{
                if (e.key === 'Enter') {{
                    executeCinematicEnter();
                }}
            }});
        </script>
    </body>
    </html>
    """
    return html_content
