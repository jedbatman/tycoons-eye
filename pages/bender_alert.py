# ==============================================================================
# BENDER OVERRIDE - STREAMLIT DASHBOARD
# Purpose:
#   1) Manual live dashboard
#   2) One "BENDER ONLINE" Telegram heartbeat per Streamlit session
#   3) Optional manual consolidated scan notification
#
# IMPORTANT:
# Scheduled 8:10 AM / 10:00 PM automation lives in scheduled_scan.py,
# NOT in this Streamlit page.
# ==============================================================================

from datetime import datetime
import warnings

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

warnings.filterwarnings("ignore")

# ------------------------------------------------------------------------------
# PAGE
# ------------------------------------------------------------------------------
st.set_page_config(page_title="Bender Override", layout="wide")
st.title("🎯 LIVE HYDRAULIC SIGNALS (Bender Override Status)")

WATCHLIST = [
    "BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "AVAX-USD",
    "XRP-USD", "XLM-USD", "LINK-USD", "DOGE-USD", "PEPE-USD", "SHIB-USD"
]

CAPITAL_PHP = st.sidebar.number_input(
    "War Chest (PHP)",
    min_value=0.0,
    value=560000.0,
    step=10000.0
)

FEE_RATE = 0.005
FRICTION_BARRIER = FEE_RATE * 3.0

# ------------------------------------------------------------------------------
# STREAMLIT SECRETS
# ------------------------------------------------------------------------------
def read_secret(*names):
    for name in names:
        try:
            value = st.secrets.get(name)
            if value:
                return str(value).strip()
        except Exception:
            pass
    return None


def get_telegram_credentials():
    token = read_secret("TELEGRAM_BOT_TOKEN", "TELEGRAM_TOKEN")
    chat_id = read_secret("TELEGRAM_CHAT_ID")
    return token, chat_id


def telegram_send(text):
    token, chat_id = get_telegram_credentials()

    if not token:
        return False, "Bot token missing sa Streamlit Secrets."

    if not chat_id:
        return False, "Chat ID missing sa Streamlit Secrets."

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    try:
        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": text,
                "disable_web_page_preview": True,
            },
            timeout=15,
        )

        try:
            data = response.json()
        except ValueError:
            data = {}

        if response.status_code != 200:
            return False, data.get("description", response.text[:300])

        if not data.get("ok", False):
            return False, str(data)

        return True, "sent"

    except requests.RequestException as exc:
        return False, str(exc)


# ------------------------------------------------------------------------------
# ONLINE HEARTBEAT
# ------------------------------------------------------------------------------
# Streamlit reruns often because of widgets.
# We only send one heartbeat per browser session, so it does not machine-gun you.
if "bender_online_heartbeat_sent" not in st.session_state:
    st.session_state.bender_online_heartbeat_sent = False

if not st.session_state.bender_online_heartbeat_sent:
    now_text = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")

    heartbeat = (
        "🤖 BENDER ONLINE\n\n"
        f"Dashboard session active: {now_text}\n"
        "Manual scanner is alive.\n\n"
        "Scheduled reports remain separate:\n"
        "☀️ 8:10 AM — Daily Report\n"
        "🌙 10:00 PM — Risk Check"
    )

    ok, status = telegram_send(heartbeat)

    if ok:
        st.session_state.bender_online_heartbeat_sent = True
    else:
        st.sidebar.warning(f"Heartbeat not sent: {status}")


# ------------------------------------------------------------------------------
# MARKET ENGINE
# ------------------------------------------------------------------------------
@st.cache_data(ttl=300, show_spinner=False)
def download_market_data(ticker):
    df = yf.download(
        ticker,
        period="4y",
        interval="1d",
        progress=False,
        auto_adjust=True,
        threads=False,
    )

    if df is None or df.empty:
        return pd.DataFrame()

    df = df.copy()

    if isinstance(df.columns, pd.MultiIndex):
        if "Close" in df.columns.get_level_values(0):
            df.columns = df.columns.get_level_values(0)
        elif "Close" in df.columns.get_level_values(-1):
            df.columns = df.columns.get_level_values(-1)

    if "Close" not in df.columns or "Volume" not in df.columns:
        return pd.DataFrame()

    return df


def engineer_hydrodynamics(df):
    df = df.copy()

    close = pd.to_numeric(df["Close"], errors="coerce")
    volume = pd.to_numeric(df["Volume"], errors="coerce")

    volume = volume.replace(0, np.nan).ffill().fillna(1.0)

    log_close = np.log(close.where(close > 0))
    velocity = log_close.diff(7)

    rho = volume / volume.rolling(50).mean()
    rho = rho.replace([np.inf, -np.inf], np.nan).fillna(1.0)

    dynamic_pressure = 0.5 * rho * velocity * velocity.abs()

    daily_ret = log_close.diff(1)
    viscosity = daily_ret.rolling(20).std() * np.sqrt(7)
    viscosity = viscosity.replace(0, np.nan).fillna(1e-8)

    reynolds = velocity.abs() / viscosity

    q_mean = dynamic_pressure.rolling(50).mean()
    q_std = dynamic_pressure.rolling(50).std().replace(0, np.nan).fillna(1e-8)
    hpfo_z = (dynamic_pressure - q_mean) / q_std

    df["Velocity"] = velocity
    df["Reynolds"] = reynolds
    df["HPFO_Z"] = hpfo_z

    return df


def latest_valid(series):
    clean = (
        pd.to_numeric(series, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )
    return None if clean.empty else float(clean.iloc[-1])


def classify_signal(hpfo, reynolds, velocity):
    if hpfo is None or reynolds is None or velocity is None:
        return "⚠️ INSUFFICIENT DATA"

    if hpfo > 1.65 and reynolds > 0.9 and velocity > FRICTION_BARRIER:
        return "🚰 OPEN VALVE (BUY)"

    if velocity < 0 or hpfo < 0:
        return "⛔ EMERGENCY EXIT"

    return "⏳ MAINTAIN PRESSURE"


# ------------------------------------------------------------------------------
# SCAN
# ------------------------------------------------------------------------------
results = []
errors = []

with st.spinner("🤖 Bender is scanning the matrix..."):
    for ticker in WATCHLIST:
        try:
            df = download_market_data(ticker)

            if df.empty or len(df) < 200:
                errors.append(f"{ticker}: insufficient market data")
                continue

            df = engineer_hydrodynamics(df)

            close = pd.to_numeric(df["Close"], errors="coerce")
            current_price = latest_valid(close)

            if current_price is None:
                errors.append(f"{ticker}: invalid latest price")
                continue

            ma200 = latest_valid(close.rolling(200).mean())
            if ma200 is None:
                ma200 = current_price

            dist_pct = ((current_price - ma200) / ma200) * 100 if ma200 else np.nan

            delta = close.diff()
            gain = delta.clip(lower=0).rolling(14).mean()
            loss = (-delta.clip(upper=0)).rolling(14).mean()
            rs = gain / (loss + 1e-9)
            rsi = latest_valid(100 - (100 / (1 + rs)))

            hpfo = latest_valid(df["HPFO_Z"])
            reynolds = latest_valid(df["Reynolds"])
            velocity = latest_valid(df["Velocity"])

            action = classify_signal(hpfo, reynolds, velocity)

            results.append({
                "COIN": ticker.replace("-USD", ""),
                "PRICE ($)": f"${current_price:,.4f}" if current_price < 1 else f"${current_price:,.2f}",
                "MA200 ($)": f"${ma200:,.4f}" if ma200 < 1 else f"${ma200:,.2f}",
                "DIST %": f"{dist_pct:+.2f}%" if np.isfinite(dist_pct) else "N/A",
                "RSI": round(rsi, 1) if rsi is not None else "N/A",
                "HPFO Z": round(hpfo, 2) if hpfo is not None else "N/A",
                "REYNOLDS": round(reynolds, 2) if reynolds is not None else "N/A",
                "VELOCITY": round(velocity, 3) if velocity is not None else "N/A",
                "ACTION 📢": action,
            })

        except Exception as exc:
            errors.append(f"{ticker}: {type(exc).__name__}: {exc}")


if results:
    df_live = pd.DataFrame(results)
    st.dataframe(df_live, use_container_width=True, hide_index=True)
else:
    st.error("Market data unavailable.")


# ------------------------------------------------------------------------------
# MANUAL CONSOLIDATED TELEGRAM REPORT
# ------------------------------------------------------------------------------
st.sidebar.markdown("---")
st.sidebar.markdown("### 📲 Telegram")

token, chat_id = get_telegram_credentials()

if token:
    st.sidebar.success("✅ Bot Token detected")
else:
    st.sidebar.error("❌ Bot Token missing")

if chat_id:
    st.sidebar.success("✅ Chat ID detected")
else:
    st.sidebar.error("❌ Chat ID missing")


def build_manual_report(rows):
    buy = [r for r in rows if "BUY" in r["ACTION 📢"]]
    hold = [r for r in rows if "MAINTAIN" in r["ACTION 📢"]]
    exit_rows = [r for r in rows if "EXIT" in r["ACTION 📢"]]

    lines = [
        "🧪 BENDER MANUAL DASHBOARD SCAN",
        datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "",
        "🚰 BUY",
        ", ".join(r["COIN"] for r in buy) if buy else "None",
        "",
        "⛔ EXIT",
        ", ".join(r["COIN"] for r in exit_rows) if exit_rows else "None",
        "",
        "⏳ HOLD",
        ", ".join(r["COIN"] for r in hold) if hold else "None",
        "",
        "Manual Streamlit scan only.",
    ]
    return "\n".join(lines)


if st.sidebar.button("📨 SEND CURRENT SCAN", use_container_width=True):
    if results:
        ok, status = telegram_send(build_manual_report(results))
        if ok:
            st.sidebar.success("✅ Current scan sent")
        else:
            st.sidebar.error(f"❌ {status}")
    else:
        st.sidebar.error("No scan data to send.")


if st.sidebar.button("🤖 SEND ONLINE HEARTBEAT", use_container_width=True):
    ok, status = telegram_send(
        "🤖 BENDER ONLINE — manual heartbeat\n"
        f"{datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}"
    )
    if ok:
        st.sidebar.success("✅ Heartbeat sent")
    else:
        st.sidebar.error(f"❌ {status}")


if errors:
    with st.expander("⚠️ Scan errors", expanded=False):
        for err in errors:
            st.write(f"- {err}")

st.caption(
    "☀️ Scheduled 8:10 AM report and 🌙 10:00 PM risk check "
    "are handled separately by GitHub Actions."
)
