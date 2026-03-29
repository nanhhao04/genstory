"""
styles.py — Định nghĩa phong cách Visual cho GenStory (Nebula Theme)
"""

# Màu sắc chủ đạo (Tokens)
# ---------------------------------------------------------------------------
DARK_BG = "#010105"
PURE_WHITE = "#FFFFFF"
LIGHT_PURPLE = "#C084FC"
LIGHT_GRAY = "#EAEAEA"

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Cinzel:wght@400;700;900&family=Crimson+Pro:ital,wght@0,400;0,500;1,400&display=swap');

:root {{
    --p:      {LIGHT_PURPLE};   /* purple-400  – primary accent */
    --p-dim:  #A855F7;          /* purple-500  – slightly darker */
    --p-glow: rgba(192,132,252,0.35);
    --pink:   #F472B6;          /* pink-400    – secondary accent */
    --cyan:   #67E8F9;          /* cyan-300    – tertiary / info */
    --bg:     {DARK_BG};        /* Black deep space */
    --card:   rgba(14, 8, 32, 0.85); /* Tăng độ mờ để dễ đọc chữ trắng */
    --border: rgba(192,132,252,0.18);
    --border-bright: rgba(192,132,252,0.45);

    /* Text — High contrast */
    --txt:    {PURE_WHITE};     /* Pure White */
    --txt-2:  {LIGHT_GRAY};     /* Light Gray */
    --txt-3:  #94A3B8;          /* Muted hints */
}}

#galaxy-canvas {{
    position: fixed;
    inset: 0;
    z-index: 0;
    pointer-events: none;
}}

body, .gradio-container, footer {{
    background: transparent !important;
    position: relative;
    z-index: 1;
}}

body {{
    background-color: var(--bg) !important;
    color: var(--txt) !important;
    font-family: 'Inter', sans-serif !important;
}}

/* Nebula layers */
body::before {{
    content: "";
    position: fixed;
    inset: 0;
    z-index: 0;
    background:
        radial-gradient(ellipse 80% 60% at 15% 25%,  rgba(139,68,255,0.18) 0%, transparent 60%),
        radial-gradient(ellipse 60% 80% at 85% 75%,  rgba(103,232,249,0.08) 0%, transparent 55%),
        radial-gradient(ellipse 70% 50% at 50% 100%, rgba(244,114,182,0.10) 0%, transparent 50%);
    animation: nebula-drift 35s ease-in-out infinite alternate;
    pointer-events: none;
}}

@keyframes nebula-drift {{
    0%   {{ opacity: 0.8; transform: scale(1) translate(0, 0); }}
    100% {{ opacity: 1;   transform: scale(1.05) translate(-10px, 8px); }}
}}

.gradio-container {{
    max-width: 1340px !important;
    border: none !important;
    background: transparent !important;
}}

.glass-card {{
    background: var(--card) !important;
    backdrop-filter: blur(28px) saturate(150%) !important;
    border: 1px solid var(--border) !important;
    border-radius: 20px !important;
    box-shadow: 0 20px 60px -15px rgba(0,0,0,0.8) !important;
    padding: 28px !important;
    margin-bottom: 20px !important;
}}

#chapter-content {{
    background: rgba(5, 2, 12, 0.9) !important;
    backdrop-filter: blur(16px) !important;
    padding: 44px 48px !important;
    border-radius: 24px 24px 0 0 !important;
    border: 1px solid var(--border) !important;
    border-bottom: none !important;
    box-shadow: inset 0 0 40px rgba(139,68,255,0.08) !important;
}}

#manga-image {{
    background: rgba(5, 2, 12, 0.9) !important;
    border-radius: 0 0 24px 24px !important;
    border: 1px solid var(--border) !important;
    border-top: none !important;
    padding: 0 28px 28px !important;
}}

/* Inputs */
textarea, input[type="text"], .gr-textbox textarea, .gr-textbox input {{
    background: rgba(0, 0, 0, 0.5) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    color: #FFFFFF !important;
    font-size: 15px !important;
}}

textarea:focus, input:focus {{
    border-color: var(--p) !important;
    box-shadow: 0 0 0 2px rgba(192,132,252,0.2) !important;
}}

/* Buttons */
button.primary, .gr-button-primary {{
    background: linear-gradient(135deg, #9333EA 0%, #C084FC 50%, #F472B6 100%) !important;
    background-size: 200% 200% !important;
    animation: btn-shimmer 4s ease infinite !important;
    border: none !important;
    border-radius: 14px !important;
    color: #fff !important;
    font-weight: 700 !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    box-shadow: 0 4px 20px rgba(147,51,234,0.6) !important;
    transition: all 0.2s !important;
}}

@keyframes btn-shimmer {{
    0%   {{ background-position: 0% 50%; }}
    50%  {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}

button.primary:hover, .gr-button-primary:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 30px rgba(192,132,252,0.7) !important;
}}

.gr-radio-label {{
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid var(--border) !important;
    border-radius: 14px !important;
    color: var(--txt-2) !important;
    transition: all 0.2s !important;
}}

.gr-radio-label:hover {{
    background: rgba(139,68,255,0.15) !important;
    border-color: var(--p) !important;
    transform: translateX(4px) !important;
}}

.export-btn button {{
    background: rgba(192,132,252,0.1) !important;
    border: 1px dashed var(--p) !important;
    color: var(--p) !important;
}}

/* Scrollbar */
::-webkit-scrollbar {{ width: 6px; }}
::-webkit-scrollbar-thumb {{ background: rgba(192,132,252,0.4); border-radius: 3px; }}
"""

GALAXY_HTML = f"""
<canvas id="galaxy-canvas"></canvas>
<script>
(function(){{
  const canvas = document.getElementById('galaxy-canvas');
  const ctx    = canvas.getContext('2d');
  let W, H, stars=[], shooting=[], nebula=[];

  function resize(){{
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }}

  function mkStar(){{
    return {{
      x: Math.random()*W, y: Math.random()*H,
      r: Math.random()*1.3 + 0.2,
      base: Math.random()*0.5 + 0.2, phase: Math.random()*Math.PI*2,
      speed: Math.random()*0.006 + 0.002,
      color: `hsl(${{[280,290,200][Math.random()*3|0]}}, 80%, 90%)`,
    }};
  }}

  function mkBlob(){{
    return {{
      x: Math.random()*W, y: Math.random()*H,
      rx: 200+Math.random()*300, ry: 150+Math.random()*250,
      hue: 260+Math.random()*60, alpha: 0.05+Math.random()*0.05,
      dx: (Math.random()-.5)*0.1, dy: (Math.random()-.5)*0.06,
    }};
  }}

  function init(){{
    resize();
    stars = Array.from({{length:250}}, mkStar);
    nebula = Array.from({{length:6}}, mkBlob);
  }}

  function loop(t){{
    ctx.clearRect(0,0,W,H);
    ctx.fillStyle = '{DARK_BG}';
    ctx.fillRect(0,0,W,H);

    // Nebula blobs
    nebula.forEach(b=>{{
      b.x += b.dx; b.y += b.dy;
      if(b.x < -b.rx) b.x = W+b.rx; if(b.x > W+b.rx) b.x = -b.rx;
      if(b.y < -b.ry) b.y = H+b.ry; if(b.y > H+b.ry) b.y = -b.ry;
      const pulse = 1 + 0.05*Math.sin(t*0.0005 + b.hue);
      const g = ctx.createRadialGradient(b.x, b.y, 0, b.x, b.y, b.rx*pulse);
      g.addColorStop(0, `hsla(${{b.hue}},70%,50%,${{b.alpha}})`);
      g.addColorStop(1, `hsla(${{b.hue}},50%,20%,0)`);
      ctx.save(); ctx.scale(1, b.ry/b.rx);
      ctx.beginPath(); ctx.arc(b.x, b.y*(b.rx/b.ry), b.rx*pulse, 0, Math.PI*2);
      ctx.fillStyle = g; ctx.fill(); ctx.restore();
    }});

    // Stars
    stars.forEach(s=>{{
      const a = s.base + 0.4*Math.sin(t*s.speed + s.phase);
      ctx.beginPath(); ctx.arc(s.x, s.y, s.r, 0, Math.PI*2);
      ctx.fillStyle = s.color; ctx.globalAlpha = Math.max(0, a);
      ctx.fill(); ctx.globalAlpha = 1;
    }});

    requestAnimationFrame(loop);
  }}

  window.addEventListener('resize', resize);
  init(); requestAnimationFrame(loop);
}})();
</script>
"""
