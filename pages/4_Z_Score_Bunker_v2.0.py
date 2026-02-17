import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# --- PAGE SETTINGS ---
st.set_page_config(page_title="Z-Score Bunker", layout="wide")

# --- PATCH: CYBERPUNK WARLORD GUI INJECTION ---
st.markdown("""
<style>
    /* 1. Matrix Dark Background */
    .stApp {
        background-color: #0b0f19;
        font-family: 'Courier New', Courier, monospace;
    }
    
    /* 2. Glowing Warlord Titles */
    h1, h2, h3 {
        color: #00ffcc !important;
        text-shadow: 0 0 10px rgba(0, 255, 204, 0.4);
        font-family: 'Courier New', Courier, monospace;
        letter-spacing: 1px;
    }
    
    /* 3. Titanium Info Box (Yung Logic sa taas) */
    div[data-testid="stAlert"] {
        background-color: rgba(0, 255, 204, 0.05) !important;
        border: 1px solid #374151 !important;
        border-left: 5px solid #00ffcc !important;
        color: #e5e7eb !important;
    }
    
    /* 4. Bunker Expander (Cheat Sheet Box) */
    div[data-testid="stExpander"] {
        background-color: #111827 !important;
        border: 1px solid #00ffcc !important;
        box-shadow: 0 0 10px rgba(0, 255, 204, 0.1);
        border-radius: 5px;
    }
    
    /* 5. Sidebar Command Center */
    section[data-testid="stSidebar"] {
        background-color: #080b12 !important;
        border-right: 1px dashed #00ffcc;
    }
    
    /* 6. Neon Glow sa Tables */
    div[data-testid="stDataFrame"] {
        border: 1px solid #374151;
        border-radius: 5px;
        box-shadow: 0 0 15px rgba(0, 255, 204, 0.15);
    }
    
    /* 7. Base Text Color */
    p, span, div {
        color: #d1d5db;
    }
</style>
""", unsafe_allow_html=True)

st.title("🛡️ MODULE 4: THE Z-SCORE BUNKER (REALITY PATCH)")
st.markdown("**Powered by Tycoon Jed Racho & Bender AI** | The Shock-Absorber Protocol")
st.info("💡 **LOGIC:** Ang makinang ito ay isang Warlord Momentum Engine. Nakakabit sa MA200 Bunker. Ngayon, may kasama nang 0.5% Trading Fees at Max Leverage Cap (1.5x) para sa totoong Warlord simulation.")

# --- PATCH: BENDER'S CHEAT SHEET (Added Here) ---
with st.expander("📖 BENDER'S CHEAT SHEET (Paano Basahin 'To)", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("### 1. MA200 (The Floor)")
        st.caption("Ang Sahig ng Market.")
        st.write("📉 **Ilalim:** Cash is King.")
        st.write("📈 **Ibabaw:** Party Time.")
    with col2:
        st.markdown("### 2. DIST % (The Dive)")
        st.caption("Layo mula sa MA200.")
        st.write("🟥 **Negative:** Nasa ilalim ng tubig.")
        st.write("🟩 **Positive:** Nasa himpapawid.")
    with col3:
        st.markdown("### 3. RSI (The Price)")
        st.caption("Mura o Mahal?")
        st.write("🛍️ **< 30:** SALE (Mura).")
        st.write("💸 **> 70:** SCAM (Mahal).")
    with col4:
        st.markdown("### 4. Z-SCORE (The Force)")
        st.caption("Ang Bwelo ng Trend.")
        st.write("🚀 **Positive:** Paakyat.")
        st.write("💤 **Negative:** Pahinga/Bagsak.")

st.markdown("---")

# --- CONFIGURATION ---
WATCHLIST = ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD"]
CAPITAL_PHP = st.sidebar.number_input("War Chest (PHP)", value=50000.0, step=5000.0)

st.write(f"⏳ **Live Scan Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# 1. LIVE SIGNAL DASHBOARD (CURRENT STATE)
# ==========================================
st.subheader("🎯 LIVE Z-SCORE SIGNALS")

with st.spinner('🤖 Bender is scanning the Z-Score Matrix...'):
    live_results = []
    
    for ticker in WATCHLIST:
        try:
            df = yf.download(ticker, period="1y", interval="1d", progress=False, auto_adjust=True)
            if len(df) < 200: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            close = df["Close"]
            current_price = float(close.iloc[-1])
            
            # Z-Score Math
            # --- MATH INDICATORS ---
            ma_200 = close.rolling(200).mean()
            ma_50 = close.rolling(50).mean()
            
            # PATCH: DISTANCE % FROM MA200
            ma200_val = float(ma_200.iloc[-1])
            dist_pct = ((current_price - ma200_val) / ma200_val) * 100

            # PATCH: RSI CALCULATION (14-Day)
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_val = float(rsi.iloc[-1])

            # Z-Score Math (UNCHANGED)
            trend_diff = np.log(close / ma_50)
            # ... (tuloy ang dating code hanggang sa allocation computation) ...
            
            trend_diff = np.log(close / ma_50)
            z_score = (trend_diff - trend_diff.rolling(120).mean()) / (trend_diff.rolling(120).std() + 1e-9)
            
            ret = close.pct_change().fillna(0.0)
            downside_ret = ret.copy()
            downside_ret[downside_ret > 0] = 0.0
            
            # PATCH: Lalagyan natin ng floor ang volatility para hindi mabaliw
            downside_vol = downside_ret.rolling(20).std() * np.sqrt(365)
            downside_vol = downside_vol.clip(lower=0.15) 
            
            target_vol = 0.75
            vol_scalar = (target_vol / (downside_vol + 1e-9)).clip(0, 3.0)
            
            # ORIGINAL WARLORD LOGIC (Trend Riding)
            risk_scaler = (z_score / 2.0).clip(0, 1.0)
            
            # PATCH: Binabaan ang limit ng tapak sa gasolina from 3.0 to 1.5
            lev_target_raw = (vol_scalar * risk_scaler).clip(0, 1.5)
            
            # PATCH: Nilagyan ng Shock Absorber (EWMA) para di malikot
            lev_target = lev_target_raw.ewm(span=5).mean()
            
            # Concrete Floor Guard
            if current_price < float(ma_200.iloc[-1]):
                final_lev = 0.0
            else:
                final_lev = float(lev_target.iloc[-1])
            
            # Action Logic
            if final_lev == 0.0:
                action = "⛔ CASH / EXIT"
            elif final_lev < 0.5:
                action = "⚠️ WEAK BUY (Pre-Pump)"
            elif final_lev >= 1.0:
                action = "🚀 FULL THROTTLE"
            else:
                action = "✅ STEADY BUY"

            allocation = CAPITAL_PHP * 0.25 * final_lev # 25% max risk per coin
            
            live_results.append({
                "COIN": ticker.replace("-USD", ""),
                "PRICE ($)": f"${current_price:,.2f}",
                "MA200 ($)": f"${ma200_val:,.2f}",
                "DIST %": f"{dist_pct:.2f}%",    # ADDED
                "RSI": round(rsi_val, 2),        # ADDED
                "Z-SCORE": round(float(z_score.iloc[-1]), 2),
                "LEV (1.5x)": round(final_lev, 2),
                "ACTION 📢": action,
                "ALLOCATION (₱)": f"₱{allocation:,.2f}"
            })
            
        except Exception as e:
            pass

    if live_results:
        df_live = pd.DataFrame(live_results)
        
        # --- STYLING LOGIC FOR COLORS ---
        def style_dataframe(row):
            styles = [''] * len(row)
            
            # Action Colors (Column 7 usually, adjust based on order)
            # COIN=0, PRICE=1, MA200=2, DIST=3, RSI=4, Z=5, LEV=6, ACTION=7, ALLOC=8
            
            if "🚀" in str(row["ACTION 📢"]) or "✅" in str(row["ACTION 📢"]):
                styles[7] = 'color: #00ffcc; font-weight: bold;' 
            elif "⛔" in str(row["ACTION 📢"]):
                styles[7] = 'color: #ff4d4d; font-weight: bold;'
            
            # Dist % Colors (Column 3)
            try:
                dist_val = float(row["DIST %"].replace('%',''))
                if dist_val < 0:
                    styles[3] = 'color: #ff4d4d;' # Red underwater
                else:
                    styles[3] = 'color: #00ffcc;' # Green above
            except: pass
            
            # RSI Colors (Column 4)
            try:
                rsi_val = float(row["RSI"])
                if rsi_val < 30:
                    styles[4] = 'color: #00ffcc; font-weight: bold;' # Cheap
                elif rsi_val > 70:
                    styles[4] = 'color: #ff4d4d; font-weight: bold;' # Expensive
            except: pass
                
            return styles
            
        st.dataframe(df_live.style.apply(style_dataframe, axis=1), use_container_width=True)
    else:
        st.error("Market data unavailable.")
# ==========================================
# 2. THE 3-YEAR BACKTEST ENGINE
# ==========================================
st.markdown("---")
st.subheader("📊 Z-SCORE SHOCK-ABSORBER: BATTLE-TESTED SIMULATION")

with st.expander("Tignan ang Real-World Backtest Graphs & Performance Report", expanded=False):
    st.write("🤖 *Crushing concrete cylinders in the cyber-lab with actual friction...*")
    
    START_DATE = "2021-01-01"
    INITIAL_CAP_BT = 50000.0
    FEE_RATE = 0.0050 # PDAX Trading Fee & Spread Estimate (0.5%)

    plt.style.use('dark_background')
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle("Patched Z-Score Engine vs. Buy & Hold (3 Years)", fontsize=16, fontweight='bold', color='white')
    axes = axes.flatten()

    # --- PATCH 1: CANVAS PARA SA UNDERWATER DRAWDOWN ---
    fig_dd, axes_dd = plt.subplots(2, 2, figsize=(16, 6))
    fig_dd.suptitle("🌊 UNDERWATER DRAWDOWN (Ang Sukat ng Baha)", fontsize=16, fontweight='bold', color='#ff4d4d')
    axes_dd = axes_dd.flatten()

    bt_results = []
    
    with st.spinner("Simulating trades from 2021 to Present with Fees..."):
        for idx, ticker in enumerate(WATCHLIST):
            df = yf.download(ticker, start=START_DATE, progress=False, auto_adjust=True)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            close = df["Close"]
            
            ma_200 = close.rolling(200).mean()
            ma_50 = close.rolling(50).mean()
            
            trend_diff = np.log(close / ma_50)
            z_score = (trend_diff - trend_diff.rolling(120).mean()) / (trend_diff.rolling(120).std() + 1e-9)
            
            ret = close.pct_change().fillna(0.0)
            downside_ret = ret.copy()
            downside_ret[downside_ret > 0] = 0.0
            
            downside_vol = downside_ret.rolling(20).std() * np.sqrt(365)
            downside_vol = downside_vol.clip(lower=0.15) # Realism Patch
            
            target_vol = 0.75
            vol_scalar = (target_vol / (downside_vol + 1e-9)).clip(0, 3.0)
            
            # WARLORD ORIGINAL LOGIC
            risk_scaler = (z_score / 2.0).clip(0, 1.0)
            
            # PATCH: Speed Limiter and Shock Absorber
            lev_target_raw = (vol_scalar * risk_scaler).clip(0, 1.5)
            lev_target = lev_target_raw.ewm(span=5).mean()
            lev_target = lev_target.where(close >= ma_200, 0.0)
            
            df['Position'] = lev_target.shift(1).fillna(0.0)
            
            # PATCH: Dito sisingil ng toll fee ang Binance!
            df['Turnover'] = df['Position'].diff().abs().fillna(0.0)
            df['Fees'] = df['Turnover'] * FEE_RATE
            
            df['Strat_Ret'] = (df['Position'] * ret) - df['Fees']
            
            df_clean = df.dropna().copy()
            if len(df_clean) == 0: continue
                
            df_clean['Cum_Strat'] = (1 + df_clean['Strat_Ret']).cumprod()
            df_clean['Cum_Hold'] = (1 + ret).cumprod()
            
            algo_roi = (df_clean['Cum_Strat'].iloc[-1] - 1) * 100
            hold_roi = (df_clean['Cum_Hold'].iloc[-1] - 1) * 100
            strat_vol = df_clean['Strat_Ret'].std() * np.sqrt(365)
            sharpe = (df_clean['Strat_Ret'].mean() * 365) / (strat_vol + 1e-9)
            roll_max = df_clean['Cum_Strat'].cummax()
            max_dd = ((df_clean['Cum_Strat'] / roll_max) - 1).min() * 100
            
# --- THE GOD-TIER KPIs PATCH ---
            # 1. Market Exposure (% Time in Market)
            days_in_market = len(df_clean[df_clean['Position'] > 0])
            total_days = len(df_clean)
            exposure_pct = (days_in_market / total_days) * 100 if total_days > 0 else 0
            
            # 2. Trade Block Analysis (Kino-convert ang buhos ng Algo into individual "Trades")
            df_clean['Trade_Start'] = ((df_clean['Position'] > 0) & (df_clean['Position'].shift(1) == 0)).astype(int)
            df_clean['Trade_ID'] = df_clean['Trade_Start'].cumsum()
            
            in_market_df = df_clean[df_clean['Position'] > 0]
            if not in_market_df.empty:
                trade_returns = in_market_df.groupby('Trade_ID')['Strat_Ret'].apply(lambda x: (1+x).prod() - 1)
                winning_trades = trade_returns[trade_returns > 0]
                losing_trades = trade_returns[trade_returns <= 0]
                
                total_trades = len(trade_returns)
                win_rate = (len(winning_trades) / total_trades) * 100 if total_trades > 0 else 0
                avg_win = winning_trades.mean() * 100 if not winning_trades.empty else 0
                avg_loss = losing_trades.mean() * 100 if not losing_trades.empty else 0
                
                gross_profit = winning_trades.sum()
                gross_loss = abs(losing_trades.sum())
                profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else np.nan
                
                # --- PATCH 2A: MAX LOSING STREAK LOGIC ---
                is_loss = (trade_returns <= 0).astype(int)
                streak = is_loss.groupby((is_loss != is_loss.shift()).cumsum()).cumsum()
                max_losing_streak = streak.max() if not streak.empty else 0
            else:
                total_trades = win_rate = avg_win = avg_loss = profit_factor = max_losing_streak = 0
                
            # 3. Calmar Ratio (Annualized Return / Max Drawdown)
            years_in_market = total_days / 365.25
            ann_ret = (df_clean['Cum_Strat'].iloc[-1]) ** (1 / years_in_market) - 1 if years_in_market > 0 else 0
            calmar = ann_ret / (abs(max_dd) / 100) if max_dd != 0 else np.nan

            # 4. Ang Bagong Dashboard Output (WITH SHARPE RATIO ⚡)
            bt_results.append({
                "Asset": ticker.replace("-USD", ""),
                "Algo ROI": f"{algo_roi:.1f}%",
                "HODL ROI": f"{hold_roi:.1f}%",
                "Max DD": f"{max_dd:.1f}%",
                "Sharpe": f"{sharpe:.2f}", # --- BINALIK NATIN ANG SHARPE RATIO PRE! ---
                "Calmar": f"{calmar:.2f}",
                "Win Rate": f"{win_rate:.1f}%",
                "Profit Fctr": f"{profit_factor:.2f}",
                "Avg Win": f"+{avg_win:.1f}%",
                "Avg Loss": f"{avg_loss:.1f}%",
                "Max Lose Streak": int(max_losing_streak),
                "Total Trades": total_trades,
                "Exposure": f"{exposure_pct:.1f}%"
            })
            
            ax = axes[idx]
            ax.plot(df_clean.index, df_clean['Cum_Strat'], label='Patched Z-Score Algo', color='#ffcc00', linewidth=2)
            ax.plot(df_clean.index, df_clean['Cum_Hold'], label='Buy & Hold', color='#777777', linewidth=1.5, alpha=0.8)
            ax.fill_between(df_clean.index, df_clean['Cum_Strat'].min(), df_clean['Cum_Strat'].max(), 
                            where=df_clean['Position'] > 0, color='#ffcc00', alpha=0.1)
            ax.set_title(f"{ticker.replace('-USD', '')}", fontsize=12, fontweight='bold', color='white')
            ax.legend(loc='upper left', frameon=False, labelcolor='white')
            ax.grid(True, color='#333333', linestyle='--', alpha=0.5)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.set_ylabel("Equity Multiplier")
            
            # --- PATCH 3A: DRAWDOWN PLOTTING ---
            drawdown_series = ((df_clean['Cum_Strat'] / roll_max) - 1) * 100
            ax_dd = axes_dd[idx]
            ax_dd.fill_between(df_clean.index, drawdown_series, 0, color='#ff4d4d', alpha=0.3)
            ax_dd.plot(df_clean.index, drawdown_series, color='#ff4d4d', linewidth=1.2)
            ax_dd.set_title(f"{ticker.replace('-USD', '')} Drawdown %", fontsize=11, color='white')
            ax_dd.grid(True, color='#333333', linestyle='--', alpha=0.5)
            ax_dd.spines['top'].set_visible(False)
            ax_dd.spines['right'].set_visible(False)
            ax_dd.set_ylabel("Drawdown (%)")

    # --- PATCH 3B: DISPLAY BOTH GRAPHS ---
    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    fig_dd.tight_layout()
    fig_dd.subplots_adjust(top=0.90)
    
    st.pyplot(fig)
    st.markdown("<br>", unsafe_allow_html=True)
    st.pyplot(fig_dd)
    
    st.markdown("### 🏆 THE REAL-WORLD REPORT CARD")
    if bt_results:
        st.dataframe(pd.DataFrame(bt_results), use_container_width=True)

st.markdown("---")
st.subheader("🍺 BENDER'S FINAL WORD: Ang algo na 'to ay parang titanium helmet na. Makatotohanan ang kikitain mo at protektado ka sa bear market. Dismissed.")
