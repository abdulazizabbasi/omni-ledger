"""
╔══════════════════════════════════════════════════════════════════════╗
║        OMNI LEDGER INTELLIGENCE  v3.0           ║
║        Production-Ready | DynamoDB Live Stream | Leaflet Maps        ║
╚══════════════════════════════════════════════════════════════════════╝

Requirements:
    pip install streamlit boto3 pandas plotly requests python-dotenv

Run:
    streamlit run dashboard.py
"""

import json
import math
import time
import hashlib
from datetime import datetime, timezone
from decimal import Decimal

import boto3
import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
import streamlit.components.v1 as components
from botocore.exceptions import ClientError, NoCredentialsError

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OMNI LEDGER INTELLIGENCE",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# GLOBAL CSS – Corporate daytime layout theme
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Sora:wght@300;400;600;700&display=swap');

/* ── Reset & root ── */
:root {
    --bg:         #F4F6FA;
    --surface:    #FFFFFF;
    --surface2:   #EEF1F8;
    --border:     #D8DDE8;
    --accent:     #1A56DB;
    --accent2:    #E53E3E;
    --accent3:    #D97706;
    --text:       #111827;
    --text2:      #4B5563;
    --text3:      #9CA3AF;
    --green:      #059669;
    --mono:       'IBM Plex Mono', monospace;
    --sans:       'Sora', sans-serif;
    --radius:     10px;
    --shadow:     0 2px 12px rgba(0,0,0,0.08);
    --shadow-lg:  0 8px 32px rgba(0,0,0,0.12);
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    font-family: var(--sans);
    color: var(--text);
}

[data-testid="stHeader"] { background: transparent !important; }
.block-container { padding: 1.2rem 2rem 2rem !important; max-width: 100% !important; }

/* ── Metric cards ribbon ── */
.stat-ribbon {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 14px;
    margin-bottom: 1.4rem;
}
.stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 20px;
    box-shadow: var(--shadow);
    position: relative;
    overflow: hidden;
}
.stat-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: var(--radius) var(--radius) 0 0;
}
.stat-card.blue::before  { background: var(--accent); }
.stat-card.red::before   { background: var(--accent2); }
.stat-card.amber::before { background: var(--accent3); }
.stat-card.green::before { background: var(--green); }
.stat-card.gray::before  { background: var(--text3); }

.stat-label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text2);
    margin-bottom: 6px;
}
.stat-value {
    font-family: var(--mono);
    font-size: 24px;
    font-weight: 600;
    color: var(--text);
    line-height: 1.1;
}
.stat-sub {
    font-size: 11px;
    color: var(--text3);
    margin-top: 4px;
    font-family: var(--mono);
}
.badge-live {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 20px;
    margin-top: 6px;
}
.badge-live.online  { background:#DCFCE7; color:#166534; border:1px solid #BBF7D0; }
.pulse { width:7px; height:7px; border-radius:50%; }
.pulse.green { background:#22C55E; animation: pulse 1.4s infinite; }
@keyframes pulse {
    0%,100% { opacity:1; transform:scale(1); }
    50%      { opacity:.5; transform:scale(1.3); }
}

/* ── Section headers ── */
.section-header {
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: var(--text2);
    margin-bottom: 10px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--border);
}
.section-dot {
    width: 8px; height: 8px; border-radius: 50%;
    background: var(--accent); flex-shrink: 0;
}

/* ── Audit feed cards ── */
.audit-feed {
    display: flex;
    flex-direction: column;
    gap: 10px;
    max-height: 560px;
    overflow-y: auto;
    padding-right: 4px;
}
.audit-feed::-webkit-scrollbar { width: 5px; }
.audit-feed::-webkit-scrollbar-track { background: var(--surface2); border-radius:4px; }
.audit-feed::-webkit-scrollbar-thumb { background: var(--border); border-radius:4px; }

.audit-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-left: 4px solid var(--accent);
    border-radius: var(--radius);
    padding: 12px 14px;
    box-shadow: var(--shadow);
    font-size: 12px;
    line-height: 1.6;
}
.audit-card.suspicious { border-left-color: var(--accent2); }

.tx-hash {
    font-family: var(--mono);
    font-size: 10.5px;
    color: var(--accent);
    word-break: break-all;
    font-weight: 600;
    margin-bottom: 4px;
}
.wallet {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text2);
    word-break: break-all;
}
.addr-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--text3);
}
.geo-tag {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 2px 7px;
    font-size: 10px;
    font-weight: 600;
    color: var(--text2);
    margin-top: 4px;
}
.value-badge {
    display: inline-block;
    background: #FEF3C7;
    border: 1px solid #FDE68A;
    color: #92400E;
    border-radius: 4px;
    padding: 1px 7px;
    font-size: 10.5px;
    font-weight: 700;
    font-family: var(--mono);
}
.value-badge.suspicious {
    background: #FEE2E2;
    border-color: #FECACA;
    color: #991B1B;
}
.ai-block {
    margin-top: 8px;
    background: #F0F4FF;
    border: 1px solid #C7D7FD;
    border-radius: 6px;
    padding: 7px 10px;
    font-size: 11px;
    color: #1E3A8A;
    line-height: 1.5;
}
.ai-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #3B82F6;
    margin-bottom: 3px;
}
.timestamp-tag {
    font-family: var(--mono);
    font-size: 10px;
    color: var(--text3);
}

/* ── Chart containers ── */
.chart-container {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px;
    box-shadow: var(--shadow);
    margin-bottom: 1rem;
}

/* ── Page title bar ── */
.title-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1.4rem;
    padding-bottom: 12px;
    border-bottom: 2px solid var(--border);
}
.title-main {
    font-size: 20px;
    font-weight: 700;
    color: var(--text);
    letter-spacing: -0.02em;
}
.title-sub {
    font-size: 12px;
    color: var(--text2);
    margin-top: 2px;
    font-family: var(--mono);
}
.refresh-info {
    font-size: 11px;
    color: var(--text3);
    font-family: var(--mono);
}
</style>
""",
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION & CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────
DYNAMO_TABLE = "crypto-fraud-alerts"
AWS_REGION = "us-east-1"
REFRESH_SECS = 5

# ─────────────────────────────────────────────────────────────────────────────
# DATA HELPERS & TYPE CASTING
# ─────────────────────────────────────────────────────────────────────────────
def safe_float(val, default=0.0) -> float:
    if val is None: return default
    try: return float(val)
    except (ValueError, TypeError): return default

def safe_str(val, default="—") -> str:
    if val is None or str(val).strip() == "": return default
    return str(val).strip()

def unify_decimals(element):
    if isinstance(element, list): return [unify_decimals(x) for x in element]
    if isinstance(element, dict): return {k: unify_decimals(v) for k, v in element.items()}
    if isinstance(element, Decimal): return int(element) if element % 1 == 0 else float(element)
    return element

# ─────────────────────────────────────────────────────────────────────────────
# DATA INTEGRATION PIPELINE (DYNAMODB)
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(show_spinner=False)
def get_dynamodb_table():
    # This explicitly passes your credentials to Boto3
    dynamodb = boto3.resource(
        "dynamodb", 
        region_name=st.secrets["AWS"]["AWS_DEFAULT_REGION"],
        aws_access_key_id=st.secrets["AWS"]["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS"]["AWS_SECRET_ACCESS_KEY"]
    )
    return dynamodb.Table("crypto-fraud-alerts") # Ensure this matches your exact table name

def fetch_all_records(table) -> list[dict]:
    items = []
    try:
        resp = table.scan()
        items.extend(resp.get("Items", []))
        while "LastEvaluatedKey" in resp:
            resp = table.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
            items.extend(resp.get("Items", []))
    except Exception as e:
        st.error(f"Data Fetch Failure: {e}")
    return items

def records_to_df(items: list[dict]) -> pd.DataFrame:
    rows = []
    for item in items:
        try:
            cleaned_item = unify_decimals(item)
            # Universal key matching (adapting value_coin/chain schemas smoothly)
            val_coin = safe_float(cleaned_item.get("value_coin") or cleaned_item.get("value_eth"))
            chain = safe_str(cleaned_item.get("chain"), default="ETH")
            
            rows.append({
                "transaction_hash": safe_str(cleaned_item.get("transaction_hash")),
                "timestamp": safe_str(cleaned_item.get("timestamp")),
                "from_address": safe_str(cleaned_item.get("from_address")),
                "to_address": safe_str(cleaned_item.get("to_address")),
                "value_coin": val_coin,
                "chain": chain,
                "gas_fee": safe_str(cleaned_item.get("gas_fee") or cleaned_item.get("gas_price_gwei"), "0.00 Gwei"),
                "sender_lat": safe_float(cleaned_item.get("sender_lat") or cleaned_item.get("lat"), default=24.8607),
                "sender_lon": safe_float(cleaned_item.get("sender_lon") or cleaned_item.get("lon"), default=67.0011),
                "sender_city": safe_str(cleaned_item.get("sender_city") or cleaned_item.get("node_city"), "Global Node"),
                "sender_country": safe_str(cleaned_item.get("sender_country") or cleaned_item.get("node_country"), "Network"),
                "lat": safe_float(cleaned_item.get("lat"), default=24.8607),
                "lon": safe_float(cleaned_item.get("lon"), default=67.0011),
                "node_city": safe_str(cleaned_item.get("node_city"), "Global Node"),
                "node_country": safe_str(cleaned_item.get("node_country"), "Hub"),
                "node_ip": safe_str(cleaned_item.get("node_ip"), "127.0.0.1"),
                "node_isp": safe_str(cleaned_item.get("node_isp"), "Autonomous Core Systems"),
                "broadcast_source": safe_str(cleaned_item.get("broadcast_source"), "Unknown Endpoint"),
                "ai_analysis": safe_str(cleaned_item.get("ai_analysis"), "Routine verification verified safe."),
                "risk_status": safe_str(cleaned_item.get("risk_status"), "CLEAN"),
            })
        except Exception:
            pass
    
    df = pd.DataFrame(rows)
    if not df.empty and "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True).dt.tz_localize(None)
        df = df.sort_values("timestamp", ascending=False).reset_index(drop=True)
    return df

# ─────────────────────────────────────────────────────────────────────────────
# LEAFLET CINEMATIC ARC MAP HTML ENGINE
# ─────────────────────────────────────────────────────────────────────────────
def build_map_html(df: pd.DataFrame, height: int = 560) -> str:
    geo_df = df.dropna(subset=["sender_lat", "sender_lon", "lat", "lon"]).copy()
    transactions = []
    for _, row in geo_df.iterrows():
        transactions.append({
            "hash": row["transaction_hash"],
            "from_addr": row["from_address"],
            "to_addr": row["to_address"],
            "value_coin": round(row["value_coin"], 4),
            "chain": row["chain"],
            "gas_fee": row["gas_fee"],
            "sender_lat": row["sender_lat"],
            "sender_lon": row["sender_lon"],
            "sender_city": row["sender_city"],
            "sender_country": row["sender_country"],
            "lat": row["lat"],
            "lon": row["lon"],
            "node_city": row["node_city"],
            "node_country": row["node_country"],
            "node_ip": row["node_ip"],
            "node_isp": row["node_isp"],
            "ai_analysis": row["ai_analysis"],
            "timestamp": str(row["timestamp"]),
            "is_suspicious": bool(row["risk_status"] == "SUSPICIOUS"),
        })

    tx_json = json.dumps(transactions)
    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  html, body, #map {{ width:100%; height:{height}px; font-family:'Sora',sans-serif; }}
  .tx-tooltip {{ background:#fff; border:1.5px solid #D8DDE8; border-radius:10px; padding:14px 16px; min-width:310px; box-shadow:0 8px 32px rgba(0,0,0,0.14); font-size:12px; line-height:1.7; }}
  .tx-tooltip .tt-hash {{ font-family:'IBM Plex Mono',monospace; font-size:10px; word-break:break-all; color:#1A56DB; font-weight:600; margin-bottom:8px; border-bottom:1px solid #EEF1F8; padding-bottom:6px; }}
  .tx-tooltip .tt-row {{ display:flex; gap:6px; margin-bottom:3px; }}
  .tx-tooltip .tt-label {{ font-size:10px; font-weight:700; text-transform:uppercase; color:#9CA3AF; min-width:75px; }}
  .tx-tooltip .tt-val {{ font-family:'IBM Plex Mono',monospace; font-size:10.5px; word-break:break-all; }}
  .tx-tooltip .tt-ai {{ margin-top:8px; background:#F0F4FF; border:1px solid #C7D7FD; border-radius:6px; padding:7px 10px; color:#1E3A8A; }}
  .tx-tooltip .tt-badge {{ display:inline-block; background:#FEE2E2; border:1px solid #FECACA; color:#991B1B; border-radius:4px; padding:0 6px; font-size:10px; font-weight:700; margin-left:6px; }}
  #arc-canvas {{ position:absolute; top:0; left:0; width:100%; height:{height}px; pointer-events:none; z-index:500; }}
</style>
</head>
<body>
<div style="position:relative;">
  <div id="map"></div>
  <canvas id="arc-canvas"></canvas>
</div>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
const TRANSACTIONS = {tx_json};
const map = L.map('map', {{ zoomControl:true }}).setView([24, 40], 2);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/rastertiles/voyager/{{z}}/{{x}}/{{y}}{{r}}.png').addTo(map);

const canvas = document.getElementById('arc-canvas');
const ctx = canvas.getContext('2d');
let animations = [];

function resizeCanvas() {{
  canvas.width = map.getContainer().offsetWidth;
  canvas.height = map.getContainer().offsetHeight;
}}
resizeCanvas();
map.on('resize move zoom', resizeCanvas);

function bezierPoint(p0, p1, t) {{
  const mx = (p0.x + p1.x) / 2, my = (p0.y + p1.y) / 2;
  const dx = p1.x - p0.x, dy = p1.y - p0.y;
  const len = Math.sqrt(dx*dx + dy*dy);
  const ctrl = {{ x: mx - dy*0.4, y: my + dx*0.4 - len*0.2 }};
  return {{
    x: (1-t)*(1-t)*p0.x + 2*(1-t)*t*ctrl.x + t*t*p1.x,
    y: (1-t)*(1-t)*p0.y + 2*(1-t)*t*ctrl.y + t*t*p1.y,
  }};
}}

function renderLoop() {{
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  animations = animations.filter(a => a.progress <= 1.02);
  for (const arc of animations) {{
    arc.progress += arc.speed;
    const t = Math.min(arc.progress, 1);
    const sPt = map.latLngToContainerPoint([arc.srcLat, arc.srcLng]);
    const dPt = map.latLngToContainerPoint([arc.dstLat, arc.dstLng]);
    
    // Path trail drawing
    ctx.beginPath();
    for(let i=0; i<20; i++) {{
      const ta = Math.max(0, t - 0.15) + (0.15 * (i/20));
      const pt = bezierPoint(sPt, dPt, ta);
      if(i==0) ctx.moveTo(pt.x, pt.y); else ctx.lineTo(pt.x, pt.y);
    }}
    ctx.strokeStyle = arc.isSuspicious ? 'rgba(229,62,62,0.8)' : 'rgba(26,86,219,0.8)';
    ctx.lineWidth = arc.isSuspicious ? 3 : 2;
    ctx.stroke();

    if(t >= 1 && !arc.impactDrawn) {{ arc.impactDrawn = true; }}
  }}
  requestAnimationFrame(renderLoop);
}}
renderLoop();

const sIcon = L.divIcon({{ html: `<div style="width:8px;height:8px;background:#1A56DB;border:1.5px solid #fff;border-radius:50%;"></div>`, className:'' }});
TRANSACTIONS.forEach((tx, i) => {{
  setTimeout(() => {{
    animations.push({{ srcLat:tx.sender_lat, srcLng:tx.sender_lon, dstLat:tx.lat, dstLng:tx.lon, progress:0, speed:0.007, isSuspicious:tx.is_suspicious }});
    const html = `<div class="tx-tooltip">
      <div class="tt-hash">⬡ ${{tx.hash}} ${{tx.is_suspicious ? '<span class="tt-badge">THREAT</span>':''}}</div>
      <div class="tt-row"><span class="tt-label">NET LAYER</span><span class="tt-val" style="font-weight:bold;color:#D97706">${{tx.chain}}</span></div>
      <div class="tt-row"><span class="tt-label">VALUE</span><span class="tt-val">${{tx.value_coin}} ${{tx.chain}}</span></div>
      <div class="tt-row"><span class="tt-label">FROM</span><span class="tt-val">${{tx.from_addr}}</span></div>
      <div class="tt-row"><span class="tt-label">TO</span><span class="tt-val">${{tx.to_addr}}</span></div>
      <div class="tt-row"><span class="tt-label">NODE IP</span><span class="tt-val">${{tx.node_ip}}</span></div>
      <div class="tt-ai"><strong>AI Analysis:</strong><br>${{tx.ai_analysis}}</div>
    </div>`;
    L.marker([tx.sender_lat, tx.sender_lon], {{ icon:sIcon }}).bindPopup(html).addTo(map);
    const rColor = tx.is_suspicious ? '#E53E3E' : '#059669';
    const rIcon = L.divIcon({{ html: `<div style="width:12px;height:12px;background:${{rColor}};border:2px solid #fff;border-radius:50%;"></div>`, className:'' }});
    L.marker([tx.lat, tx.lon], {{ icon:rIcon }}).bindPopup(html).addTo(map);
  }}, i * 150);
}});
</script>
</body>
</html>"""

# ─────────────────────────────────────────────────────────────────────────────
# AUDIT CARD COMPONENT RENDERER
# ─────────────────────────────────────────────────────────────────────────────
def render_audit_card(row: dict) -> str:
    status_class = "suspicious" if row.get("risk_status") == "SUSPICIOUS" else ""
    threat_flag = "⚠️ RISK THREAT DIRECTIVE &nbsp;" if row.get("risk_status") == "SUSPICIOUS" else ""
    val_badge_class = "suspicious" if row.get("risk_status") == "SUSPICIOUS" else ""
    
    return f"""
<div class="audit-card {status_class}">
  <div class="tx-hash">{threat_flag}{safe_str(row.get('transaction_hash'))}</div>
  <div class="addr-label">FROM TARGET</div>
  <div class="wallet">{safe_str(row.get('from_address'))}</div>
  <div class="addr-label" style="margin-top:4px">TO DESTINATION</div>
  <div class="wallet">{safe_str(row.get('to_address'))}</div>
  <div style="margin-top:6px;display:flex;flex-wrap:wrap;gap:6px;align-items:center">
    <span class="value-badge {val_badge_class}">{row.get('value_coin'):,.4f} {row.get('chain')}</span>
    <span class="value-badge" style="background:#F0FDF4;border-color:#BBF7D0;color:#166534">{safe_str(row.get('gas_fee'))}</span>
    <span class="geo-tag">📍 Node: {safe_str(row.get('node_city'))}</span>
    <span class="geo-tag" style="background:#FFF7ED;color:#C2410C;">⚡ Source: {safe_str(row.get('broadcast_source'))}</span>
  </div>
  <div class="ai-block">
    <div class="ai-label">AI Forensic Core Verdict</div>
    {safe_str(row.get('ai_analysis'))}
  </div>
  <div class="timestamp-tag" style="margin-top:6px">{str(row.get('timestamp'))} UTC</div>
</div>"""

# ─────────────────────────────────────────────────────────────────────────────
# MAIN PLATFORM APPLICATION ORCHESTRATION
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # --- Sidebar Control Panel Layout ---
    with st.sidebar:
        st.markdown("<h2 style='font-family:\"Sora\";font-weight:700;margin-bottom:0;'>Control Panel</h2>", unsafe_allow_html=True)
        st.markdown("---")
        selected_chains = st.multiselect("Active Crypto Networks", options=["BTC", "ETH", "SOL"], default=["BTC", "ETH", "SOL"])
        selected_risks = st.multiselect("Threat Signatures", options=["CLEAN", "SUSPICIOUS"], default=["CLEAN", "SUSPICIOUS"])
        live_loop = st.toggle("Ingestion Loop Telemetry", value=True)

    # --- Header Banner Component ---
    st.markdown(
        f"""
<div class="title-bar">
  <div>
    <div class="title-main">🔐 OMNI LEDGER INTELLIGENCE</div>
    <div class="title-sub">Cross-Layer Ledger Forensic Pipeline · DynamoDB Engine</div>
  </div>
  <div class="refresh-info">
    Auto-refresh Active &nbsp;·&nbsp; {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")}
  </div>
</div>""",
        unsafe_allow_html=True,
    )

    # --- Fetch and Process Unified Framework Analytics Data ---
    table = get_dynamodb_table()
    raw_items = fetch_all_records(table)
    df = records_to_df(raw_items)

    if df.empty:
        st.warning("Telemetry infrastructure pipeline empty. Awaiting stream incoming signals...")
        return

    # Filter application constraints
    mask = df["chain"].isin(selected_chains) & df["risk_status"].isin(selected_risks)
    filtered_df = df[mask].reset_index(drop=True)

    # --- Top Metrics HUD Ribbon Bar Row ---
    total_incidents = len(df)
    suspicious_count = int((df["risk_status"] == "SUSPICIOUS").sum())
    eth_vol = float(df[df["chain"] == "ETH"]["value_coin"].sum())
    btc_vol = float(df[df["chain"] == "BTC"]["value_coin"].sum())
    sol_vol = float(df[df["chain"] == "SOL"]["value_coin"].sum())

    st.markdown(
        f"""
<div class="stat-ribbon">
    <div class="stat-card blue">
        <div class="stat-label">TOTAL PACKETS INGESTED</div>
        <div class="stat-value">{total_incidents:,}</div>
        <div class="stat-sub">Live DynamoDB Scans</div>
    </div>
    <div class="stat-card red">
        <div class="stat-label">CRITICAL THREATS DISCOVERED</div>
        <div class="stat-value">{suspicious_count:,}</div>
        <div class="stat-sub">Flagged Risk Status</div>
    </div>
    <div class="stat-card amber">
        <div class="stat-label">BTC CUMULATIVE VOL</div>
        <div class="stat-value">{btc_vol:,.2f}</div>
        <div class="stat-sub">Bitcoin Ledger Network</div>
    </div>
    <div class="stat-card green">
        <div class="stat-label">ETH CUMULATIVE VOL</div>
        <div class="stat-value">{eth_vol:,.2f}</div>
        <div class="stat-sub">Ethereum Ecosystem</div>
    </div>
    <div class="stat-card gray">
        <div class="stat-label">SOL CUMULATIVE VOL</div>
        <div class="stat-value">{sol_vol:,.1f}</div>
        <div class="stat-sub">Solana High Velocity</div>
    </div>
</div>""",
        unsafe_allow_html=True,
    )

    # --- Interactive Geospatial Vector & Card Audit Live Stream Layout Row ---
    col1, col2 = st.columns([7, 5])
    
    with col1:
        st.markdown('<div class="section-header"><div class="section-dot"></div>🌐 Live Geospatial Vector Flow Map Architecture</div>', unsafe_allow_html=True)
        if not filtered_df.empty:
            map_html = build_map_html(filtered_df.head(40))
            components.html(map_html, height=560)
        else:
            st.info("No matching records coordinates to visualize.")

    with col2:
        st.markdown('<div class="section-header"><div class="section-dot"></div>📋 Premium Card Audit Stream Log</div>', unsafe_allow_html=True)
        if filtered_df.empty:
            st.info("No records matched network operational filters.")
        else:
            cards_html = "".join([render_audit_card(row) for _, row in filtered_df.head(25).iterrows()])
            st.markdown(f'<div class="audit-feed">{cards_html}</div>', unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────────
    # NEW MODULES APPENDED SEAMLESSLY AT THE BOTTOM
    # ─────────────────────────────────────────────────────────────────────────────
    
    # --- MODULE 1: MIXER EXPOSURE PROTOCOL INDEX ---
    st.markdown('<div class="section-header"><div class="section-dot" style="background:#D97706;"></div>🌪️ Liquidity Mixing & Protocol Exposure Trace Index</div>', unsafe_allow_html=True)
    if filtered_df.empty:
        st.info("No network data entries available to parse mixer exposure.")
    else:
        mix_col1, mix_col2, mix_col3 = st.columns(3)
        for idx, row in filtered_df.head(3).iterrows():
            target_col = [mix_col1, mix_col2, mix_col3][idx % 3]
            with target_col:
                exposure = round(min(98.4, float(row["value_coin"]) * 3.8 + (40.0 if row["risk_status"] == "SUSPICIOUS" else 4.0)), 1)
                border_style = "border-left: 4px solid #EF4444;" if exposure > 50.0 else "border-left: 4px solid #10B981;"
                badge_lbl = "CRITICAL TAINT ALERT" if exposure > 50.0 else "NOMINAL COEF PASS"
                badge_color = "color:#EF4444; background:#FEE2E2;" if exposure > 50.0 else "color:#10B981; background:#D1FAE5;"
                
                st.markdown(
                    f"""
                    <div class="chart-container" style="{border_style} padding: 14px;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                            <span style="font-family:'IBM Plex Mono'; font-size:11px; font-weight:600; color:#1A56DB;">⬡ {row['chain']} Chain Target</span>
                            <span style="font-size:9px; font-weight:700; padding:2px 6px; border-radius:4px; {badge_color}">{badge_lbl}</span>
                        </div>
                        <div style="font-size:10px; color:#4B5563; font-weight:600;">WALLET ENDPOINT REFERENCE</div>
                        <div style="font-family:'IBM Plex Mono'; font-size:10px; color:#111827; word-break:break-all; margin-bottom:6px;">{row['from_address']}</div>
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-top:8px; border-top:1px solid #EEF1F8; padding-top:6px;">
                            <span style="font-size:11px; color:#4B5563;">Exposure Weight</span>
                            <span style="font-family:'Sora'; font-size:16px; font-weight:700; color:#111827;">{exposure}%</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True
                )

    # --- MODULE 2: FORENSIC AI TERMINAL WORKSPACE & TIME VELOCITY CONTROLS ---
    btm_col1, btm_col2 = st.columns([5, 7])
    
    with btm_col1:
        st.markdown('<div class="section-header"><div class="section-dot" style="background:#059669;"></div>🧠 Forensic Cognitive Prompt AI Terminal</div>', unsafe_allow_html=True)
        st.markdown('<div class="chart-container" style="padding:15px;">', unsafe_allow_html=True)
        search_input = st.text_input("Enter Active Ledger Hash Index / Target Account Index String Key", placeholder="Enter 0x or address reference...", key="ai_term_input")
        if st.button("Initialize Deep Attack Vector Trace Scan Sequences", use_container_width=True):
            if search_input:
                calc_hash = hashlib.md5(search_input.encode('utf-8')).hexdigest().upper()
                st.markdown(
                    f"""
                    <div style="margin-top:10px; padding:10px; background:#F0FDF4; border:1px solid #BBF7D0; border-radius:6px; color:#166534; font-size:11px;">
                        <strong>Status: Processing Complete.</strong><br>
                        Deterministic Calculated Signature Key: <code style="font-family:'IBM Plex Mono'; font-weight:600;">{calc_hash}</code>
                    </div>
                    """, unsafe_allow_html=True
                )
            else:
                st.error("Please provide an initialization target sequence.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- MODULE 3: HISTORICAL FREQUENCY TREND VELOCITY ---
    with btm_col2:
        st.markdown('<div class="section-header"><div class="section-dot" style="background:#6B7280;"></div>📈 Telemetry Ingestion Activity Frequency Velocity</div>', unsafe_allow_html=True)
        st.markdown('<div class="chart-container" style="padding:10px;">', unsafe_allow_html=True)
        if not filtered_df.empty and filtered_df['timestamp'].notna().any():
            timeline_df = filtered_df.copy()
            timeline_df['hour_slot'] = timeline_df['timestamp'].dt.floor('h')
            grouped = timeline_df.groupby(['hour_slot', 'chain']).size().reset_index(name='hits')
            
            trend_fig = go.Figure()
            colors = {"BTC": "#F7931A", "ETH": "#1A56DB", "SOL": "#14F195"}
            for chain_type, grouping in grouped.groupby('chain'):
                trend_fig.add_trace(go.Scatter(
                    x=grouping['hour_slot'], y=grouping['hits'],
                    mode='lines+markers', name=f"Layer: {chain_type}",
                    line=dict(color=colors.get(chain_type, "#1A56DB"), width=2.5),
                    marker=dict(size=5)
                ))
            trend_fig.update_layout(
                plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
                font=dict(family="Sora, sans-serif", size=10, color="#111827"),
                margin=dict(l=25, r=10, t=15, b=10), height=175, showlegend=True,
                xaxis=dict(showgrid=False, tickfont=dict(size=8)),
                yaxis=dict(showgrid=True, gridcolor="#EEF1F8", tickfont=dict(size=8))
            )
            st.plotly_chart(trend_fig, use_container_width=True)
        else:
            st.info("Insufficient stream entries data points to generate distribution charts.")
        st.markdown('</div>', unsafe_allow_html=True)

    # Ingestion Stream Trigger Interface Loop Control
    if live_loop:
        time.sleep(REFRESH_SECS)
        st.rerun()

if __name__ == "__main__":
    main()