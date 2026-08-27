# ==============================================================================
# MODULE 12: THE BENDER OVERRIDE v2 (E.S.V.E)
# Ethereum-Specific Viscosity Engine | Built by Chaotic Genius Warlord
# v2: Plotly visual layer + Signal Autopsy + Robustness Lab + cached data
# ==============================================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# ==========================================
# PAGE SETTINGS & HEADER
# ==========================================
st.set_page_config(page_title="Bender Override v2 (E.S.V.E)", layout="wide")

st.title("🛢️ MODULE 12: THE BENDER OVERRIDE v2 (E.S.V.E)")
st.markdown("**Powered by Warlord Jed Racho x Chaotic Genius Engine** | Ethereum-Specific Viscosity Engine")
st.info("💡 **LOGIC:** Ang makinang ito ay HINDI para sa lahat. Nakatono ang balbula nito para sa malapot at mabigat na liquidity ng Ethereum. May 7-Day Velocity trigger at Brutal Ejection Protocol para iwasan ang dambuhalang bear market drops!")

# --- BENDER'S CHEAT SHEET ---
with st.expander("📖 BENDER'S CHEAT SHEET (Ang Bagong Warlord Physics)", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("### 1. HPFO Z (Pressure)")
        st.caption("Lower Entry Threshold")
        st.write("🌊 **> +1.65:** Baha na! (Strong Buy).")
        st.write("💧 **< 0.0:** Tuyo na (Brutal Sell).")
    with col2:
        st.markdown("### 2. REYNOLDS (Flow)")
        st.caption("Viscosity Tolerance")
        st.write("🟢 **> 0.9:** Pasado sa ETH Slurry.")
        st.write("🔴 **< 0.9:** Magulong putik.")
    with col3:
        st.markdown("### 3. VELOCITY (Speed)")
        st.caption("The 7-Day Ejection")
        st.write("🚀 **> 0.015:** Kayang bayaran ang PDAX Fee.")
        st.write("💥 **< 0.0:** EMERGENCY EXIT (Bagsak!).")
    with col4:
        st.markdown("### 4. THE VALVE (Action)")
        st.caption("Warlord Command")
        st.write("🚰 **OPEN VALVE:** Saluhin ang baha!")
        st.write("⛔ **EMERGENCY EXIT:** Putulin ang linya!")

st.markdown("---")

# ==========================================
# CONFIGURATION
# ==========================================
WATCHLIST = [
    "BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "AVAX-USD",
    "XRP-USD", "XLM-USD", "LINK-USD",
    "DOGE-USD", "PEPE-USD", "SHIB-USD"
]
BACKTEST_TICKERS = ["ETH-USD", "BTC-USD", "SOL-USD", "XLM-USD", "XRP-USD", "ADA-USD"]

CAPITAL_PHP = st.sidebar.number_input("War Chest (PHP)", value=560000.0, step=10000.0)
FEE_RATE = 0.005  # 0.5% PDAX Fee

# --- Signal thresholds (the live logic uses these literal values) ---
HPFO_ENTRY = 1.65
REY_ENTRY = 0.9
REDLINE = 0.0
FRICTION_BARRIER = FEE_RATE * 3.0  # 0.015

# --- Visual palette ---
CLR_BUY = "#00ffcc"
CLR_HOLD = "#ffcc00"
CLR_EXIT = "#ff4d4d"
ACTION_COLORS = {
    "🚰 OPEN VALVE (BUY)": CLR_BUY,
    "⏳ MAINTAIN PRESSURE": CLR_HOLD,
    "⛔ EMERGENCY EXIT": CLR_EXIT,
}
PLOTLY_BASE_LAYOUT = dict(
    template="plotly_dark",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="white"),
)

st.write(f"⏳ **Live Scan Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# THE ALIEN PHYSICS ENGINE (E.S.V.E) — UNTOUCHED
# ==========================================
def engineer_eth_hydrodynamics(df):
    close = df['Close']
    volume = df['Volume'].replace(0, np.nan).ffill().fillna(1)
    
    log_close = np.log(close)
    velocity = log_close.diff(7) # 7-Day Window for Faster ETH reaction
    
    rho = volume / volume.rolling(50).mean()
    rho = rho.fillna(1.0)
    
    dynamic_pressure = 0.5 * rho * velocity * velocity.abs()
    
    daily_ret = log_close.diff(1)
    viscosity = daily_ret.rolling(20).std() * np.sqrt(7)
    viscosity = viscosity.replace(0, 1e-8).fillna(1e-8)
    
    reynolds = velocity.abs() / viscosity
    
    q_mean = dynamic_pressure.rolling(50).mean()
    q_std = dynamic_pressure.rolling(50).std().replace(0, 1e-8).fillna(1e-8)
    hpfo_z = (dynamic_pressure - q_mean) / q_std
    
    df['Velocity'] = velocity
    df['Reynolds'] = reynolds
    df['HPFO_Z'] = hpfo_z
    return df

# ==========================================
# DATA LAYER (cached — Yahoo gets hit once per 15 min, not per click)
# ==========================================
@st.cache_data(ttl=900, show_spinner=False)
def fetch_ohlcv(ticker, period="4y"):
    df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True)
    if df is None or df.empty:
        return pd.DataFrame()
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

@st.cache_data(ttl=900, show_spinner=False)
def load_engineered(ticker, period="4y"):
    df = fetch_ohlcv(ticker, period)
    if df.empty:
        return df
    return engineer_eth_hydrodynamics(df.copy())

# ==========================================
# BACKTEST ENGINE (same loop logic as the original matrix, parametrized)
# ==========================================
def run_bender_backtest(df, hpfo_thr=HPFO_ENTRY, rey_thr=REY_ENTRY, vel_thr=FRICTION_BARRIER, fee=FEE_RATE):
    buy_cond = (df['HPFO_Z'] > hpfo_thr) & (df['Reynolds'] > rey_thr) & (df['Velocity'] > vel_thr)
    sell_cond = (df['Velocity'] < 0) | (df['HPFO_Z'] < 0)

    raw = np.where(buy_cond, 1, np.where(sell_cond, 0, np.nan))
    raw = pd.Series(raw, index=df.index).ffill().fillna(0)
    target = raw.shift(1).fillna(0).values

    closes = df['Close'].values
    n = len(df)

    equity = np.ones(n)
    exposure = np.zeros(n)
    trades = []
    in_pos = False
    entry_equity = 1.0
    fee_events = 0

    for i in range(1, n):
        if in_pos:
            equity[i] = equity[i-1] * (closes[i] / closes[i-1])
            exposure[i] = 1.0
        else:
            equity[i] = equity[i-1]

        if not in_pos and target[i] == 1:
            equity[i] *= (1 - fee)
            fee_events += 1
            entry_equity = equity[i]
            in_pos = True
            exposure[i] = 1.0
        elif in_pos and target[i] == 0:
            equity[i] *= (1 - fee)
            fee_events += 1
            in_pos = False
            exposure[i] = 0.0
            trades.append((equity[i] / entry_equity) - 1.0)

    if in_pos:
        equity[-1] *= (1 - fee)
        fee_events += 1
        trades.append((equity[-1] / entry_equity) - 1.0)

    cum_max = np.maximum.accumulate(equity)
    drawdown = (equity / cum_max) - 1.0

    return {
        "equity": equity,
        "drawdown": drawdown,
        "trades": np.array(trades),
        "exposure": exposure,
        "target": target,
        "raw": raw.values,
        "fee_events": fee_events,
    }

def compute_kpis(res, closes, fee=FEE_RATE):
    eq = res["equity"]
    n = len(eq)
    trades = res["trades"]
    dd = res["drawdown"]

    algo_roi = (eq[-1] - 1.0) * 100
    hodl_roi = (closes[-1] / closes[0] - 1.0) * 100
    max_dd = np.min(dd) * 100

    rets = pd.Series(eq).pct_change().dropna()
    sharpe = (rets.mean() / rets.std()) * np.sqrt(365) if rets.std() > 0 else 0.0
    downside = rets[rets < 0].std()
    sortino = (rets.mean() / downside) * np.sqrt(365) if downside and downside > 0 else 0.0

    years = max(n / 365.0, 1e-9)
    ann_roi = ((eq[-1]) ** (1 / years) - 1.0) * 100 if eq[-1] > 0 else -100.0
    calmar = ann_roi / abs(max_dd) if max_dd < 0 else 0.0

    total = len(trades)
    wins = trades[trades > 0]
    losses = trades[trades <= 0]
    win_rate = (len(wins) / total) * 100 if total > 0 else 0.0
    gross_profit = np.sum(wins)
    gross_loss = np.abs(np.sum(losses))
    profit_factor = gross_profit / gross_loss if gross_loss > 0 else (99.9 if gross_profit > 0 else 0.0)
    avg_win = np.mean(wins) * 100 if len(wins) > 0 else 0.0
    avg_loss = np.mean(losses) * 100 if len(losses) > 0 else 0.0
    expectancy = np.mean(trades) * 100 if total > 0 else 0.0

    max_streak = streak = 0
    for t in trades:
        streak = streak + 1 if t <= 0 else 0
        max_streak = max(max_streak, streak)

    exposure = (np.sum(res["exposure"]) / n) * 100
    fee_drag = (1 - (1 - fee) ** res["fee_events"]) * 100
    underwater = (dd < 0).mean() * 100

    return dict(
        algo_roi=algo_roi, hodl_roi=hodl_roi, ann_roi=ann_roi, max_dd=max_dd,
        sharpe=sharpe, sortino=sortino, calmar=calmar,
        win_rate=win_rate, profit_factor=profit_factor, avg_win=avg_win, avg_loss=avg_loss,
        expectancy=expectancy, max_streak=max_streak, trades=total,
        exposure=exposure, fee_drag=fee_drag, underwater=underwater
    )

# ==========================================
# 1. LIVE SIGNAL DASHBOARD
# ==========================================
st.subheader("🎯 LIVE HYDRAULIC SIGNALS (Bender Override Status)")

with st.spinner('🤖 Bender is scanning the matrix for slurry pressure...'):
    live_results = []
    plot_data = []
    friction_barrier = FRICTION_BARRIER
    
    for ticker in WATCHLIST:
        try:
            df = load_engineered(ticker)
            if df.empty or len(df) < 200: continue
            
            current_price = float(df['Close'].iloc[-1])
            ma_200 = df['Close'].rolling(200).mean()
            ma200_val = float(ma_200.iloc[-1]) if len(ma_200.dropna()) > 0 else current_price
            dist_pct = ((current_price - ma200_val) / ma200_val) * 100

            delta = df['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / (loss + 1e-9)
            rsi = 100 - (100 / (1 + rs))
            rsi_val = float(rsi.iloc[-1])

            vel = float(df['Velocity'].iloc[-1])
            rey = float(df['Reynolds'].iloc[-1])
            hpfo = float(df['HPFO_Z'].iloc[-1])
            
            # BENDER'S ASYMMETRIC LOGIC
            if hpfo > 1.65 and rey > 0.9 and vel > friction_barrier:
                action = "🚰 OPEN VALVE (BUY)"
                allocation = f"₱{(CAPITAL_PHP * 0.25):,.2f} (25%)"
                comment = "Dambuhalang Baha! Front-run the herd!"
            elif vel < 0 or hpfo < 0:
                action = "⛔ EMERGENCY EXIT"
                allocation = "₱0.00"
                comment = "Bumabagsak ang agos! Brutal Ejection!"
            else:
                action = "⏳ MAINTAIN PRESSURE"
                allocation = "Hold Status"
                comment = "Nag-iipon ng bwelo ang malapot na tubig."
                
            coin_name = ticker.replace("-USD", "")
            
            live_results.append({
                "COIN": coin_name,
                "PRICE ($)": f"${current_price:,.2f}",
                "MA200 ($)": f"${ma200_val:,.2f}",
                "DIST %": f"{dist_pct:+.2f}%",
                "RSI": round(rsi_val, 1),
                "HPFO Z": round(hpfo, 2),
                "REYNOLDS": round(rey, 2),
                "VELOCITY": round(vel, 3),
                "ACTION 📢": action,
                "ALLOCATION": allocation,
                "COMMENTARY 💬": comment
            })
            plot_data.append({
                "COIN": coin_name, "Ticker": ticker, "Price": current_price,
                "HPFO_Z": hpfo, "Reynolds": rey, "Velocity": vel, "Action": action
            })
        except Exception:
            pass

    if live_results:
        df_live = pd.DataFrame(live_results)
        
        def color_coding(val):
            if isinstance(val, str):
                if "🚰" in val: return 'color: #00ffcc; font-weight: bold;'
                if "⛔" in val: return 'color: #ff4d4d; font-weight: bold;'
                if "⏳" in val: return 'color: #ffcc00;'
            return ''
            
        st.dataframe(df_live.style.map(color_coding), use_container_width=True)
    else:
        st.error("Market Data Unavailable.")

# ==========================================
# 2. THE VISUAL LAYER (Radar / Gauges / Rotation)
# ==========================================
if plot_data:
    df_plot = pd.DataFrame(plot_data).dropna(subset=["HPFO_Z", "Reynolds", "Velocity"])
    
    st.markdown("---")
    golden = df_plot[(df_plot["HPFO_Z"] > HPFO_ENTRY) & (df_plot["Reynolds"] > REY_ENTRY)]
    hottest = df_plot.loc[df_plot["Velocity"].idxmax()]
    coldest = df_plot.loc[df_plot["Velocity"].idxmin()]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("🟡 Coins in Golden Quadrant", f"{len(golden)} / {len(df_plot)}")
    m2.metric("🔥 Hottest Velocity", hottest["COIN"], f"{hottest['Velocity']:+.3f}")
    m3.metric("🧊 Coldest Velocity", coldest["COIN"], f"{coldest['Velocity']:+.3f}")
    m4.metric("⛔ Below Redline (HPFO < 0)", f"{int((df_plot['HPFO_Z'] < REDLINE).sum())}")

    # --- A. THERMODYNAMIC RADAR ---
    st.markdown("---")
    st.subheader("📡 THERMODYNAMIC RADAR (Pressure vs Flow)")
    st.caption("X = HPFO Z (Pressure) | Y = Reynolds (Flow) | Upper-right shaded box = 🟡 GOLDEN QUADRANT | Left of the red dotted line = 💀 Ejection zone")

    x_max = max(3.0, float(df_plot["HPFO_Z"].max()) * 1.15 + 0.2)
    x_min = min(-1.0, float(df_plot["HPFO_Z"].min()) * 1.15 - 0.2)
    y_max = max(2.0, float(df_plot["Reynolds"].max()) * 1.15 + 0.1)
    y_min = 0.0

    fig_radar = go.Figure()
    fig_radar.add_shape(type="rect", x0=HPFO_ENTRY, x1=x_max, y0=REY_ENTRY, y1=y_max,
                        fillcolor=CLR_HOLD, opacity=0.13, line_width=0, layer="below")
    fig_radar.add_shape(type="rect", x0=x_min, x1=REDLINE, y0=y_min, y1=y_max,
                        fillcolor=CLR_EXIT, opacity=0.08, line_width=0, layer="below")
    fig_radar.add_vline(x=HPFO_ENTRY, line_dash="dash", line_color=CLR_HOLD, line_width=2,
                        annotation_text=f"HPFO Z = {HPFO_ENTRY}", annotation_position="top",
                        annotation_font_color=CLR_HOLD)
    fig_radar.add_hline(y=REY_ENTRY, line_dash="dash", line_color=CLR_BUY, line_width=2,
                        annotation_text=f"Reynolds = {REY_ENTRY}", annotation_position="right",
                        annotation_font_color=CLR_BUY)
    fig_radar.add_vline(x=REDLINE, line_dash="dot", line_color=CLR_EXIT, line_width=2,
                        annotation_text="EJECT REDLINE", annotation_position="bottom",
                        annotation_font_color=CLR_EXIT)
    fig_radar.add_annotation(x=x_max, y=y_max, text="🟡 GOLDEN QUADRANT", showarrow=False,
                             xanchor="right", yanchor="top", font=dict(color=CLR_HOLD, size=13))

    for action, grp in df_plot.groupby("Action"):
        fig_radar.add_trace(go.Scatter(
            x=grp["HPFO_Z"], y=grp["Reynolds"], mode="markers+text",
            text=grp["COIN"], textposition="top center",
            textfont=dict(color="white", size=11), name=action,
            marker=dict(size=15, color=ACTION_COLORS.get(action, "#ffffff"),
                        line=dict(width=1, color="white"),
                        symbol="diamond" if "🚰" in action else "circle"),
            customdata=np.stack([grp["Velocity"], grp["Price"]], axis=-1),
            hovertemplate=("<b>%{text}</b><br>HPFO Z: %{x:.2f}<br>Reynolds: %{y:.2f}<br>"
                           "Velocity: %{customdata[0]:+.3f}<br>Price: $%{customdata[1]:,.2f}<extra></extra>")
        ))
    fig_radar.update_layout(
        **PLOTLY_BASE_LAYOUT, height=540,
        xaxis=dict(title="HPFO Z-Score (Dynamic Pressure)", range=[x_min, x_max], gridcolor="#333333", zeroline=False),
        yaxis=dict(title="Reynolds Number (Flow / Viscosity)", range=[y_min, y_max], gridcolor="#333333", zeroline=False),
        legend=dict(orientation="h", yanchor="bottom", y=-0.22, xanchor="center", x=0.5),
        margin=dict(l=40, r=40, t=50, b=40), hovermode="closest"
    )
    st.plotly_chart(fig_radar, use_container_width=True)

    # --- B. PRESSURE GAUGES ---
    st.markdown("---")
    st.subheader("🏎️ PRESSURE GAUGES (Top Holdings vs Emergency Exit Redline)")
    st.caption("Needle = current HPFO Z. Red band = below 0.0 redline (Brutal Ejection). Delta = distance from redline.")

    available_coins = df_plot["COIN"].tolist()
    default_gauges = [c for c in ["BTC", "SOL"] if c in available_coins]
    gauge_coins = st.sidebar.multiselect("🏎️ Gauge Holdings", options=available_coins, default=default_gauges,
                                         help="Piliin ang mga holdings na gusto mong bantayan sa speedometer.")

    def build_gauge(coin, hpfo, action):
        bar_color = CLR_BUY if hpfo >= HPFO_ENTRY else (CLR_HOLD if hpfo >= REDLINE else CLR_EXIT)
        axis_max = max(3.0, abs(hpfo) * 1.2)
        axis_min = -axis_max
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta", value=hpfo,
            number={"suffix": " σ", "font": {"color": bar_color, "size": 42}},
            delta={"reference": REDLINE, "increasing": {"color": CLR_BUY},
                   "decreasing": {"color": CLR_EXIT}, "suffix": " vs Redline"},
            title={"text": f"<b>{coin}</b> — HPFO Z<br><span style='font-size:0.75em;color:#aaaaaa'>{action}</span>",
                   "font": {"color": "white"}},
            gauge={
                "axis": {"range": [axis_min, axis_max],
                         "tickvals": [axis_min, REDLINE, HPFO_ENTRY, axis_max],
                         "ticktext": [f"{axis_min:.1f}", "0.0 ⛔", "1.65 🚰", f"{axis_max:.1f}"],
                         "tickcolor": "white", "tickfont": {"color": "white"}},
                "bar": {"color": bar_color, "thickness": 0.3},
                "bgcolor": "rgba(0,0,0,0)", "borderwidth": 1, "bordercolor": "#444444",
                "steps": [
                    {"range": [axis_min, REDLINE], "color": "rgba(255,77,77,0.40)"},
                    {"range": [REDLINE, HPFO_ENTRY], "color": "rgba(255,204,0,0.22)"},
                    {"range": [HPFO_ENTRY, axis_max], "color": "rgba(0,255,204,0.22)"},
                ],
                "threshold": {"line": {"color": CLR_EXIT, "width": 5}, "thickness": 0.9, "value": REDLINE},
            }
        ))
        fig.update_layout(**PLOTLY_BASE_LAYOUT, height=330, margin=dict(l=30, r=30, t=90, b=20))
        return fig

    if gauge_coins:
        gauge_cols = st.columns(len(gauge_coins))
        for col, coin in zip(gauge_cols, gauge_coins):
            row = df_plot[df_plot["COIN"] == coin].iloc[0]
            with col:
                st.plotly_chart(build_gauge(coin, float(row["HPFO_Z"]), row["Action"]), use_container_width=True)
    else:
        st.warning("Walang piniling holdings para sa gauges. Pumili sa sidebar.")

    # --- C. KINETIC CAPITAL ROTATION ---
    st.markdown("---")
    st.subheader("🌪️ KINETIC CAPITAL ROTATION (7-Day Velocity Ranking)")
    st.caption(f"Sorted highest → lowest. Green = liquidity flowing IN, Red = flowing OUT. Yellow line = friction barrier ({FRICTION_BARRIER:.3f}), red line = 0.0 ejection.")

    df_vel = df_plot.sort_values("Velocity", ascending=False).reset_index(drop=True)
    v_abs_max = max(abs(float(df_vel["Velocity"].max())), abs(float(df_vel["Velocity"].min())), 0.05)

    fig_vel = px.bar(
        df_vel, x="COIN", y="Velocity", color="Velocity",
        color_continuous_scale=["#8b0000", CLR_EXIT, "#2b2b2b", "#00cc66", CLR_BUY],
        range_color=[-v_abs_max, v_abs_max],
        text=df_vel["Velocity"].map(lambda v: f"{v:+.3f}"),
        custom_data=["Action", "HPFO_Z", "Reynolds"]
    )
    fig_vel.update_traces(
        textposition="outside", textfont=dict(color="white", size=11),
        marker_line=dict(width=1, color="#555555"),
        hovertemplate=("<b>%{x}</b><br>7-Day Velocity: %{y:+.3f}<br>HPFO Z: %{customdata[1]:.2f}<br>"
                       "Reynolds: %{customdata[2]:.2f}<br>%{customdata[0]}<extra></extra>")
    )
    fig_vel.add_hline(y=FRICTION_BARRIER, line_dash="dash", line_color=CLR_HOLD, line_width=2,
                      annotation_text=f"Friction Barrier {FRICTION_BARRIER:.3f}",
                      annotation_position="top right", annotation_font_color=CLR_HOLD)
    fig_vel.add_hline(y=0.0, line_color=CLR_EXIT, line_width=2, annotation_text="EJECT (< 0)",
                      annotation_position="bottom right", annotation_font_color=CLR_EXIT)
    fig_vel.update_layout(
        **PLOTLY_BASE_LAYOUT, height=480,
        xaxis=dict(title="", categoryorder="array", categoryarray=df_vel["COIN"].tolist()),
        yaxis=dict(title="7-Day Log Velocity", gridcolor="#333333", zeroline=False),
        coloraxis_colorbar=dict(title="Velocity", tickformat="+.3f"),
        margin=dict(l=40, r=40, t=50, b=40), showlegend=False
    )
    st.plotly_chart(fig_vel, use_container_width=True)

    # ==========================================
    # 3. SIGNAL AUTOPSY (where did the valve actually fire?)
    # ==========================================
    st.markdown("---")
    st.subheader("🔬 SIGNAL AUTOPSY (Saan Nagpaputok ang Balbula?)")
    st.caption("Price + shaded in-position windows + entry/exit markers, with the HPFO Z and Velocity that caused them. Shared x-axis — hover anywhere.")

    ac1, ac2 = st.columns([1, 4])
    with ac1:
        coin_list = df_plot["COIN"].tolist()
        autopsy_coin = st.selectbox("Coin", coin_list, index=coin_list.index("ETH") if "ETH" in coin_list else 0)
        lookback = st.slider("Lookback (days)", min_value=90, max_value=1460, value=365, step=30)

    autopsy_ticker = df_plot.loc[df_plot["COIN"] == autopsy_coin, "Ticker"].iloc[0]
    df_a = load_engineered(autopsy_ticker).copy()
    res_a = run_bender_backtest(df_a)
    df_a["Target_Pos"] = res_a["target"]
    df_a["Raw_Signal"] = res_a["raw"]
    tail = df_a.iloc[-lookback:].copy()
    sig_change = tail["Raw_Signal"].diff()
    entries = tail.index[sig_change == 1]
    exits = tail.index[sig_change == -1]

    fig_auto = make_subplots(
        rows=3, cols=1, shared_xaxes=True, row_heights=[0.5, 0.25, 0.25], vertical_spacing=0.04,
        subplot_titles=(f"{autopsy_coin} Price ($)", "HPFO Z (Pressure)", "7-Day Velocity")
    )
    # shaded in-position windows
    pos = tail["Target_Pos"].values
    idx = tail.index
    i = 0
    while i < len(pos):
        if pos[i] == 1:
            j = i
            while j + 1 < len(pos) and pos[j + 1] == 1:
                j += 1
            fig_auto.add_vrect(x0=idx[i], x1=idx[j], fillcolor=CLR_HOLD, opacity=0.10, line_width=0, row="all", col=1)
            i = j + 1
        else:
            i += 1

    fig_auto.add_trace(go.Scatter(x=tail.index, y=tail["Close"], mode="lines", name="Close",
                                  line=dict(color="#dddddd", width=1.6)), row=1, col=1)
    fig_auto.add_trace(go.Scatter(x=entries, y=tail.loc[entries, "Close"], mode="markers", name="🚰 Entry",
                                  marker=dict(symbol="triangle-up", size=13, color=CLR_BUY, line=dict(width=1, color="white"))), row=1, col=1)
    fig_auto.add_trace(go.Scatter(x=exits, y=tail.loc[exits, "Close"], mode="markers", name="⛔ Exit",
                                  marker=dict(symbol="triangle-down", size=13, color=CLR_EXIT, line=dict(width=1, color="white"))), row=1, col=1)

    fig_auto.add_trace(go.Scatter(x=tail.index, y=tail["HPFO_Z"], mode="lines", name="HPFO Z",
                                  line=dict(color=CLR_HOLD, width=1.4)), row=2, col=1)
    fig_auto.add_hline(y=HPFO_ENTRY, line_dash="dash", line_color=CLR_BUY, row=2, col=1)
    fig_auto.add_hline(y=REDLINE, line_dash="dot", line_color=CLR_EXIT, row=2, col=1)

    vel_colors = np.where(tail["Velocity"] > FRICTION_BARRIER, CLR_BUY, np.where(tail["Velocity"] < 0, CLR_EXIT, CLR_HOLD))
    fig_auto.add_trace(go.Bar(x=tail.index, y=tail["Velocity"], name="Velocity", marker_color=vel_colors, opacity=0.85), row=3, col=1)
    fig_auto.add_hline(y=FRICTION_BARRIER, line_dash="dash", line_color=CLR_HOLD, row=3, col=1)
    fig_auto.add_hline(y=0.0, line_color=CLR_EXIT, row=3, col=1)

    fig_auto.update_layout(**PLOTLY_BASE_LAYOUT, height=760, hovermode="x unified", bargap=0,
                           legend=dict(orientation="h", y=1.04, x=0), margin=dict(l=40, r=40, t=60, b=30))
    fig_auto.update_xaxes(gridcolor="#333333")
    fig_auto.update_yaxes(gridcolor="#333333", zeroline=False)
    st.plotly_chart(fig_auto, use_container_width=True)

    k_a = compute_kpis(res_a, df_a["Close"].values)
    ka1, ka2, ka3, ka4 = st.columns(4)
    ka1.metric("Entries in window", f"{len(entries)}")
    ka2.metric("Exits in window", f"{len(exits)}")
    ka3.metric("4Y Expectancy / trade", f"{k_a['expectancy']:+.2f}%")
    ka4.metric("4Y Fee Drag", f"-{k_a['fee_drag']:.1f}%")

# ==========================================
# 4. THE WARLORD BACKTEST MATRIX (extended KPIs)
# ==========================================
st.markdown("---")
st.subheader("📊 4-YEAR BACKTEST: BENDER OVERRIDE (0.5% Fee Imposed)")

with st.expander("Tignan ang 4-Year Lab Report & Drawdown Graphs", expanded=False):
    st.write("🤖 *Executing Warlord Physics Simulation...*")
    
    plt.style.use('dark_background')
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle("E.S.V.E Engine vs Buy & Hold", fontsize=16, fontweight='bold', color='white')
    axes = axes.flatten()

    fig_dd, axes_dd = plt.subplots(2, 2, figsize=(16, 6))
    fig_dd.suptitle("🌊 UNDERWATER DRAWDOWN (Bender Ejection Status)", fontsize=16, fontweight='bold', color='#ff4d4d')
    axes_dd = axes_dd.flatten()
    
    bt_results = []

    with st.spinner("Executing Thermodynamic Audits..."):
        for idx, ticker in enumerate(BACKTEST_TICKERS):
            df = load_engineered(ticker)
            if df.empty or len(df) < 500: continue
            df = df.copy()

            res = run_bender_backtest(df)
            closes = df['Close'].values
            df['Target_Pos'] = res['target']
            df['Equity'] = res['equity']
            drawdown = res['drawdown']
            k = compute_kpis(res, closes)

            bt_results.append({
                "Asset": ticker.replace("-USD", ""),
                "Raw_ROI": k["algo_roi"],
                "Algo ROI": f"{k['algo_roi']:.1f}%",
                "HODL ROI": f"{k['hodl_roi']:.1f}%",
                "Ann. ROI": f"{k['ann_roi']:.1f}%",
                "Max DD": f"{k['max_dd']:.1f}%",
                "Sharpe": f"{k['sharpe']:.2f}",
                "Sortino": f"{k['sortino']:.2f}",
                "Calmar": f"{k['calmar']:.2f}",
                "Win Rate": f"{k['win_rate']:.1f}%",
                "Profit Fctr": f"{k['profit_factor']:.2f}",
                "Expect./Trade": f"{k['expectancy']:+.2f}%",
                "Avg Win": f"+{k['avg_win']:.1f}%",
                "Avg Loss": f"{k['avg_loss']:.1f}%",
                "Max L-Streak": k["max_streak"],
                "Trades": k["trades"],
                "Exposure": f"{k['exposure']:.1f}%",
                "Fee Drag": f"-{k['fee_drag']:.1f}%",
                "Time Underwater": f"{k['underwater']:.0f}%"
            })

            if idx < 4:
                ax = axes[idx]
                ax.plot(df.index, df['Equity'], label='Bender Override', color='#ffcc00', linewidth=2)
                ax.plot(df.index, closes/closes[0], label='Buy & Hold', color='#777777', linewidth=1.5, alpha=0.8)
                ax.fill_between(df.index, df['Equity'].min(), df['Equity'].max(), where=df['Target_Pos']==1, color='#ffcc00', alpha=0.1)
                ax.set_title(f"{ticker.replace('-USD', '')}", fontsize=12, fontweight='bold', color='white')
                ax.legend(loc='upper left', frameon=False, labelcolor='white')
                ax.grid(True, color='#333333', linestyle='--', alpha=0.5)
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                
                ax_dd = axes_dd[idx]
                ax_dd.fill_between(df.index, drawdown*100, 0, color='#ff4d4d', alpha=0.3)
                ax_dd.plot(df.index, drawdown*100, color='#ff4d4d', linewidth=1.2)
                ax_dd.set_title(f"{ticker.replace('-USD', '')} Drawdown %", fontsize=11, color='white')
                ax_dd.grid(True, color='#333333', linestyle='--', alpha=0.5)
                ax_dd.spines['top'].set_visible(False)
                ax_dd.spines['right'].set_visible(False)

    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    fig_dd.tight_layout()
    fig_dd.subplots_adjust(top=0.90)
    
    st.pyplot(fig)
    st.markdown("<br>", unsafe_allow_html=True)
    st.pyplot(fig_dd)
    
    st.markdown("### 🏆 THE BENDER LAB REPORT (SORTED BY DOMINANCE)")
    st.caption("Calmar = annualized ROI ÷ |Max DD| (higher = pain-adjusted profit). Expectancy = average % per trade after fees. Fee Drag = total equity burned on PDAX fees. Time Underwater = % of days below the previous equity peak.")
    if bt_results:
        df_report = pd.DataFrame(bt_results)
        df_report = df_report.sort_values(by="Raw_ROI", ascending=False).drop(columns=["Raw_ROI"]).reset_index(drop=True)
        st.dataframe(df_report, use_container_width=True)

# ==========================================
# 5. ROBUSTNESS LAB (overfit or not — let the data testify)
# ==========================================
st.markdown("---")
st.subheader("🧪 ROBUSTNESS LAB (Overfit Detector)")
st.caption("Two tests. (1) In-sample vs out-of-sample: rules tuned on the first 70% — do they survive the last 30% they've never seen? (2) Parameter sweep: is 1.65 / 0.9 a stable plateau or a lonely island?")

HPFO_GRID = (1.00, 1.25, 1.50, 1.65, 2.00, 2.25, 2.50)
REY_GRID = (0.50, 0.70, 0.90, 1.10, 1.30, 1.50)

@st.cache_data(ttl=900, show_spinner=False)
def parameter_sweep(ticker, hpfo_grid, rey_grid):
    df = load_engineered(ticker)
    if df.empty or len(df) < 500:
        return None
    closes = df['Close'].values
    hodl = (closes[-1] / closes[0] - 1.0) * 100
    z_roi = np.zeros((len(rey_grid), len(hpfo_grid)))
    z_dd = np.zeros((len(rey_grid), len(hpfo_grid)))
    z_tr = np.zeros((len(rey_grid), len(hpfo_grid)))
    for i, r in enumerate(rey_grid):
        for j, h in enumerate(hpfo_grid):
            res = run_bender_backtest(df, hpfo_thr=h, rey_thr=r)
            z_roi[i, j] = (res["equity"][-1] - 1.0) * 100
            z_dd[i, j] = np.min(res["drawdown"]) * 100
            z_tr[i, j] = len(res["trades"])
    return z_roi, z_dd, z_tr, hodl

with st.expander("Buksan ang Robustness Lab", expanded=False):
    lab_ticker = st.selectbox("Asset under audit", BACKTEST_TICKERS, index=0, format_func=lambda t: t.replace("-USD", ""))
    df_lab = load_engineered(lab_ticker)

    if df_lab.empty or len(df_lab) < 500:
        st.error("Kulang ang data para sa audit.")
    else:
        df_lab = df_lab.copy()
        n_lab = len(df_lab)
        split = int(n_lab * 0.70)
        df_is = df_lab.iloc[:split]
        df_oos = df_lab.iloc[split:]

        res_is = run_bender_backtest(df_is)
        res_oos = run_bender_backtest(df_oos)
        k_is = compute_kpis(res_is, df_is['Close'].values)
        k_oos = compute_kpis(res_oos, df_oos['Close'].values)

        st.markdown(f"### ⏱️ Test 1 — In-Sample vs Out-of-Sample ({lab_ticker.replace('-USD','')})")
        st.caption(f"In-sample: {df_is.index[0].date()} → {df_is.index[-1].date()} | Out-of-sample: {df_oos.index[0].date()} → {df_oos.index[-1].date()}")

        oos_table = pd.DataFrame({
            "Metric": ["Algo ROI", "HODL ROI", "Ann. ROI", "Max DD", "Sharpe", "Calmar", "Win Rate", "Expect./Trade", "Trades", "Exposure"],
            "In-Sample (70%)": [f"{k_is['algo_roi']:.1f}%", f"{k_is['hodl_roi']:.1f}%", f"{k_is['ann_roi']:.1f}%", f"{k_is['max_dd']:.1f}%",
                                f"{k_is['sharpe']:.2f}", f"{k_is['calmar']:.2f}", f"{k_is['win_rate']:.1f}%", f"{k_is['expectancy']:+.2f}%",
                                k_is['trades'], f"{k_is['exposure']:.1f}%"],
            "Out-of-Sample (30%)": [f"{k_oos['algo_roi']:.1f}%", f"{k_oos['hodl_roi']:.1f}%", f"{k_oos['ann_roi']:.1f}%", f"{k_oos['max_dd']:.1f}%",
                                    f"{k_oos['sharpe']:.2f}", f"{k_oos['calmar']:.2f}", f"{k_oos['win_rate']:.1f}%", f"{k_oos['expectancy']:+.2f}%",
                                    k_oos['trades'], f"{k_oos['exposure']:.1f}%"],
        })
        st.dataframe(oos_table, use_container_width=True, hide_index=True)

        fig_oos = go.Figure()
        fig_oos.add_trace(go.Scatter(x=df_is.index, y=res_is["equity"], name="In-Sample Equity", line=dict(color=CLR_HOLD, width=2)))
        fig_oos.add_trace(go.Scatter(x=df_oos.index, y=res_oos["equity"], name="Out-of-Sample Equity (restarts at 1.0)", line=dict(color=CLR_BUY, width=2)))
        fig_oos.add_trace(go.Scatter(x=df_lab.index, y=df_lab['Close'].values / df_lab['Close'].values[0], name="Buy & Hold",
                                     line=dict(color="#777777", width=1.2, dash="dot")))
        fig_oos.add_vline(x=df_oos.index[0], line_dash="dash", line_color=CLR_EXIT,
                          annotation_text="OOS starts", annotation_position="top", annotation_font_color=CLR_EXIT)
        fig_oos.update_layout(**PLOTLY_BASE_LAYOUT, height=380, yaxis_title="Equity (×)",
                              legend=dict(orientation="h", y=-0.2), margin=dict(l=40, r=40, t=40, b=40))
        fig_oos.update_xaxes(gridcolor="#333333")
        fig_oos.update_yaxes(gridcolor="#333333")
        st.plotly_chart(fig_oos, use_container_width=True)

        if k_is['algo_roi'] > 0 and k_oos['algo_roi'] <= 0:
            st.error("💀 OVERFIT SMELL: Kumita in-sample, natalo out-of-sample. Ang rules ay naka-memorize sa nakaraan, hindi naka-generalize.")
        elif k_oos['algo_roi'] > 0 and k_oos['algo_roi'] >= k_oos['hodl_roi']:
            st.success("✅ SURVIVED: Positive OOS at tinalo ang HODL sa data na hindi niya nakita. Pasado sa unang test.")
        elif k_oos['algo_roi'] > 0:
            st.warning("⚠️ MIXED: Positive OOS pero natalo ng HODL. Kumikita ang balbula pero mas kumita ang tulog na meatbag.")
        else:
            st.error("💀 FAILED: Negative sa OOS at negative sa IS. Ang problema ay hindi overfitting — ang problema ay ang rules mismo.")

        st.markdown("---")
        st.markdown("### 🗺️ Test 2 — Parameter Sweep (HPFO entry × Reynolds entry)")
        st.caption("Bawat cell = 4Y Algo ROI kung ito ang thresholds. ⭐ = ang current config mo (1.65 / 0.9). Exit rules (Velocity < 0 | HPFO < 0) at friction barrier constant sa lahat ng cell.")

        with st.spinner("Sweeping 42 parameter combos..."):
            sweep = parameter_sweep(lab_ticker, HPFO_GRID, REY_GRID)

        if sweep is not None:
            z_roi, z_dd, z_tr, hodl_lab = sweep
            x_lbl = [f"{h:.2f}" for h in HPFO_GRID]
            y_lbl = [f"{r:.2f}" for r in REY_GRID]
            cur_i = REY_GRID.index(REY_ENTRY)
            cur_j = HPFO_GRID.index(HPFO_ENTRY)
            cur_roi = z_roi[cur_i, cur_j]

            fig_sweep = go.Figure(data=go.Heatmap(
                z=z_roi, x=x_lbl, y=y_lbl,
                colorscale="RdYlGn", zmid=0,
                text=np.round(z_roi, 0).astype(int), texttemplate="%{text}%",
                textfont={"size": 12, "color": "black"},
                customdata=np.dstack([z_dd, z_tr]),
                hovertemplate="HPFO > %{x} | Reynolds > %{y}<br>Algo ROI: %{z:.1f}%<br>Max DD: %{customdata[0]:.1f}%<br>Trades: %{customdata[1]:.0f}<extra></extra>",
                colorbar=dict(title="ROI %")
            ))
            fig_sweep.add_trace(go.Scatter(x=[x_lbl[cur_j]], y=[y_lbl[cur_i]], mode="markers+text", text=["⭐"],
                                           textfont=dict(size=22), marker=dict(size=1, color="rgba(0,0,0,0)"),
                                           showlegend=False, hoverinfo="skip"))
            fig_sweep.update_layout(**PLOTLY_BASE_LAYOUT, height=440,
                                    xaxis=dict(title="HPFO Z entry threshold", type="category"),
                                    yaxis=dict(title="Reynolds entry threshold", type="category"),
                                    margin=dict(l=40, r=40, t=30, b=40))
            st.plotly_chart(fig_sweep, use_container_width=True)

            pct_positive = (z_roi > 0).mean() * 100
            pct_beat_hodl = (z_roi > hodl_lab).mean() * 100
            i0, i1 = max(0, cur_i - 1), min(len(REY_GRID), cur_i + 2)
            j0, j1 = max(0, cur_j - 1), min(len(HPFO_GRID), cur_j + 2)
            neighborhood = z_roi[i0:i1, j0:j1]
            neigh_mean = (neighborhood.sum() - cur_roi) / max(neighborhood.size - 1, 1)

            s1, s2, s3, s4 = st.columns(4)
            s1.metric("⭐ Current config ROI", f"{cur_roi:.1f}%")
            s2.metric("Neighbor avg ROI", f"{neigh_mean:.1f}%", f"{cur_roi - neigh_mean:+.1f}% vs current")
            s3.metric("% of grid profitable", f"{pct_positive:.0f}%")
            s4.metric("% of grid beating HODL", f"{pct_beat_hodl:.0f}%")

            if cur_roi > 0 and neigh_mean <= 0:
                st.error("💀 ISLAND DETECTED: Ang 1.65/0.9 lang ang green, pula ang mga kapitbahay. Classic overfit signature — isang tick ng noise at wala na.")
            elif cur_roi > 0 and cur_roi > 2.0 * max(neigh_mean, 1e-9):
                st.warning("⚠️ PEAK, HINDI PLATEAU: Profitable ang paligid pero doble ang ROI mo sa kapitbahay. Ang kalahati ng edge mo ay malamang swerte ng specific cutoff.")
            elif cur_roi > 0 and neigh_mean > 0:
                st.success("✅ PLATEAU: Profitable ang current config AT ang mga kapitbahay. Hindi sensitive sa exact cutoff — iyan ang tunay na robustness, hindi ang README.")
            else:
                st.error("💀 Negative ang current config sa sweep. Balik sa drawing board, Warlord.")

st.markdown("---")
st.subheader("🍺 BENDER'S FINAL WORD: Ito ang purong pisika ng Warlord Supremacy. Kung papangit ang performance sa ibang coins, ibig sabihin hindi sila Ethereum! Dismissed.")
