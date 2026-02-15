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

st.title("🛡️ MODULE 4: THE Z-SCORE BUNKER (REALITY PATCH)")
st.markdown("**Powered by Tycoon Jed Racho & Bender AI** | The Shock-Absorber Protocol")
st.info("💡 **LOGIC:** Ang makinang ito ay isang Warlord Momentum Engine. Nakakabit sa MA200 Bunker. Ngayon, may kasama nang 0.1% Trading Fees at Max Leverage Cap (1.5x) para sa totoong Warlord simulation.")
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
            ma_200 = close.rolling(200).mean()
            ma_50 = close.rolling(50).mean()
            
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
                "MA200 ($)": f"${float(ma_200.iloc[-1]):,.2f}",
                "Z-SCORE": round(float(z_score.iloc[-1]), 2),
                "LEVERAGE (MAX 1.5x)": round(final_lev, 2),
                "ACTION 📢": action,
                "SUGGESTED ALLOCATION (₱)": f"₱{allocation:,.2f}"
            })
            
        except Exception as e:
            pass

    if live_results:
        df_live = pd.DataFrame(live_results)
        
        def color_zscore(val):
            if isinstance(val, str):
                if "🚀" in val or "✅" in val: return 'color: #00ffcc'
                if "⛔" in val: return 'color: #ff4d4d'
                if "⚠️" in val: return 'color: #ffcc00'
            return ''
            
        st.dataframe(df_live.style.map(color_zscore), use_container_width=True)
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
    FEE_RATE = 0.0010 # Binance Trading Fee (0.1%)

    plt.style.use('dark_background')
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle("Patched Z-Score Engine vs. Buy & Hold (3 Years)", fontsize=16, fontweight='bold', color='white')
    axes = axes.flatten()

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
            
            bt_results.append({
                "Asset": ticker.replace("-USD", ""),
                "Algo ROI (%)": f"{algo_roi:.1f}%",
                "HODL ROI (%)": f"{hold_roi:.1f}%",
                "Sharpe Ratio": f"{sharpe:.2f}",
                "Max Drawdown (%)": f"{max_dd:.1f}%"
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

    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    
    st.pyplot(fig)
    
    st.markdown("### 🏆 THE REAL-WORLD REPORT CARD")
    if bt_results:
        st.dataframe(pd.DataFrame(bt_results), use_container_width=True)

st.markdown("---")
st.subheader("🍺 BENDER'S FINAL WORD: Ang algo na 'to ay parang titanium helmet na. Makatotohanan ang kikitain mo at protektado ka sa bear market. Dismissed.")
