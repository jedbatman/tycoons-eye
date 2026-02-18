import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings

warnings.filterwarnings('ignore')

# ==========================================
# PAGE SETTINGS & HEADER
# ==========================================
st.set_page_config(page_title="Fluid Dynamics (HPFO)", layout="wide")

st.title("🚰 MODULE 7: FLUID DYNAMICS ENGINE (HPFO)")
st.markdown("**Powered by Tycoon Jed Racho x DeepThink AI** | Hydrodynamic Price-Flow Oscillator")
st.info("💡 **LOGIC:** Tinatrato ng makinang ito ang crypto market bilang isang dambuhalang tubo ng tubig. Ang Pera ay Liquidity. Kung malakas ang pressure (Volume) at mabilis ang agos (Velocity), bubuksan niya ang balbula para saluhin ang baha. Ligtas sa 0.5% PDAX friction!")

# --- BENDER'S CHEAT SHEET ---
with st.expander("📖 BENDER'S CHEAT SHEET (Paano Basahin ang Hydraulics)", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("### 1. HPFO Z (Pressure)")
        st.caption("Lakas ng Bwelo")
        st.write("🌊 **> +1.8:** Dambuhalang Baha (Strong Buy).")
        st.write("💧 **< -0.2:** Tuyo na ang tubo (Sell).")
    with col2:
        st.markdown("### 2. REYNOLDS (Flow)")
        st.caption("Malinis ba ang agos?")
        st.write("🟢 **> 1.0:** Laminar (Dire-diretso).")
        st.write("🔴 **< 0.8:** Turbulent (Magulo/Chop).")
    with col3:
        st.markdown("### 3. VELOCITY (Speed)")
        st.caption("Bilis ng Pera")
        st.write("🚀 **> 0.02:** Kayang bayaran ang PDAX Fee.")
        st.write("🐢 **< 0.02:** Mahina, kakainin lang ng fee.")
    with col4:
        st.markdown("### 4. THE VALVE (Action)")
        st.caption("Warlord Command")
        st.write("🚰 **OPEN VALVE:** Saluhin ang baha!")
        st.write("🔒 **CLOSE VALVE:** Patay ang makina, ligtas.")

st.markdown("---")

# --- CONFIGURATION ---
WATCHLIST = ["BTC-USD", "SOL-USD", "XLM-USD", "XRP-USD", "ADA-USD", "DOGE-USD"]
CAPITAL_PHP = st.sidebar.number_input("War Chest (PHP)", value=50000.0, step=5000.0)
FEE_RATE = 0.005 # 0.5% PDAX Fee

st.write(f"⏳ **Live Scan Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# THE ALIEN PHYSICS ENGINE (HPFO)
# ==========================================
def engineer_hydrodynamics(df):
    close = df['Close']
    volume = df['Volume'].replace(0, np.nan).ffill().fillna(1)
    
    log_close = np.log(close)
    velocity = log_close.diff(10)
    
    rho = volume / volume.rolling(50).mean()
    rho = rho.fillna(1.0)
    
    dynamic_pressure = 0.5 * rho * velocity * velocity.abs()
    
    daily_ret = log_close.diff(1)
    viscosity = daily_ret.rolling(20).std() * np.sqrt(10)
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
# 1. LIVE SIGNAL DASHBOARD
# ==========================================
st.subheader("🎯 LIVE HYDRAULIC SIGNALS (Valve Status)")

with st.spinner('🤖 Bender is checking pipe pressure and fluid velocity...'):
    live_results = []
    
    for ticker in WATCHLIST:
        try:
            df = yf.download(ticker, period="4y", interval="1d", progress=False, auto_adjust=True)
            if len(df) < 200: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            df = engineer_hydrodynamics(df)
            
            # --- BENDER'S SANITY CHECK PATCH (MA200 & RSI) ---
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
            # -------------------------------------------------

            vel = float(df['Velocity'].iloc[-1])
            rey = float(df['Reynolds'].iloc[-1])
            hpfo = float(df['HPFO_Z'].iloc[-1])
            
            friction_barrier = FEE_RATE * 4.0 # 0.02
            
            # THE HYDRAULIC VALVE LOGIC
            if hpfo > 1.8 and rey > 1.0 and vel > friction_barrier:
                action = "🚰 OPEN VALVE (BUY)"
                allocation = f"₱{(CAPITAL_PHP * 0.25):,.2f} (25%)"
                comment = "Dambuhalang Baha! Saluhin ang pera!"
            elif hpfo < -0.2 or rey < 0.8:
                action = "🔒 CLOSE VALVE (EXIT)"
                allocation = "₱0.00"
                comment = "Magulo ang agos. Ligtas sa bunker."
            else:
                action = "⏳ MAINTAIN PRESSURE"
                allocation = "Hold"
                comment = "Nag-iipon ng bwelo ang tubig."
                
            live_results.append({
                "COIN": ticker.replace("-USD", ""),
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
        except Exception as e:
            pass

    if live_results:
        df_live = pd.DataFrame(live_results)
        
        def color_coding(val):
            if isinstance(val, str):
                if "🚰" in val: return 'color: #00ffcc; font-weight: bold;'
                if "🔒" in val: return 'color: #ff4d4d; font-weight: bold;'
                if "⏳" in val: return 'color: #ffcc00;'
            return ''
            
        st.dataframe(df_live.style.map(color_coding), use_container_width=True)
    else:
        st.error("Wala tayong tubig ngayon (No Market Data).")

# ==========================================
# 2. THE FLUID DYNAMICS BACKTEST BATTLE ROYALE
# ==========================================
st.markdown("---")
st.subheader("📊 4-YEAR BACKTEST: HPFO vs HODL (0.5% Fee Imposed)")

with st.expander("Tignan ang 4-Year Lab Report & Drawdown Graphs", expanded=False):
    st.write("🤖 *Pumping 4 years of historical fluid data through the Warlord Engine...*")
    
    plt.style.use('dark_background')
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle("Hydrodynamic Engine (HPFO) vs Buy & Hold", fontsize=16, fontweight='bold', color='white')
    axes = axes.flatten()

    fig_dd, axes_dd = plt.subplots(2, 2, figsize=(16, 6))
    fig_dd.suptitle("🌊 UNDERWATER DRAWDOWN (Ang Sukat ng Baha)", fontsize=16, fontweight='bold', color='#ff4d4d')
    axes_dd = axes_dd.flatten()
    
    bt_results = []
    # Dambuhalang Listahan (Top 4 ang map-plot sa graph, lahat papasok sa table)
    backtest_tickers = [
        "XLM-USD", "SOL-USD", "XRP-USD", "BTC-USD", "ADA-USD",
        "ETH-USD", "AVAX-USD", "LINK-USD", "DOGE-USD", "UNI-USD",
        "DOT-USD", "LTC-USD", "BCH-USD", "NEAR-USD", "TRX-USD"
    ]

    with st.spinner("Executing Darcy-Weisbach Friction Simulator para sa 15 coins..."):
        for idx, ticker in enumerate(backtest_tickers):
            df = yf.download(ticker, period="4y", interval="1d", progress=False, auto_adjust=True)
            if df.empty or len(df) < 500: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            df = engineer_hydrodynamics(df)
            friction_barrier = FEE_RATE * 4.0
            
            # --- SIGNAL GEN ---
            buy_cond = (df['HPFO_Z'] > 1.8) & (df['Reynolds'] > 1.0) & (df['Velocity'] > friction_barrier)
            sell_cond = (df['HPFO_Z'] < -0.2) | (df['Reynolds'] < 0.8)
            
            df['Raw_Signal'] = np.where(buy_cond, 1, np.where(sell_cond, 0, np.nan))
            df['Raw_Signal'] = df['Raw_Signal'].ffill().fillna(0)
            
            # 🚨 ZERO LOOK-AHEAD BIAS 🚨
            df['Target_Pos'] = df['Raw_Signal'].shift(1).fillna(0)
            
            # --- SIMULATION ---
            closes = df['Close'].values
            target_pos = df['Target_Pos'].values
            n = len(df)
            
            equity = np.ones(n)
            in_pos = False
            entry_equity = 1.0
            trades = []
            market_exposure = np.zeros(n)
            
            for i in range(1, n):
                if in_pos:
                    equity[i] = equity[i-1] * (closes[i] / closes[i-1])
                    market_exposure[i] = 1.0
                else:
                    equity[i] = equity[i-1]
                    
                current_target = target_pos[i]
                if not in_pos and current_target == 1:
                    equity[i] *= (1 - FEE_RATE)
                    entry_equity = equity[i]
                    in_pos = True
                    market_exposure[i] = 1.0
                elif in_pos and current_target == 0:
                    equity[i] *= (1 - FEE_RATE)
                    in_pos = False
                    market_exposure[i] = 0.0
                    trades.append((equity[i] / entry_equity) - 1.0)
                    
            if in_pos:
                equity[-1] *= (1 - FEE_RATE)
                trades.append((equity[-1] / entry_equity) - 1.0)
                
            df['Equity'] = equity
            
            # --- KPIs ---
            algo_roi = (equity[-1] - 1.0) * 100
            hodl_roi = (closes[-1] / closes[0] - 1.0) * 100
            
            cum_max = np.maximum.accumulate(equity)
            drawdown = (equity / cum_max) - 1.0
            max_dd = np.min(drawdown) * 100
            
            strat_returns = pd.Series(equity).pct_change().dropna()
            sharpe = (strat_returns.mean() / strat_returns.std()) * np.sqrt(365) if strat_returns.std() > 0 else 0.0
            
            trades = np.array(trades)
            total_trades = len(trades)
            win_rate = (len(trades[trades > 0]) / total_trades) * 100 if total_trades > 0 else 0
            
            gross_profit = np.sum(trades[trades > 0])
            gross_loss = np.abs(np.sum(trades[trades <= 0]))
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else (99.9 if gross_profit > 0 else 0.0)
            
            avg_win = np.mean(trades[trades > 0]) * 100 if len(trades[trades > 0]) > 0 else 0
            avg_loss = np.mean(trades[trades <= 0]) * 100 if len(trades[trades <= 0]) > 0 else 0
            exposure = (np.sum(market_exposure) / n) * 100
            
            bt_results.append({
                "Asset": ticker.replace("-USD", ""),
                "Raw_ROI": algo_roi,  # <-- SIKRETONG COLUMN PARA SA SORTING
                "Algo ROI": f"{algo_roi:.1f}%",
                "HODL ROI": f"{hodl_roi:.1f}%",
                "Max DD": f"{max_dd:.1f}%",
                "Sharpe": f"{sharpe:.2f}",
                "Win Rate": f"{win_rate:.1f}%",
                "Profit Fctr": f"{profit_factor:.2f}",
                "Avg Win": f"+{avg_win:.1f}%",
                "Avg Loss": f"{avg_loss:.1f}%",
                "Trades": total_trades,
                "Exposure": f"{exposure:.1f}%"
            })

            # --- GRAPH PROTECTOR: Top 4 lang ang i-d-drawing ---
            if idx >= 4:
                continue
            # ----------------------------------------------------

            # PLOT 1: EQUITY
            ax = axes[idx]
            ax.plot(df.index, df['Equity'], label='HPFO Engine', color='#00aaff', linewidth=2)
            ax.plot(df.index, closes/closes[0], label='Buy & Hold', color='#777777', linewidth=1.5, alpha=0.8)
            ax.fill_between(df.index, df['Equity'].min(), df['Equity'].max(), where=df['Target_Pos']==1, color='#00aaff', alpha=0.1)
            ax.set_title(f"{ticker.replace('-USD', '')}", fontsize=12, fontweight='bold', color='white')
            ax.legend(loc='upper left', frameon=False, labelcolor='white')
            ax.grid(True, color='#333333', linestyle='--', alpha=0.5)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            # PLOT 2: DRAWDOWN
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
    
    st.markdown("### 🏆 THE FLUID DYNAMICS LAB REPORT (RANKED COMPATIBILITY)")
    if bt_results:
        df_report = pd.DataFrame(bt_results)
        # I-sort mula pinakamataas na kita pababa, tapos itago ang sikretong column
        df_report = df_report.sort_values(by="Raw_ROI", ascending=False).drop(columns=["Raw_ROI"]).reset_index(drop=True)
        st.dataframe(df_report, use_container_width=True)

st.markdown("---")
st.subheader("🍺 BENDER'S FINAL WORD: Para tayong nag-install ng water pump sa bank vault. Bantayan mo lang ang pressure, sasabog nang kusa ang pera. Dismissed.")
