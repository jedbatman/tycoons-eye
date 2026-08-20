# ==============================================================================
# MODULE 9: THE BENDER OVERRIDE (E.S.V.E)
# Streamlit Secrets Active Version | Built by Chaotic Genius Warlord
# ==============================================================================

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import warnings
import requests

warnings.filterwarnings('ignore')

# ==========================================
# PAGE SETTINGS & HEADER
# ==========================================
st.set_page_config(page_title="Bender Override (E.S.V.E)", layout="wide")

st.title("🛢️ MODULE 9: THE BENDER OVERRIDE (E.S.V.E)")
st.markdown("**Powered by Warlord Jed Racho x Chaotic Genius Engine** | Ethereum-Specific Viscosity Engine")
st.info("💡 **LOGIC:** Ang makinang ito ay nakatono para sa malapot at mabigat na liquidity ng Ethereum. May 7-Day Velocity trigger at Brutal Ejection Protocol para iwasan ang dambuhalang bear market drops!")

# --- BENDER'S CHEAT SHEET ---
with st.expander("📖 BENDER'S CHEAT SHEET (Ang Bagong Warlord Physics)", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("### 1. HPFO Z (Pressure)")
        st.write("🌊 **> +1.65:** Baha na! (Strong Buy).")
        st.write("💧 **< 0.0:** Tuyo na (Brutal Sell).")
    with col2:
        st.markdown("### 2. REYNOLDS (Flow)")
        st.write("🟢 **> 0.9:** Pasado sa ETH Slurry.")
        st.write("🔴 **< 0.9:** Magulong putik.")
    with col3:
        st.markdown("### 3. VELOCITY (Speed)")
        st.write("🚀 **> 0.015:** Kayang bayaran ang PDAX Fee.")
        st.write("💥 **< 0.0:** EMERGENCY EXIT (Bagsak!).")
    with col4:
        st.markdown("### 4. THE VALVE (Action)")
        st.write("🚰 **OPEN VALVE:** Saluhin ang baha!")
        st.write("⛔ **EMERGENCY EXIT:** Putulin ang linya!")

st.markdown("---")

# --- CONFIGURATION ---
WATCHLIST = [
    "BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "AVAX-USD",
    "XRP-USD", "XLM-USD", "LINK-USD",
    "DOGE-USD", "PEPE-USD", "SHIB-USD"
]
CAPITAL_PHP = st.sidebar.number_input("War Chest (PHP)", value=560000.0, step=10000.0)
FEE_RATE = 0.005 

st.write(f"⏳ **Live Scan Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ==========================================
# TELEGRAM AGENT NOTIFICATION WITH SECRETS
# ==========================================
def send_warlord_telegram_alert(coin, price, hpfo_z, reynolds, velocity, action, allocation, comment):
    try:
        # Higupin ang ligtas na selyo mula sa Streamlit Cloud Cloud Settings, kupal!
        TOKEN = st.secrets["TELEGRAM_TOKEN"]
        CHAT_ID = st.secrets["TELEGRAM_CHAT_ID"]
        
        if "BUY" in action:
            emoji = "🌊💸🚀"
            vibe_check = f"GAGO GISING!!! Nagbabaha ng pera sa {coin}! Patakbuhin mo na ang water pump sa PDAX!"
        elif "EXIT" in action:
            emoji = "🚨📉🛑"
            vibe_check = f"PUTANGINA TUMAKBO KA NA SA BUNKER!!! Bagsak ang agos sa {coin}! Ligtas ang kapital!"
        else:
            emoji = "🚰🛌"
            vibe_check = f"Matulog ka na muna o mag-semento sa Burgos. Nag-iipon lang ng bwelo si {coin}."

        message = (
            f"{emoji} *WARLORD QUANT AGENT ALERT* {emoji}\n\n"
            f"*{vibe_check}*\n\n"
            f"📊 *Asset:* {coin}\n"
            f"💰 *Live Price:* {price}\n"
            f"📈 *HPFO Z (Pressure):* {hpfo_z}\n"
            f"🌊 *Reynolds (Flow):* {reynolds}\n"
            f"🏎️ *Velocity (Speed):* {velocity}\n"
            f"⚙️ *Command:* {action}\n"
            f"💼 *Allocation:* {allocation}\n\n"
            f"💡 *Commentary:* _{comment}_"
        )
        
        url = f"https://telegram.org{TOKEN}/sendMessage"
        payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
        requests.post(url, json=payload)
    except Exception as e:
        st.sidebar.error(f"⚠️ Notification Error: {str(e)}")

# ==========================================
# THE ALIEN PHYSICS ENGINE (E.S.V.E)
# ==========================================
def engineer_eth_hydrodynamics(df):
    close = df['Close']
    volume = df['Volume'].replace(0, np.nan).ffill().fillna(1)
    log_close = np.log(close)
    velocity = log_close.diff(7)
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
# 1. LIVE SIGNAL DASHBOARD
# ==========================================
st.subheader("🎯 LIVE HYDRAULIC SIGNALS (Bender Override Status)")

# Tiyakin kung nakasaksak ang secrets bago patakbuhin, gago
if "TELEGRAM_TOKEN" not in st.secrets or "TELEGRAM_CHAT_ID" not in st.secrets:
    st.error("❌ ERROR: Kulang ka sa Hakbang 1, kupal! Isaksak mo muna ang Token at Chat ID sa Streamlit Secrets settings sa kanan!")
else:
    with st.spinner('🤖 Bender is scanning the matrix...'):
        live_results = []
        errors_log = []
        friction_barrier = FEE_RATE * 3.0
        
        for ticker in WATCHLIST:
            try:
                df = yf.download(ticker, period="4y", interval="1d", progress=False, auto_adjust=True)
                if len(df) < 200: continue
                if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
                
                df = engineer_eth_hydrodynamics(df)
                
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
                
                if hpfo > 1.65 and rey > 0.9 and vel > friction_barrier:
                    action = "🚰 OPEN VALVE (BUY)"
                    allocation = f"₱{(CAPITAL_PHP * 0.25):,.2f} (25%)"
                    comment = "Strong pressure + flow + velocity confirmation."
                elif vel < 0 or hpfo < 0:
                    action = "⛔ EMERGENCY EXIT"
                    allocation = "₱0.00"
                    comment = "Bumabagsak ang agos! Brutal Ejection!"
                else:
                    action = "⏳ MAINTAIN PRESSURE"
                    allocation = "Hold Status"
                    comment = "Wala pang kumpletong BUY o EXIT confirmation."
                    
                coin_name = ticker.replace("-USD", "")
                
                if "BUY" in action or "EXIT" in action:
                    send_warlord_telegram_alert(coin_name, f"${current_price:,.2f}", round(hpfo, 2), round(rey, 2), round(vel, 3), action, allocation, comment)
                    
                live_results.append({
                    "COIN": coin_name, "PRICE ($)": f"${current_price:,.2f}", "MA200 ($)": f"${ma200_val:,.2f}",
                    "DIST %": f"{dist_pct:+.2f}%", "RSI": round(rsi_val, 1), "HPFO Z": round(hpfo, 2),
                    "REYNOLDS": round(rey, 2), "VELOCITY": round(vel, 3), "ACTION 📢": action,
                    "ALLOCATION": allocation, "COMMENTARY 💬": comment
                })
            except Exception as e:
                errors_log.append(f"• {ticker.replace('-USD', '')}: {str(e)}")
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
            
        if errors_log:
            with st.expander("⚠️ Scan / Telegram errors"):
                for err in errors_log: st.write(err)

# ==========================================
# 2. THE WARLORD BACKTEST MATRIX
# ==========================================
st.markdown("---")
st.subheader("📊 4-YEAR BACKTEST: BENDER OVERRIDE (0.5% Fee Imposed)")
with st.expander("Tignan ang 4-Year Lab Report", expanded=False):
    st.write("Backtest disabled on live notification scan to optimize traffic fluid flow.")
