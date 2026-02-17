import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')

# --- PAGE SETTINGS ---
st.set_page_config(page_title="Solana Rocket Engine", layout="wide")

st.title("🚀 MODULE 5: THE SOLANA ROCKET (OVERDRIVE)")
st.markdown("**Powered by Tycoon Jed Racho & Bender AI** | Dedicated High-Speed Trend Rider")
st.info("💡 **LOGIC:** Ang makinang ito ay ginawa PARA SA SOLANA LANG. Walang mabagal na preno (Max 2.5x Lev), mabilis ang manibela (2-day smoothing), at handang sumakay sa dambuhalang volatility.")
st.markdown("---")

# --- CONFIGURATION ---
TICKER = "SOL-USD"
CAPITAL_PHP = st.sidebar.number_input("Rocket Fuel (PHP)", value=50000.0, step=5000.0)

st.write(f"⏳ **Live Scan Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# 1. LIVE SIGNAL DASHBOARD (SOLANA ONLY)
# ==========================================
st.subheader("🎯 LIVE OVERDRIVE RADAR")

with st.spinner('🤖 Bender is igniting the Solana thrusters...'):
    try:
        df = yf.download(TICKER, period="1y", interval="1d", progress=False, auto_adjust=True)
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
        
        # OVERDRIVE TWEAK 1: Lower Floor
        downside_vol = downside_ret.rolling(20).std() * np.sqrt(365)
        downside_vol = downside_vol.clip(lower=0.10) 
        
        target_vol = 0.75
        vol_scalar = (target_vol / (downside_vol + 1e-9)).clip(0, 3.0)
        risk_scaler = (z_score / 2.0).clip(0, 1.0)
        
        # OVERDRIVE TWEAK 2: 2.5x Leverage + Faster Steering (span=2)
        lev_target_raw = (vol_scalar * risk_scaler).clip(0, 2.5)
        lev_target = lev_target_raw.ewm(span=2).mean()
        
        # Concrete Floor Guard
        if current_price < float(ma_200.iloc[-1]):
            final_lev = 0.0
        else:
            final_lev = float(lev_target.iloc[-1])
        
        # Action Logic
        if final_lev == 0.0:
            action = "⛔ ENGINE OFF (Cash / Exit)"
        elif final_lev < 1.0:
            action = "⚠️ PRE-IGNITION (Weak Buy)"
        elif final_lev >= 2.0:
            action = "🚀 WARP SPEED (Max Buy)"
        else:
            action = "✅ THROTTLE UP (Steady Buy)"

        allocation = CAPITAL_PHP * final_lev # 100% of inputted capital allocated for this rocket
        
        live_results = [{
            "COIN": "SOLANA",
            "PRICE ($)": f"${current_price:,.2f}",
            "MA200 ($)": f"${float(ma_200.iloc[-1]):,.2f}",
            "Z-SCORE": round(float(z_score.iloc[-1]), 2),
            "LEVERAGE (MAX 2.5x)": round(final_lev, 2),
            "ACTION 📢": action,
            "SUGGESTED ALLOCATION (₱)": f"₱{allocation:,.2f}"
        }]
        
        df_live = pd.DataFrame(live_results)
        
        def color_zscore(val):
            if isinstance(val, str):
                if "🚀" in val or "✅" in val: return 'color: #00ffcc'
                if "⛔" in val: return 'color: #ff4d4d'
                if "⚠️" in val: return 'color: #ffcc00'
            return ''
            
        st.dataframe(df_live.style.map(color_zscore), use_container_width=True)
        
    except Exception as e:
        st.error(f"Market data unavailable. Error: {e}")

# ==========================================
# 2. THE 3-YEAR BACKTEST ENGINE (SOLANA DEDICATED)
# ==========================================
st.markdown("---")
st.subheader("📊 OVERDRIVE TELEMETRY: 3-YEAR BACKTEST")

with st.expander("Tignan ang Backtest Graph & Performance Report (with Binance Fees)", expanded=False):
    st.write("🤖 *Calculating G-Force and Friction...*")
    
    START_DATE = "2021-01-01"
    FEE_RATE = 0.0050 # PDAX Trading Fee (0.5%)

    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(14, 7))
    
    with st.spinner("Simulating Solana trades from 2021 to Present..."):
        df_bt = yf.download(TICKER, start=START_DATE, progress=False, auto_adjust=True)
        if isinstance(df_bt.columns, pd.MultiIndex): df_bt.columns = df_bt.columns.get_level_values(0)
        
        close_bt = df_bt["Close"]
        
        ma_200_bt = close_bt.rolling(200).mean()
        ma_50_bt = close_bt.rolling(50).mean()
        
        trend_diff_bt = np.log(close_bt / ma_50_bt)
        z_score_bt = (trend_diff_bt - trend_diff_bt.rolling(120).mean()) / (trend_diff_bt.rolling(120).std() + 1e-9)
        
        ret_bt = close_bt.pct_change().fillna(0.0)
        downside_ret_bt = ret_bt.copy()
        downside_ret_bt[downside_ret_bt > 0] = 0.0
        
        downside_vol_bt = downside_ret_bt.rolling(20).std() * np.sqrt(365)
        downside_vol_bt = downside_vol_bt.clip(lower=0.10) 
        
        target_vol_bt = 0.75
        vol_scalar_bt = (target_vol_bt / (downside_vol_bt + 1e-9)).clip(0, 3.0)
        risk_scaler_bt = (z_score_bt / 2.0).clip(0, 1.0)
        
        lev_target_raw_bt = (vol_scalar_bt * risk_scaler_bt).clip(0, 2.5)
        lev_target_bt = lev_target_raw_bt.ewm(span=2).mean()
        lev_target_bt = lev_target_bt.where(close_bt >= ma_200_bt, 0.0)
        
        df_bt['Position'] = lev_target_bt.shift(1).fillna(0.0)
        
        # Dito sisingil ng toll fee ang Binance!
        df_bt['Turnover'] = df_bt['Position'].diff().abs().fillna(0.0)
        df_bt['Fees'] = df_bt['Turnover'] * FEE_RATE
        
        df_bt['Strat_Ret'] = (df_bt['Position'] * ret_bt) - df_bt['Fees']
        
        df_clean = df_bt.dropna().copy()
            
        df_clean['Cum_Strat'] = (1 + df_clean['Strat_Ret']).cumprod()
        df_clean['Cum_Hold'] = (1 + ret_bt).cumprod()
        
        algo_roi = (df_clean['Cum_Strat'].iloc[-1] - 1) * 100
        hold_roi = (df_clean['Cum_Hold'].iloc[-1] - 1) * 100
        strat_vol = df_clean['Strat_Ret'].std() * np.sqrt(365)
        sharpe = (df_clean['Strat_Ret'].mean() * 365) / (strat_vol + 1e-9)
        roll_max = df_clean['Cum_Strat'].cummax()
        max_dd = ((df_clean['Cum_Strat'] / roll_max) - 1).min() * 100
        
        bt_results = [{
            "Asset": "SOLANA (OVERDRIVE)",
            "Algo ROI (%)": f"{algo_roi:.1f}%",
            "HODL ROI (%)": f"{hold_roi:.1f}%",
            "Sharpe Ratio": f"{sharpe:.2f}",
            "Max Drawdown (%)": f"{max_dd:.1f}%"
        }]
        
        ax.plot(df_clean.index, df_clean['Cum_Strat'], label='Solana Rocket Algo', color='#00ffcc', linewidth=2)
        ax.plot(df_clean.index, df_clean['Cum_Hold'], label='Buy & Hold', color='#777777', linewidth=1.5, alpha=0.8)
        ax.fill_between(df_clean.index, df_clean['Cum_Strat'].min(), df_clean['Cum_Strat'].max(), 
                        where=df_clean['Position'] > 0, color='#00ffcc', alpha=0.1)
        ax.set_title("🚀 SOLANA ROCKET vs Buy & Hold", fontsize=16, fontweight='bold', color='white')
        ax.legend(loc='upper left', frameon=False, labelcolor='white')
        ax.grid(True, color='#333333', linestyle='--', alpha=0.5)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.set_ylabel("Equity Multiplier")

    st.pyplot(fig)
    
    st.markdown("### 🏆 THE OVERDRIVE REPORT CARD")
    st.dataframe(pd.DataFrame(bt_results), use_container_width=True)

st.markdown("---")
st.subheader("🍺 BENDER'S WARNING: Ang module na 'to ay walang seatbelt. Pag sumabog 'to, ramdam mo ang sakit. Play at your own risk, Warlord.")
