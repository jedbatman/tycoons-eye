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
st.set_page_config(page_title="Altcoin Assassin (AKSSE)", layout="wide")

st.title("🥷 MODULE 6: THE ALTCOIN ASSASSIN (AKSSE PROTOCOL)")
st.markdown("**Powered by Tycoon Jed Racho x DeepThink AI** | Institutional Kalman Filter Sniper")
st.info("💡 **LOGIC:** Ang makinang ito ay HINDI pang-araw-araw na trade. Ito ay isang 'Macro Sniper' na gumagamit ng NASA-grade math (Kalman Filters). Nakadisenyo para sa ADA, SOL, at mga baliw na altcoins. Kaya nitong bayaran ang 0.5% PDAX Fee dahil bultuhan kung kumita!")

# --- BENDER'S CHEAT SHEET ---
with st.expander("📖 BENDER'S CHEAT SHEET (Paano Basahin ang Alien Math na 'To)", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("### 1. MACRO SLOPE")
        st.caption("Ang Totoong Direksyon")
        st.write("🟢 **Positive:** Bull Market.")
        st.write("🔴 **Negative:** Bear Market / Bagsak.")
    with col2:
        st.markdown("### 2. VELOCITY Z")
        st.caption("Ang Bilis ng Bwelo")
        st.write("🚀 **> +1.25:** Sniper BUY Trigger!")
        st.write("💤 **< -0.25:** Ubos na ang gas. SELL.")
    with col3:
        st.markdown("### 3. PRICE Z")
        st.caption("Blow-Off Top Filter")
        st.write("🔥 **> 2.0:** Masyadong Hype. Wag bibili!")
        st.write("🧊 **Normal:** Safe pumasok.")
    with col4:
        st.markdown("### 4. THE ACTION")
        st.caption("Warlord Command")
        st.write("🔫 **SNIPER BUY:** Pumasok ka na.")
        st.write("🛡️ **CASH/HOLD:** Tulog ang pera, ligtas sa baha.")

st.markdown("---")

# --- CONFIGURATION ---
WATCHLIST = ["ADA-USD", "SOL-USD", "AVAX-USD", "UNI-USD", "XRP-USD", "BTC-USD"]
CAPITAL_PHP = st.sidebar.number_input("War Chest (PHP)", value=50000.0, step=5000.0)
FEE_RATE = 0.005 # 0.5% PDAX Fee

st.write(f"⏳ **Live Scan Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# THE ALIEN MATH ENGINE (DEEPTHINK'S AKSSE)
# ==========================================
def kinematic_kalman_filter(prices, q=1e-4, r=0.01):
    n = len(prices)
    x = np.zeros((2, n))
    x[0, 0] = prices[0]
    x[1, 0] = 0.0              
    
    P = np.eye(2)
    F = np.array([[1.0, 1.0], [0.0, 1.0]]) 
    H = np.array([[1.0, 0.0]])
    Q = np.array([[q, 0.0], [0.0, q]])
    R = np.array([[r]])
    
    for i in range(1, n):
        x_pred = F @ x[:, i-1]
        P_pred = F @ P @ F.T + Q
        y = prices[i] - (H @ x_pred)[0]
        S = H @ P_pred @ H.T + R
        K = P_pred @ H.T @ np.linalg.inv(S)
        x[:, i] = x_pred + (K @ np.array([y])).flatten()
        P = (np.eye(2) - K @ H) @ P_pred
        
    return x[0, :], x[1, :]

def build_features(df):
    close = df['Close'].values.flatten()
    log_close = np.log(close)
    
    kf_price_log, kf_vel_log = kinematic_kalman_filter(log_close, q=1e-4, r=0.01)
    
    log_rets = np.diff(log_close, prepend=log_close[0])
    vol = pd.Series(log_rets).rolling(window=20).std().bfill().values
    vol[vol == 0] = 1e-6 
    
    norm_vel = kf_vel_log / vol
    norm_vel_s = pd.Series(norm_vel)
    
    roll_mean_v = norm_vel_s.rolling(50).mean().bfill().values
    roll_std_v = norm_vel_s.rolling(50).std().bfill().values
    roll_std_v[roll_std_v == 0] = 1e-6
    vel_z = (norm_vel - roll_mean_v) / roll_std_v
    
    macro_slope = pd.Series(kf_price_log).diff(100).fillna(0).values
    
    log_s = pd.Series(log_close)
    roll_mean_p = log_s.rolling(20).mean().bfill().values
    roll_std_p = log_s.rolling(20).std().bfill().values
    roll_std_p[roll_std_p == 0] = 1e-6
    price_z = (log_close - roll_mean_p) / roll_std_p
    
    df['Vel_Z'] = vel_z
    df['Price_Z'] = price_z
    df['Macro_Slope'] = macro_slope
    return df

# ==========================================
# 1. LIVE SIGNAL DASHBOARD
# ==========================================
st.subheader("🎯 LIVE ASSASSIN SIGNALS (Kalman Filter)")

with st.spinner('🤖 DeepThink Engine is extracting True Velocity...'):
    live_results = []
    
    for ticker in WATCHLIST:
        try:
            df = yf.download(ticker, period="4y", interval="1d", progress=False, auto_adjust=True)
            if len(df) < 200: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            df = build_features(df)
            
            current_price = float(df['Close'].iloc[-1])
            vel_z = float(df['Vel_Z'].iloc[-1])
            price_z = float(df['Price_Z'].iloc[-1])
            macro = float(df['Macro_Slope'].iloc[-1])
            
            # THE SNIPER LOGIC
            if vel_z > 1.25 and macro > 0 and price_z < 2.0:
                action = "🔫 SNIPER BUY"
                allocation = f"₱{(CAPITAL_PHP * 0.25):,.2f} (25%)"
                comment = "Dambuhalang Breakout! Pasok!"
            elif price_z > 3.0:
                action = "🔥 TAKE PROFIT (BLOW-OFF)"
                allocation = "₱0.00 (SELL ALL)"
                comment = "Masyado nang hype. Benta na!"
            elif vel_z < -0.25 or macro < -0.1:
                action = "⛔ CASH / EXIT"
                allocation = "₱0.00"
                comment = "Walang momentum. Ligtas sa bunker."
            else:
                action = "⏳ HOLD / WAIT"
                allocation = "Maintain"
                comment = "Hayaan mo lang yung sniper na mag-abang."
                
            live_results.append({
                "COIN": ticker.replace("-USD", ""),
                "PRICE ($)": f"${current_price:,.2f}",
                "MACRO SLOPE": round(macro, 3),
                "VELOCITY Z": round(vel_z, 2),
                "PRICE Z (Hype)": round(price_z, 2),
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
                if "🔫" in val: return 'color: #00ffcc; font-weight: bold;'
                if "⛔" in val or "🔥" in val: return 'color: #ff4d4d; font-weight: bold;'
                if "⏳" in val: return 'color: #ffcc00;'
            return ''
            
        st.dataframe(df_live.style.map(color_coding), use_container_width=True)
    else:
        st.error("Market data unavailable.")

# ==========================================
# 2. THE DEEPTHINK BACKTEST BATTLE ROYALE
# ==========================================
st.markdown("---")
st.subheader("📊 4-YEAR BACKTEST: AKSSE vs HODL (0.5% Fee Imposed)")

with st.expander("Tignan ang 4-Year Backtest Graphs & Warlord KPIs", expanded=False):
    st.write("🤖 *Running Kalman Filters across 4 years of history...*")
    
    plt.style.use('dark_background')
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle("The Altcoin Assassin (AKSSE) vs Buy & Hold", fontsize=16, fontweight='bold', color='white')
    axes = axes.flatten()

    fig_dd, axes_dd = plt.subplots(2, 2, figsize=(16, 6))
    fig_dd.suptitle("🌊 UNDERWATER DRAWDOWN (Ang Sukat ng Baha)", fontsize=16, fontweight='bold', color='#ff4d4d')
    axes_dd = axes_dd.flatten()
    
    bt_results = []
    plot_tickers = ["ADA-USD", "SOL-USD", "AVAX-USD", "UNI-USD"] # Top performers
    
    with st.spinner("Simulating Warlord Trades..."):
        for idx, ticker in enumerate(plot_tickers):
            df = yf.download(ticker, period="4y", interval="1d", progress=False, auto_adjust=True)
            if df.empty or len(df) < 500: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            df = build_features(df)
            
            # --- SIGNAL GEN ---
            signals = np.zeros(len(df))
            current_pos = 0
            vel_z = df['Vel_Z'].values
            price_z = df['Price_Z'].values
            macro = df['Macro_Slope'].values
            
            for i in range(len(df)):
                if current_pos == 0:
                    if vel_z[i] > 1.25 and macro[i] > 0 and price_z[i] < 2.0:
                        current_pos = 1
                else:
                    if vel_z[i] < -0.25 or price_z[i] > 3.0 or macro[i] < -0.1:
                        current_pos = 0
                signals[i] = current_pos
                
            df['Signal'] = signals
            
            # --- SIMULATION ---
            closes = df['Close'].values
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
                    
                target_pos = signals[i]
                if not in_pos and target_pos == 1:
                    entry_equity = equity[i]        
                    equity[i] *= (1 - FEE_RATE)
                    in_pos = True
                    market_exposure[i] = 1.0
                elif in_pos and target_pos == 0:
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
            
            # PLOT 1: EQUITY
            ax = axes[idx]
            ax.plot(df.index, df['Equity'], label='AKSSE Sniper', color='#00ffcc', linewidth=2)
            ax.plot(df.index, closes/closes[0], label='Buy & Hold', color='#777777', linewidth=1.5, alpha=0.8)
            ax.fill_between(df.index, df['Equity'].min(), df['Equity'].max(), where=signals==1, color='#00ffcc', alpha=0.1)
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
    
    st.markdown("### 🏆 THE ALIEN MATH REPORT CARD")
    if bt_results:
        st.dataframe(pd.DataFrame(bt_results), use_container_width=True)

st.markdown("---")
st.subheader("🍺 BENDER'S FINAL WORD: Ang algo na 'to ay parang sniper rifle. 90% ng oras, nakahiga ka lang at naghihintay. Pag kinalabit mo, siguradong wasak! Dismissed.")
