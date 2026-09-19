"""
Solar Physics & Telemetry Component using Matter.js
Renders:
- Central Sun with corona rings and glow
- 5-6 observation/data particles with real inverse-square gravity
- Draggable physics with Matter.Mouse & Matter.MouseConstraint
- 48-point smooth fading orbital trails
- Solar flare pulse and wave interaction
- Live telemetry instrument panel
"""

def render_solar_physics_html(flare_active=False, last_flare_str="M2.1 at 22:05:59 UTC", flux_str="2.41e-06"):
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Mono:wght@400;500;600&display=swap');
            
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            
            body {{
                background-color: #05060f;
                color: #eef0fb;
                font-family: 'IBM Plex Mono', monospace;
                overflow: hidden;
                width: 100%;
                height: 420px;
                display: flex;
            }}
            
            .console-grid {{
                display: flex;
                width: 100%;
                height: 100%;
                background: #0a0c22;
                border: 1px solid rgba(150, 165, 210, 0.14);
                border-radius: 2px;
                overflow: hidden;
            }}
            
            /* Left Canvas Area */
            .canvas-container {{
                position: relative;
                flex: 1;
                height: 100%;
                background: radial-gradient(circle at 50% 50%, #0d1136 0%, #05060f 75%);
                overflow: hidden;
            }}
            
            #matter-canvas {{
                width: 100%;
                height: 100%;
                display: block;
            }}
            
            .canvas-overlay-header {{
                position: absolute;
                top: 12px;
                left: 14px;
                pointer-events: none;
            }}
            
            .canvas-title {{
                font-family: 'Space Grotesk', sans-serif;
                font-size: 0.88rem;
                font-weight: 700;
                color: #eef0fb;
                letter-spacing: 0.06em;
            }}
            
            .canvas-desc {{
                font-size: 0.65rem;
                color: #8891b0;
                margin-top: 2px;
            }}
            
            .canvas-controls {{
                position: absolute;
                bottom: 10px;
                left: 12px;
                display: flex;
                gap: 6px;
                z-index: 10;
            }}
            
            .ctrl-btn {{
                background: rgba(10, 12, 34, 0.85);
                border: 1px solid rgba(150, 165, 210, 0.25);
                color: #8891b0;
                padding: 4px 8px;
                font-size: 0.65rem;
                font-family: 'IBM Plex Mono', monospace;
                border-radius: 2px;
                cursor: pointer;
                transition: all 0.2s;
            }}
            
            .ctrl-btn:hover {{
                border-color: #5fd4c9;
                color: #5fd4c9;
                background: #111538;
            }}
            
            .ctrl-btn.flare-btn {{
                border-color: rgba(245, 169, 78, 0.4);
                color: #f5a94e;
            }}
            
            .ctrl-btn.flare-btn:hover {{
                background: rgba(245, 169, 78, 0.15);
                border-color: #f5a94e;
                color: #ffd58a;
            }}
            
            /* Right Telemetry Column */
            .telemetry-col {{
                width: 270px;
                border-left: 1px solid rgba(150, 165, 210, 0.14);
                background: #080a1c;
                display: flex;
                flex-direction: column;
                padding: 14px 16px;
                justify-content: space-between;
            }}
            
            .telemetry-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid rgba(150, 165, 210, 0.12);
                padding-bottom: 8px;
            }}
            
            .telemetry-tag {{
                font-family: 'Space Grotesk', sans-serif;
                font-size: 0.82rem;
                font-weight: 700;
                color: #eef0fb;
                letter-spacing: 0.05em;
            }}
            
            .status-indicator {{
                display: flex;
                align-items: center;
                gap: 5px;
                font-size: 0.68rem;
                color: #5fd4c9;
            }}
            
            .status-dot {{
                width: 7px;
                height: 7px;
                border-radius: 50%;
                background: #5fd4c9;
                box-shadow: 0 0 8px #5fd4c9;
                animation: pulse-nominal 2s infinite ease-in-out;
            }}
            
            @keyframes pulse-nominal {{
                0%, 100% {{ opacity: 1; }}
                50% {{ opacity: 0.4; }}
            }}
            
            .readout-group {{
                display: flex;
                flex-direction: column;
                gap: 10px;
                margin: 10px 0;
            }}
            
            .readout-item {{
                display: flex;
                flex-direction: column;
            }}
            
            .readout-label {{
                font-size: 0.65rem;
                color: #565f7d;
                letter-spacing: 0.06em;
                text-transform: uppercase;
            }}
            
            .readout-val {{
                font-family: 'Space Grotesk', sans-serif;
                font-size: 1.05rem;
                font-weight: 600;
                color: #eef0fb;
            }}
            
            .readout-val.cyan {{
                color: #5fd4c9;
            }}
            
            .readout-val.gold {{
                color: #f5a94e;
            }}
            
            .telemetry-footer {{
                border-top: 1px solid rgba(150, 165, 210, 0.12);
                padding-top: 8px;
                font-size: 0.65rem;
                color: #8891b0;
                display: flex;
                flex-direction: column;
                gap: 3px;
            }}
            
            .telemetry-footer-item {{
                display: flex;
                justify-content: space-between;
            }}
            
            .telemetry-footer-item span:last-child {{
                color: #5fd4c9;
            }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/matter-js/0.19.0/matter.min.js"></script>
    </head>
    <body>
        <div class="console-grid">
            <!-- Canvas Container -->
            <div class="canvas-container" id="canvas-wrapper">
                <div class="canvas-overlay-header">
                    <div class="canvas-title">SOLAR CORE & OBSERVATION ORBITS</div>
                    <div class="canvas-desc">Matter.js Inverse-Square Gravity · Drag Particles to Perturb</div>
                </div>
                
                <canvas id="matter-canvas"></canvas>
                
                <div class="canvas-controls">
                    <button class="ctrl-btn flare-btn" id="btn-flare">⚡ TRIGGER FLARE</button>
                    <button class="ctrl-btn" id="btn-reset">RESET ORBITS</button>
                    <button class="ctrl-btn" id="btn-pause">PAUSE</button>
                </div>
            </div>
            
            <!-- Live Telemetry Side Panel -->
            <div class="telemetry-col">
                <div class="telemetry-header">
                    <div class="telemetry-tag">LIVE TELEMETRY</div>
                    <div class="status-indicator" id="status-box">
                        <span class="status-dot" id="status-dot"></span>
                        <span id="status-text">NOMINAL</span>
                    </div>
                </div>
                
                <div class="readout-group">
                    <div class="readout-item">
                        <span class="readout-label">X-Ray Flux (Empirical)</span>
                        <span class="readout-val gold" id="flux-val">{flux_str} W/m²</span>
                    </div>
                    <div class="readout-item">
                        <span class="readout-label">Active Flare Region</span>
                        <span class="readout-val cyan" id="region-val">AR 3738</span>
                    </div>
                    <div class="readout-item">
                        <span class="readout-label">Spectrometer Band</span>
                        <span class="readout-val">1.2 - 25.0 keV</span>
                    </div>
                    <div class="readout-item">
                        <span class="readout-label">Last Catalogued Flare</span>
                        <span class="readout-val gold" style="font-size: 0.85rem;" id="flare-event">{last_flare_str}</span>
                    </div>
                </div>
                
                <div class="telemetry-footer">
                    <div class="telemetry-footer-item">
                        <span>DATA LATENCY</span>
                        <span>1.8 s</span>
                    </div>
                    <div class="telemetry-footer-item">
                        <span>TELEMETRY CADENCE</span>
                        <span>1.0 s</span>
                    </div>
                    <div class="telemetry-footer-item">
                        <span>DATA MODE</span>
                        <span style="color: #f5a94e;">HISTORICAL / ARCHIVE</span>
                    </div>
                </div>
            </div>
        </div>

        <script>
            // Matter.js Setup
            const {{ Engine, Render, Runner, Bodies, Composite, Body, Vector, Mouse, MouseConstraint, Events }} = Matter;
            
            const wrapper = document.getElementById('canvas-wrapper');
            const canvas = document.getElementById('matter-canvas');
            const ctx = canvas.getContext('2d');
            
            let width = wrapper.clientWidth;
            let height = wrapper.clientHeight;
            canvas.width = width;
            canvas.height = height;
            
            const engine = Engine.create({{
                gravity: {{ x: 0, y: 0 }}
            }});
            
            let sunPos = {{ x: width / 2, y: height / 2 }};
            const SUN_RADIUS = 32;
            const SUN_MASS = 9200;
            const SPEED_SCALE = 0.58;
            
            // Orbiting Observation Bodies configuration
            const particleConfigs = [
                {{ radius: 72,  size: 3.5, color: '#f5a94e', trailColor: 'rgba(245, 169, 78, ' }},
                {{ radius: 108, size: 4.2, color: '#5fd4c9', trailColor: 'rgba(95, 212, 201, ' }},
                {{ radius: 146, size: 3.8, color: '#ffd58a', trailColor: 'rgba(255, 213, 138, ' }},
                {{ radius: 184, size: 4.8, color: '#99ece5', trailColor: 'rgba(153, 236, 229, ' }},
                {{ radius: 228, size: 3.6, color: '#f5a94e', trailColor: 'rgba(245, 169, 78, ' }},
                {{ radius: 268, size: 4.0, color: '#5fd4c9', trailColor: 'rgba(95, 212, 201, ' }}
            ];
            
            let particles = [];
            let trails = [];
            const MAX_TRAIL_LENGTH = 48;
            
            function createOrbitingBodies() {{
                // Remove existing particles
                particles.forEach(p => Composite.remove(engine.world, p));
                particles = [];
                trails = [];
                
                particleConfigs.forEach((cfg, idx) => {{
                    // Evenly spaced phase angle
                    const angle = (idx / particleConfigs.length) * Math.PI * 2 + Math.PI / 6;
                    const px = sunPos.x + Math.cos(angle) * cfg.radius;
                    const py = sunPos.y + Math.sin(angle) * cfg.radius;
                    
                    const body = Bodies.circle(px, py, cfg.size, {{
                        frictionAir: 0,
                        restitution: 1,
                        collisionFilter: {{ group: -1 }},
                        density: 0.001
                    }});
                    
                    // Circular orbit speed: v = sqrt(G * M / r)
                    const vMag = Math.sqrt((SUN_MASS) / cfg.radius) * SPEED_SCALE;
                    const vx = -Math.sin(angle) * vMag;
                    const vy =  Math.cos(angle) * vMag;
                    
                    Body.setVelocity(body, {{ x: vx, y: vy }});
                    
                    body.renderConfig = cfg;
                    particles.push(body);
                    trails.push([]);
                    Composite.add(engine.world, body);
                }});
            }}
            
            createOrbitingBodies();
            
            // Mouse Drag Constraint
            const mouse = Mouse.create(canvas);
            const mouseConstraint = MouseConstraint.create(engine, {{
                mouse: mouse,
                constraint: {{
                    stiffness: 0.12,
                    render: {{ visible: false }}
                }}
            }});
            Composite.add(engine.world, mouseConstraint);
            
            // Flare Animation State
            let flareIntensity = 0;
            let flarePulse = 0;
            let flareWaveRadius = 0;
            let isPaused = false;
            
            // Engine update hook: apply gravitational force toward Sun (F = G * M / r^2)
            Events.on(engine, 'beforeUpdate', () => {{
                if (isPaused) return;
                
                particles.forEach(body => {{
                    const dx = sunPos.x - body.position.x;
                    const dy = sunPos.y - body.position.y;
                    const distSq = dx * dx + dy * dy;
                    const dist = Math.sqrt(distSq);
                    
                    if (dist > 10) {{
                        const forceMag = (SUN_MASS * body.mass) / distSq * 0.00032;
                        Body.applyForce(body, body.position, {{
                            x: (dx / dist) * forceMag,
                            y: (dy / dist) * forceMag
                        }});
                    }}
                }});
            }});
            
            // Custom Animation Loop
            let frameCount = 0;
            function renderLoop() {{
                if (!isPaused) {{
                    Engine.update(engine, 1000 / 60);
                }}
                
                frameCount++;
                
                // Clear Canvas
                ctx.clearRect(0, 0, width, height);
                
                // Draw Corona Rings
                ctx.save();
                for (let r = 1; r <= 3; r++) {{
                    const ringRadius = SUN_RADIUS + r * 28 + Math.sin(frameCount * 0.02 + r) * 3 + flareIntensity * 12;
                    ctx.beginPath();
                    ctx.arc(sunPos.x, sunPos.y, ringRadius, 0, Math.PI * 2);
                    ctx.strokeStyle = `rgba(245, 169, 78, ${{0.04 + flareIntensity * 0.12 - r * 0.01}})`;
                    ctx.lineWidth = 1;
                    ctx.setLineDash([4, 8]);
                    ctx.stroke();
                }}
                ctx.restore();
                
                // Flare Radial Wave
                if (flareWaveRadius > 0) {{
                    ctx.save();
                    ctx.beginPath();
                    ctx.arc(sunPos.x, sunPos.y, flareWaveRadius, 0, Math.PI * 2);
                    ctx.strokeStyle = `rgba(255, 138, 61, ${{Math.max(0, 1 - flareWaveRadius / (width * 0.6)) * 0.7}})`;
                    ctx.lineWidth = 2.5;
                    ctx.stroke();
                    ctx.restore();
                    
                    flareWaveRadius += 4.5;
                    if (flareWaveRadius > width * 0.7) {{
                        flareWaveRadius = 0;
                    }}
                }}
                
                // Draw Trails
                particles.forEach((body, idx) => {{
                    const tr = trails[idx];
                    if (!isPaused) {{
                        tr.push({{ x: body.position.x, y: body.position.y }});
                        if (tr.length > MAX_TRAIL_LENGTH) {{
                            tr.shift();
                        }}
                    }}
                    
                    if (tr.length > 2) {{
                        for (let i = 1; i < tr.length; i++) {{
                            const alpha = (i / tr.length) * 0.55;
                            ctx.beginPath();
                            ctx.moveTo(tr[i - 1].x, tr[i - 1].y);
                            ctx.lineTo(tr[i].x, tr[i].y);
                            ctx.strokeStyle = body.renderConfig.trailColor + alpha + ')';
                            ctx.lineWidth = 1.2;
                            ctx.stroke();
                        }}
                    }}
                }});
                
                // Draw Orbiting Particles
                particles.forEach(body => {{
                    ctx.beginPath();
                    ctx.arc(body.position.x, body.position.y, body.renderConfig.size, 0, Math.PI * 2);
                    ctx.fillStyle = body.renderConfig.color;
                    ctx.shadowColor = body.renderConfig.color;
                    ctx.shadowBlur = 8;
                    ctx.fill();
                    ctx.shadowBlur = 0;
                }});
                
                // Draw Central Sun with Gradient Glow
                ctx.save();
                const sunGlow = ctx.createRadialGradient(
                    sunPos.x, sunPos.y, SUN_RADIUS * 0.3,
                    sunPos.x, sunPos.y, SUN_RADIUS * (2.8 + flareIntensity * 1.5)
                );
                sunGlow.addColorStop(0, 'rgba(255, 213, 138, 0.9)');
                sunGlow.addColorStop(0.35, 'rgba(245, 169, 78, 0.4)');
                sunGlow.addColorStop(0.7, 'rgba(255, 138, 61, 0.15)');
                sunGlow.addColorStop(1, 'rgba(5, 6, 15, 0)');
                
                ctx.fillStyle = sunGlow;
                ctx.beginPath();
                ctx.arc(sunPos.x, sunPos.y, SUN_RADIUS * (2.8 + flareIntensity * 1.5), 0, Math.PI * 2);
                ctx.fill();
                
                // Core Sphere
                const sunCore = ctx.createRadialGradient(
                    sunPos.x - SUN_RADIUS * 0.25, sunPos.y - SUN_RADIUS * 0.25, 2,
                    sunPos.x, sunPos.y, SUN_RADIUS
                );
                sunCore.addColorStop(0, '#fff2c2');
                sunCore.addColorStop(0.45, '#ffd58a');
                sunCore.addColorStop(0.8, '#f5a94e');
                sunCore.addColorStop(1, '#ff8a3d');
                
                ctx.fillStyle = sunCore;
                ctx.beginPath();
                ctx.arc(sunPos.x, sunPos.y, SUN_RADIUS + Math.sin(frameCount * 0.05) * 1.2, 0, Math.PI * 2);
                ctx.fill();
                ctx.restore();
                
                // Decay Flare Intensity
                if (flareIntensity > 0) {{
                    flareIntensity *= 0.96;
                    if (flareIntensity < 0.01) flareIntensity = 0;
                }}
                
                requestAnimationFrame(renderLoop);
            }}
            
            requestAnimationFrame(renderLoop);
            
            // Flare trigger function
            function triggerSolarFlare() {{
                flareIntensity = 1.0;
                flareWaveRadius = SUN_RADIUS + 5;
                
                const statusDot = document.getElementById('status-dot');
                const statusText = document.getElementById('status-text');
                const fluxVal = document.getElementById('flux-val');
                
                statusDot.style.background = '#ff8a3d';
                statusDot.style.boxShadow = '0 0 12px #ff8a3d';
                statusText.innerText = 'FLARE DETECTED';
                statusText.style.color = '#ff8a3d';
                fluxVal.innerText = '1.30e-04 W/m² (X-Class)';
                
                setTimeout(() => {{
                    statusDot.style.background = '#5fd4c9';
                    statusDot.style.boxShadow = '0 0 8px #5fd4c9';
                    statusText.innerText = 'NOMINAL';
                    statusText.style.color = '#5fd4c9';
                    fluxVal.innerText = '{flux_str} W/m²';
                }}, 6500);
            }}
            
            document.getElementById('btn-flare').addEventListener('click', triggerSolarFlare);
            document.getElementById('btn-reset').addEventListener('click', () => {{
                createOrbitingBodies();
            }});
            document.getElementById('btn-pause').addEventListener('click', (e) => {{
                isPaused = !isPaused;
                e.target.innerText = isPaused ? 'RESUME' : 'PAUSE';
            }});
            
            // Window resize handler
            window.addEventListener('resize', () => {{
                width = wrapper.clientWidth;
                height = wrapper.clientHeight;
                canvas.width = width;
                canvas.height = height;
                sunPos = {{ x: width / 2, y: height / 2 }};
            }});
        </script>
    </body>
    </html>
    """
    return html_code
