"""
Solar Physics & Telemetry Component using Matter.js
Supports:
1. render_top_solar_hud_html(): An integrated, space-themed top header HUD with an automatic periodic solar flare simulation running in the top-right corner.
2. render_solar_physics_html(): Full console-width solar physics workbench.
"""

def render_top_solar_hud_html(last_flare_str="M2.1 at 22:05:59 UTC", flux_str="2.41e-06"):
    """
    Renders an integrated mission-control top header with:
    - Left: Aerospace telemetry brand & Aditya-L1 orbital coordinates
    - Right: Matter.js live solar core with automatic cyclic solar flare eruptions,
             radial shockwave pulses, orbiting telemetry particles, and dynamic flux readout.
    """
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:wght@400;500&display=swap');
            
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            
            body {{
                background-color: transparent;
                color: #ffffff;
                font-family: 'IBM Plex Sans', sans-serif;
                overflow: hidden;
                width: 100%;
                height: 125px;
            }}
            
            .hud-chassis {{
                width: 100%;
                height: 100%;
                background: linear-gradient(135deg, rgba(10, 14, 38, 0.95) 0%, rgba(5, 7, 20, 0.98) 100%);
                border: 1px solid rgba(95, 212, 201, 0.28);
                border-left: 3px solid #5fd4c9;
                border-radius: 2px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 0 16px;
                box-shadow: 0 4px 24px rgba(0, 0, 0, 0.6), inset 0 0 15px rgba(95, 212, 201, 0.04);
                position: relative;
            }}
            
            /* Left Mission Information Block */
            .hud-left {{
                display: flex;
                flex-direction: column;
                justify-content: center;
                gap: 4px;
                z-index: 2;
            }}
            
            .hud-brand {{
                font-family: 'Space Grotesk', sans-serif;
                font-size: 1.22rem;
                font-weight: 700;
                letter-spacing: 0.07em;
                color: #ffffff;
                display: flex;
                align-items: center;
                gap: 8px;
                text-shadow: 0 0 12px rgba(255, 255, 255, 0.25);
            }}
            
            .brand-led {{
                width: 9px;
                height: 9px;
                border-radius: 50%;
                background: #f5a94e;
                box-shadow: 0 0 10px #f5a94e;
                animation: led-blink 2.4s infinite ease-in-out;
            }}
            
            @keyframes led-blink {{
                0%, 100% {{ opacity: 1; transform: scale(1); }}
                50% {{ opacity: 0.45; transform: scale(0.85); }}
            }}
            
            .hud-subtitle {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.76rem;
                color: #94a3b8;
                letter-spacing: 0.05em;
            }}
            
            .hud-tags {{
                display: flex;
                align-items: center;
                gap: 12px;
                margin-top: 4px;
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.72rem;
            }}
            
            .hud-tag-item {{
                color: #cbd5e1;
                background: rgba(148, 163, 184, 0.08);
                border: 1px solid rgba(148, 163, 184, 0.2);
                padding: 2px 7px;
                border-radius: 2px;
            }}
            
            .hud-tag-item span {{
                color: #5fd4c9;
                font-weight: 600;
            }}
            
            /* Right Solar Simulation & Live Telemetry */
            .hud-right {{
                display: flex;
                align-items: center;
                gap: 18px;
                height: 100%;
            }}
            
            .solar-telemetry-block {{
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                justify-content: center;
                gap: 4px;
                font-family: 'IBM Plex Mono', monospace;
            }}
            
            .telemetry-status-badge {{
                display: flex;
                align-items: center;
                gap: 6px;
                font-size: 0.72rem;
                font-weight: 600;
                padding: 3px 8px;
                border-radius: 2px;
                background: rgba(95, 212, 201, 0.12);
                border: 1px solid rgba(95, 212, 201, 0.4);
                color: #5fd4c9;
                transition: all 0.3s ease;
            }}
            
            .status-pulsing-dot {{
                width: 7px;
                height: 7px;
                border-radius: 50%;
                background: #5fd4c9;
                box-shadow: 0 0 8px #5fd4c9;
                animation: pulse-dot 1.8s infinite ease-in-out;
            }}
            
            .flux-readout {{
                font-family: 'Space Grotesk', sans-serif;
                font-size: 0.96rem;
                font-weight: 700;
                color: #f5a94e;
                letter-spacing: 0.02em;
                transition: all 0.3s ease;
            }}
            
            .orbit-coord {{
                font-size: 0.68rem;
                color: #94a3b8;
            }}
            
            /* Canvas Container in Upper Right */
            .solar-canvas-box {{
                width: 220px;
                height: 105px;
                position: relative;
                background: radial-gradient(circle at 50% 50%, rgba(20, 26, 60, 0.8) 0%, rgba(5, 7, 20, 0.95) 75%);
                border: 1px solid rgba(95, 212, 201, 0.22);
                border-radius: 2px;
                overflow: hidden;
            }}
            
            #matter-sun-canvas {{
                width: 100%;
                height: 100%;
                display: block;
                cursor: grab;
            }}
            
            .hud-overlay-label {{
                position: absolute;
                top: 4px;
                left: 6px;
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.58rem;
                color: #5fd4c9;
                letter-spacing: 0.06em;
                pointer-events: none;
                opacity: 0.85;
            }}
            
            .auto-flare-tag {{
                position: absolute;
                bottom: 4px;
                right: 6px;
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.55rem;
                color: #f5a94e;
                pointer-events: none;
                letter-spacing: 0.05em;
            }}
        </style>
        <script src="https://cdnjs.cloudflare.com/ajax/libs/matter-js/0.19.0/matter.min.js"></script>
    </head>
    <body>
        <div class="hud-chassis">
            <!-- Left Header -->
            <div class="hud-left">
                <div class="hud-brand">
                    <span class="brand-led"></span> SOLEXS / L1 CONSOLE
                </div>
                <div class="hud-subtitle">SOLAR LOW ENERGY X-RAY SPECTROMETER · ISRO ADITYA-L1 MISSION</div>
                <div class="hud-tags">
                    <div class="hud-tag-item">ORBIT: <span>L1 HALO (1.5M KM)</span></div>
                    <div class="hud-tag-item">SPECTROMETER: <span>SDD2 340-CH</span></div>
                    <div class="hud-tag-item">SAMPLING: <span>1.0s CADENCE</span></div>
                    <div class="hud-tag-item">MODE: <span style="color: #f5a94e;">ARCHIVE TELEMETRY</span></div>
                </div>
            </div>
            
            <!-- Right Interactive Matter.js Solar Orb & Real-time Auto Flare -->
            <div class="hud-right">
                <div class="solar-telemetry-block">
                    <div class="telemetry-status-badge" id="telemetry-badge">
                        <span class="status-pulsing-dot" id="status-dot"></span>
                        <span id="telemetry-text">● TELEMETRY NOMINAL</span>
                    </div>
                    <div class="flux-readout" id="flux-text">X-RAY FLUX: {flux_str} W/m²</div>
                    <div class="orbit-coord" id="flare-info">LAST CATALOGUED: {last_flare_str}</div>
                </div>
                
                <div class="solar-canvas-box" id="canvas-box">
                    <div class="hud-overlay-label">SOLAR CORE (MATTER.JS)</div>
                    <div class="auto-flare-tag">AUTO-FLARE: ACTIVE</div>
                    <canvas id="matter-sun-canvas"></canvas>
                </div>
            </div>
        </div>

        <script>
            // Matter.js Setup for Compact Top-Right Solar Orb
            const {{ Engine, Bodies, Composite, Body, Mouse, MouseConstraint, Events }} = Matter;
            
            const box = document.getElementById('canvas-box');
            const canvas = document.getElementById('matter-sun-canvas');
            const ctx = canvas.getContext('2d');
            
            let width = box.clientWidth;
            let height = box.clientHeight;
            canvas.width = width;
            canvas.height = height;
            
            const engine = Engine.create({{
                gravity: {{ x: 0, y: 0 }}
            }});
            
            let sunPos = {{ x: width / 2, y: height / 2 }};
            const SUN_RADIUS = 15;
            const SUN_MASS = 4500;
            const SPEED_SCALE = 0.55;
            
            // Orbiting telemetry particles
            const particleConfigs = [
                {{ radius: 29, size: 2.2, color: '#f5a94e', trailColor: 'rgba(245, 169, 78, ' }},
                {{ radius: 44, size: 2.5, color: '#5fd4c9', trailColor: 'rgba(95, 212, 201, ' }},
                {{ radius: 60, size: 2.4, color: '#ffd58a', trailColor: 'rgba(255, 213, 138, ' }},
                {{ radius: 76, size: 2.8, color: '#5fd4c9', trailColor: 'rgba(95, 212, 201, ' }},
                {{ radius: 92, size: 2.3, color: '#f5a94e', trailColor: 'rgba(245, 169, 78, ' }}
            ];
            
            let particles = [];
            let trails = [];
            const MAX_TRAIL_LENGTH = 36;
            
            function createOrbitingBodies() {{
                particles.forEach(p => Composite.remove(engine.world, p));
                particles = [];
                trails = [];
                
                particleConfigs.forEach((cfg, idx) => {{
                    const angle = (idx / particleConfigs.length) * Math.PI * 2 + Math.PI / 5;
                    const px = sunPos.x + Math.cos(angle) * cfg.radius;
                    const py = sunPos.y + Math.sin(angle) * cfg.radius;
                    
                    const body = Bodies.circle(px, py, cfg.size, {{
                        frictionAir: 0,
                        restitution: 1,
                        collisionFilter: {{ group: -1 }},
                        density: 0.001
                    }});
                    
                    const vMag = Math.sqrt(SUN_MASS / cfg.radius) * SPEED_SCALE;
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
                constraint: {{ stiffness: 0.15, render: {{ visible: false }} }}
            }});
            Composite.add(engine.world, mouseConstraint);
            
            // Gravity towards Sun
            Events.on(engine, 'beforeUpdate', () => {{
                particles.forEach(body => {{
                    const dx = sunPos.x - body.position.x;
                    const dy = sunPos.y - body.position.y;
                    const distSq = dx * dx + dy * dy;
                    const dist = Math.sqrt(distSq);
                    
                    if (dist > 6) {{
                        const forceMag = (SUN_MASS * body.mass) / distSq * 0.00035;
                        Body.applyForce(body, body.position, {{
                            x: (dx / dist) * forceMag,
                            y: (dy / dist) * forceMag
                        }});
                    }}
                }});
            }});
            
            // Automatic Solar Flare Pulse Loop
            let flareIntensity = 0;
            let flareWaveRadius = 0;
            let frameCount = 0;
            
            function triggerAutoFlare() {{
                flareIntensity = 1.0;
                flareWaveRadius = SUN_RADIUS + 3;
                
                const badge = document.getElementById('telemetry-badge');
                const dot = document.getElementById('status-dot');
                const text = document.getElementById('telemetry-text');
                const flux = document.getElementById('flux-text');
                
                badge.style.background = 'rgba(255, 138, 61, 0.2)';
                badge.style.borderColor = '#ff8a3d';
                badge.style.color = '#ff8a3d';
                dot.style.background = '#ff8a3d';
                dot.style.boxShadow = '0 0 10px #ff8a3d';
                text.innerText = '⚡ SOLAR FLARE DETECTED';
                flux.style.color = '#ff8a3d';
                flux.innerText = 'X-RAY FLUX: 1.30e-04 W/m² (X-Class)';
                
                setTimeout(() => {{
                    badge.style.background = 'rgba(95, 212, 201, 0.12)';
                    badge.style.borderColor = 'rgba(95, 212, 201, 0.4)';
                    badge.style.color = '#5fd4c9';
                    dot.style.background = '#5fd4c9';
                    dot.style.boxShadow = '0 0 8px #5fd4c9';
                    text.innerText = '● TELEMETRY NOMINAL';
                    flux.style.color = '#f5a94e';
                    flux.innerText = 'X-RAY FLUX: {flux_str} W/m²';
                }}, 4800);
            }}
            
            // Automatically trigger solar flare every 14 seconds
            setInterval(triggerAutoFlare, 14000);
            
            // Allow manual click trigger on canvas
            canvas.addEventListener('click', triggerAutoFlare);
            
            function renderLoop() {{
                Engine.update(engine, 1000 / 60);
                frameCount++;
                
                ctx.clearRect(0, 0, width, height);
                
                // Corona Rings
                ctx.save();
                for (let r = 1; r <= 3; r++) {{
                    const ringRadius = SUN_RADIUS + r * 14 + Math.sin(frameCount * 0.03 + r) * 2 + flareIntensity * 8;
                    ctx.beginPath();
                    ctx.arc(sunPos.x, sunPos.y, ringRadius, 0, Math.PI * 2);
                    ctx.strokeStyle = `rgba(245, 169, 78, ${{0.06 + flareIntensity * 0.16 - r * 0.015}})`;
                    ctx.lineWidth = 1;
                    ctx.setLineDash([3, 6]);
                    ctx.stroke();
                }}
                ctx.restore();
                
                // Flare Wave
                if (flareWaveRadius > 0) {{
                    ctx.save();
                    ctx.beginPath();
                    ctx.arc(sunPos.x, sunPos.y, flareWaveRadius, 0, Math.PI * 2);
                    ctx.strokeStyle = `rgba(255, 138, 61, ${{Math.max(0, 1 - flareWaveRadius / (width * 0.55)) * 0.85}})`;
                    ctx.lineWidth = 2;
                    ctx.stroke();
                    ctx.restore();
                    
                    flareWaveRadius += 2.8;
                    if (flareWaveRadius > width * 0.6) {{
                        flareWaveRadius = 0;
                    }}
                }}
                
                // Draw Trails
                particles.forEach((body, idx) => {{
                    const tr = trails[idx];
                    tr.push({{ x: body.position.x, y: body.position.y }});
                    if (tr.length > MAX_TRAIL_LENGTH) tr.shift();
                    
                    if (tr.length > 2) {{
                        for (let i = 1; i < tr.length; i++) {{
                            const alpha = (i / tr.length) * 0.6;
                            ctx.beginPath();
                            ctx.moveTo(tr[i - 1].x, tr[i - 1].y);
                            ctx.lineTo(tr[i].x, tr[i].y);
                            ctx.strokeStyle = body.renderConfig.trailColor + alpha + ')';
                            ctx.lineWidth = 1.1;
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
                    ctx.shadowBlur = 6;
                    ctx.fill();
                    ctx.shadowBlur = 0;
                }});
                
                // Central Sun with Glowing Gradient
                ctx.save();
                const sunGlow = ctx.createRadialGradient(
                    sunPos.x, sunPos.y, SUN_RADIUS * 0.2,
                    sunPos.x, sunPos.y, SUN_RADIUS * (2.4 + flareIntensity * 1.2)
                );
                sunGlow.addColorStop(0, 'rgba(255, 213, 138, 0.95)');
                sunGlow.addColorStop(0.4, 'rgba(245, 169, 78, 0.45)');
                sunGlow.addColorStop(0.8, 'rgba(255, 138, 61, 0.15)');
                sunGlow.addColorStop(1, 'rgba(5, 7, 20, 0)');
                
                ctx.fillStyle = sunGlow;
                ctx.beginPath();
                ctx.arc(sunPos.x, sunPos.y, SUN_RADIUS * (2.4 + flareIntensity * 1.2), 0, Math.PI * 2);
                ctx.fill();
                
                // Core
                const sunCore = ctx.createRadialGradient(
                    sunPos.x - SUN_RADIUS * 0.2, sunPos.y - SUN_RADIUS * 0.2, 1,
                    sunPos.x, sunPos.y, SUN_RADIUS
                );
                sunCore.addColorStop(0, '#fff6d6');
                sunCore.addColorStop(0.5, '#f5a94e');
                sunCore.addColorStop(1, '#ff8a3d');
                
                ctx.fillStyle = sunCore;
                ctx.beginPath();
                ctx.arc(sunPos.x, sunPos.y, SUN_RADIUS + Math.sin(frameCount * 0.06) * 0.8, 0, Math.PI * 2);
                ctx.fill();
                ctx.restore();
                
                if (flareIntensity > 0) {{
                    flareIntensity *= 0.96;
                    if (flareIntensity < 0.01) flareIntensity = 0;
                }}
                
                requestAnimationFrame(renderLoop);
            }}
            
            requestAnimationFrame(renderLoop);
            
            window.addEventListener('resize', () => {{
                width = box.clientWidth;
                height = box.clientHeight;
                canvas.width = width;
                canvas.height = height;
                sunPos = {{ x: width / 2, y: height / 2 }};
            }});
        </script>
    </body>
    </html>
    """
    return html_code

# Compatibility alias
render_solar_physics_html = render_top_solar_hud_html
