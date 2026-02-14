import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# --- PAGE SETTINGS ---
st.set_page_config(page_title="Jed's Law V6.0", layout="wide")

st.title("📈 JED'S LAW x KTO HYBRID DASHBOARD V6.0")
st.markdown("**Powered by Tycoon Jed Racho & Bender AI** | Quantitative Crypto Protocol")
st.markdown("---")

# --- CONFIGURATION ---
WATCHLIST = ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "AVAX-USD", "XRP-USD"]
CAPITAL_PHP = st.sidebar.number_input("War Chest (PHP)", value=50000.0, step=5000.0)

st.sidebar.markdown("---")
st.sidebar.subheader("🤖 BENDER'S CHEAT SHEET:")
st.sidebar.info("1. **[MA200]**: Ang Simento/Sahig. Pag nasa ilalim, Cash is King. Pag nasa ibabaw, Party time.")
st.sidebar.info("2. **[RSI]**: <30 ay SALE. >70 ay MAHAL/SCAM.")
st.sidebar.info("3. **[KTO]**: Ang pwersa. Pag positive, may bwelo. Pag negative, hingal na.")
st.sidebar.info("4. **[ACCUMULATE]**: Buy Small. Pa-konti konti lang. Wag kang tanga mag-all in sa bear market.")

# --- MATHEMATICAL ENGINES (HINDI GINALAW ANG LOGIC MO!) ---
def calculate_indicators(df):
    close = df['Close']
    
    # 1. MA 200
    ma_200 = close.rolling(200).mean()
    
    # 2. RSI
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / (loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    
    # 3. KINETIC TREND OSCILLATOR
    roc_14 = close.pct_change(14).fillna(0)
    vol_20 = close.pct_change().rolling(20).std() * np.sqrt(365)
    
    ma_50 = close.rolling(50).mean()
    std_50 = close.rolling(50).std()
    z_score = (close - ma_50) / (std_50 + 1e-9)
    
    kto = (roc_14 / (vol_20 + 1e-9)) * np.exp(-z_score)
    
    return ma_200, rsi, kto

# --- MAIN LOOP ---
st.write(f"⏳ **Live Scan Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

with st.spinner('🤖 Bender is calculating physics and gravity...'):
    results_list = []

    for ticker in WATCHLIST:
        try:
            df = yf.download(ticker, period="2y", interval="1d", progress=False, auto_adjust=True)
            if len(df) < 200: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            current_price = float(df['Close'].iloc[-1])
            
            ma_200_series, rsi_series, kto_series = calculate_indicators(df)
            
            ma_200 = float(ma_200_series.iloc[-1])
            rsi = float(rsi_series.iloc[-1])
            kto = float(kto_series.iloc[-1])
            
            dist_pct = ((current_price - ma_200) / ma_200) * 100
            
            # --- THE DECISION MATRIX ---
            action = "WAIT"
            comment = ""
            allocation = "0%"

            # SCENARIO 1: MARKET CRASH (Below Simento)
            if current_price < ma_200:
                if rsi < 30 and kto > -0.1:
                    action = "🛒 ACCUMULATE (SALE)"
                    comment = "Sale sa hardware. Ipon mode."
                    allocation = "10-20%"
                elif rsi < 30:
                    action = "✋ WAIT (FALLING KNIFE)"
                    comment = "Wag saluhin. Bubog yan."
                    allocation = "0%"
                else:
                    action = "⛔ STAY AWAY"
                    comment = "Lolo Bitcoin is tired. Tulog muna."
                    allocation = "0%"
            # SCENARIO 2: BULL MARKET (Above Simento)
            else:
                if kto > 0.1 and rsi < 70:
                    action = "🚀 STRONG BUY / RIDE"
                    comment = "Full Throttle! Sakay na!"
                    allocation = "50-100%"
                elif rsi > 75:
                    action = "💰 TAKE PROFIT / TRIM"
                    comment = "Sobrang init. Benta kaunti."
                    allocation = "Sell 20%"
                elif kto < 0:
                    action = "⚠️ CAUTION / HOLD"
                    comment = "Mahina hatak. Bantay sarado."
                    allocation = "Hold"
                else:
                    action = "✅ BUY THE DIP"
                    comment = "Nasa ibabaw ng semento. Goods yan."
                    allocation = "30-50%"

            # Append to list
            results_list.append({
                "COIN": ticker.replace("-USD", ""),
                "PRICE ($)": f"${current_price:,.2f}",
                "MA200 ($)": f"${ma_200:,.2f}",
                "DIST %": f"{dist_pct:+.2f}%",
                "RSI": round(rsi, 1),
                "KTO": round(kto, 2),
                "ACTION 📢": action,
                "ALLOCATION": allocation,
                "COMMENTARY 💬": comment
            })

        except Exception as e:
            st.error(f"Error on {ticker}: {e}")

# --- RENDER TABLE ---
if results_list:
    df_results = pd.DataFrame(results_list)
    
    # Streamlit Magic: Highlighting logic para sa DataFrame
    def color_coding(val):
        if isinstance(val, str):
            if "🚀" in val or "✅" in val or "+" in val: return 'color: #00ffcc'
            if "⛔" in val or "✋" in val or "-" in val: return 'color: #ff4d4d'
            if "⚠️" in val or "🛒" in val or "💰" in val: return 'color: #ffcc00'
        return ''

    st.dataframe(df_results.style.map(color_coding), use_container_width=True, height=280)
else:
    st.warning("Walang data na nakuha. Baka tulog ang Yahoo Finance.")

st.markdown("---")
st.subheader("🍺 BENDER'S FINAL WORD: CLASS DISMISSED. TRABAHO NA. POTA. To the Moon!!!")

# ==============================================================================
# 🏟️ BENDER'S BACKTEST BATTLE ROYALE (3-Year KTO vs HODL) ADDON 🏟️
# ==============================================================================
import matplotlib.pyplot as plt
import warnings

warnings.filterwarnings('ignore')

st.markdown("---")
st.subheader("📊 BENDER'S BACKTEST BATTLE ROYALE (3-Year KTO vs HODL)")

# Gumamit tayo ng Expander para hindi nakaharang sa buong screen pagkabukas
with st.expander("Tignan ang Backtest Graphs & Report (Pindutin para bumuka)", expanded=False):
    st.write("🤖 *Fetching historical data and computing KTO backtest mathematics...*")
    
    # --- CONFIG ---
    BT_TICKERS = ["BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD"]
    PERIOD = "3y"
    TARGET_VOL = 0.50
    FEE_RATE = 0.0010

    plt.style.use('dark_background')
    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle("Kinetic Trend Oscillator (KTO V2) vs. Buy & Hold", fontsize=16, fontweight='bold', color='white')
    axes = axes.flatten()

    bt_results = []
    
    with st.spinner("Simulating 3 years of Warlord trades..."):
        for idx, ticker in enumerate(BT_TICKERS):
            # Fetch Data
            df = yf.download(ticker, period=PERIOD, interval="1d", progress=False, auto_adjust=True)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
            
            df = df[['Close']].copy()
            df['Ret'] = df['Close'].pct_change().fillna(0)
            
            # The Mathematics
            df['SMA_50'] = df['Close'].rolling(50).mean()
            df['Std_50'] = df['Close'].rolling(50).std()
            df['Z_50'] = (df['Close'] - df['SMA_50']) / (df['Std_50'] + 1e-9)
            df['Ann_Vol'] = df['Ret'].rolling(20).std() * np.sqrt(365)
            df['ROC_14'] = df['Close'].pct_change(14).fillna(0)
            df['KTO'] = (df['ROC_14'] / (df['Ann_Vol'] + 1e-9)) * np.exp(-df['Z_50']) * 10
            df['KTO_Smooth'] = df['KTO'].rolling(3).mean()
            
            # Signal Gen
            df['Signal'] = 0.0
            df.loc[df['KTO_Smooth'] > 0.05, 'Signal'] = 1   
            df.loc[df['KTO_Smooth'] < -0.05, 'Signal'] = 0   
            df['Signal'] = df['Signal'].ffill() 
            
            # Risk & Exec
            df['Vol_Weight'] = TARGET_VOL / (df['Ann_Vol'] + 1e-9)
            df['Vol_Weight'] = df['Vol_Weight'].clip(0, 1.5)
            df['Target_Position'] = df['Signal'] * df['Vol_Weight']
            
            df['Position'] = df['Target_Position'].shift(1).fillna(0) 
            df['Turnover'] = df['Position'].diff().abs().fillna(0)
            df['Fees'] = df['Turnover'] * FEE_RATE
            df['Strat_Ret'] = (df['Position'] * df['Ret']) - df['Fees']
            
            df_clean = df.dropna().copy()
            if len(df_clean) == 0: continue
                
            df_clean['Cum_Strat'] = (1 + df_clean['Strat_Ret']).cumprod()
            df_clean['Cum_Hold'] = (1 + df_clean['Ret']).cumprod()
            
            # KPIs
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
            
            # Plotting (Hindi ko ginalaw ang aesthetics mo)
            ax = axes[idx]
            ax.plot(df_clean.index, df_clean['Cum_Strat'], label='KTO Protocol (Fixed)', color='#00ffcc', linewidth=2)
            ax.plot(df_clean.index, df_clean['Cum_Hold'], label='Buy & Hold', color='#777777', linewidth=1.5, alpha=0.8)
            
            ax.fill_between(df_clean.index, df_clean['Cum_Strat'].min(), df_clean['Cum_Strat'].max(), 
                            where=df_clean['Position'] > 0, 
                            color='#00ffcc', alpha=0.05)
            
            ax.set_title(f"{ticker.replace('-USD', '')}", fontsize=12, fontweight='bold', color='white')
            ax.legend(loc='upper left', frameon=False, labelcolor='white')
            ax.grid(True, color='#333333', linestyle='--', alpha=0.5)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.set_ylabel("Equity Multiplier")

    plt.tight_layout()
    plt.subplots_adjust(top=0.92)
    
    # ETO ANG SIKRETO NG STREAMLIT (Pagpapalabas ng drawing sa web)
    st.pyplot(fig)
    
    st.markdown("### 🎯 3-YEAR BACKTEST REPORT")
    if bt_results:
        # Gamitin natin ulit ang color coding para sa table mo
        df_bt = pd.DataFrame(bt_results)
        st.dataframe(df_bt, use_container_width=True)
