# ==============================================================================
# MODULE 9: THE BENDER OVERRIDE (E.S.V.E)
# Telegram Secrets + Diagnostics + Anti-Spam Version
# ==============================================================================

import warnings
from datetime import datetime

import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

warnings.filterwarnings("ignore")

# ==============================================================================
# PAGE SETTINGS
# ==============================================================================
st.set_page_config(
    page_title="Bender Override (E.S.V.E)",
    layout="wide"
)

st.title("🛢️ MODULE 9: THE BENDER OVERRIDE (E.S.V.E)")
st.markdown(
    "**Powered by Warlord Jed Racho x Chaotic Genius Engine** | "
    "Ethereum-Specific Viscosity Engine"
)
st.info(
    "💡 **LOGIC:** 7-Day Velocity + Reynolds-style flow + HPFO Z pressure. "
    "BUY/EXIT alerts can be sent to Telegram. Signal engine lamang ito; "
    "walang automatic trade execution."
)

# ==============================================================================
# CHEAT SHEET
# ==============================================================================
with st.expander(
    "📖 BENDER'S CHEAT SHEET (Ang Bagong Warlord Physics)",
    expanded=True
):
    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown("### 1. HPFO Z")
        st.write("🌊 **> +1.65:** Strong BUY pressure")
        st.write("💧 **< 0.0:** EXIT pressure")

    with c2:
        st.markdown("### 2. REYNOLDS")
        st.write("🟢 **> 0.9:** Flow threshold passed")
        st.write("🔴 **< 0.9:** Weak / noisy flow")

    with c3:
        st.markdown("### 3. VELOCITY")
        st.write("🚀 **> 0.015:** Positive 7-day velocity")
        st.write("💥 **< 0.0:** Emergency exit trigger")

    with c4:
        st.markdown("### 4. THE VALVE")
        st.write("🚰 **OPEN VALVE:** BUY")
        st.write("⛔ **EMERGENCY EXIT:** SELL / EXIT")
        st.write("⏳ **MAINTAIN PRESSURE:** HOLD")

st.markdown("---")

# ==============================================================================
# CONFIGURATION
# ==============================================================================
WATCHLIST = [
    "BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "AVAX-USD",
    "XRP-USD", "XLM-USD", "LINK-USD", "DOGE-USD",
    "PEPE-USD", "SHIB-USD"
]

CAPITAL_PHP = st.sidebar.number_input(
    "War Chest (PHP)",
    min_value=0.0,
    value=560000.0,
    step=10000.0
)

FEE_RATE = 0.005
FRICTION_BARRIER = FEE_RATE * 3.0  # 0.015

AUTO_TELEGRAM = st.sidebar.toggle(
    "📲 Auto Telegram BUY/EXIT alerts",
    value=True
)

st.write(
    f"⏳ **Live Scan Time:** "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)

# ==============================================================================
# STREAMLIT SECRET HELPERS
# ==============================================================================
def read_secret(*names):
    """
    Return the first non-empty secret among the supplied names.

    This intentionally supports BOTH:
      TELEGRAM_BOT_TOKEN  <- preferred new name
      TELEGRAM_TOKEN      <- Brother Eye legacy name
    """
    for name in names:
        try:
            value = st.secrets.get(name)
            if value:
                return str(value).strip()
        except Exception:
            pass

    return None


def get_telegram_credentials():
    token = read_secret(
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_TOKEN"
    )
    chat_id = read_secret(
        "TELEGRAM_CHAT_ID"
    )
    return token, chat_id


# ==============================================================================
# TELEGRAM AGENT
# ==============================================================================
def send_warlord_telegram_alert(
    coin,
    price,
    hpfo_z,
    reynolds,
    velocity,
    action,
    allocation,
    comment
):
    token, chat_id = get_telegram_credentials()

    if not token:
        return False, (
            "Walang Telegram bot token. "
            "Maglagay ng TELEGRAM_BOT_TOKEN o TELEGRAM_TOKEN sa Streamlit Secrets."
        )

    if not chat_id:
        return False, (
            "Walang TELEGRAM_CHAT_ID sa Streamlit Secrets."
        )

    if "BUY" in action:
        emoji = "🌊💸🚀"
        vibe = (
            f"GAGO GISING!!! BUY signal sa {coin}. "
            f"Malakas ang pressure + flow + velocity."
        )

    elif "EXIT" in action:
        emoji = "🚨📉🛑"
        vibe = (
            f"PUTANGINA, EMERGENCY EXIT signal sa {coin}. "
            f"Humina ang flow ayon sa engine."
        )

    else:
        emoji = "🚰🛌"
        vibe = (
            f"HOLD muna sa {coin}. "
            f"Wala pang kumpletong valve confirmation."
        )

    message = (
        f"{emoji} WARLORD QUANT AGENT ALERT {emoji}\n\n"
        f"{vibe}\n\n"
        f"📊 Asset: {coin}\n"
        f"💰 Live Price: {price}\n"
        f"📈 HPFO Z: {hpfo_z}\n"
        f"🌊 Reynolds: {reynolds}\n"
        f"🏎️ Velocity: {velocity}\n"
        f"⚙️ Command: {action}\n"
        f"💼 Allocation: {allocation}\n\n"
        f"💡 Commentary: {comment}\n\n"
        f"⚠️ Signal alert lamang ito. Walang automatic trade."
    )

    # CORRECT Telegram Bot API endpoint
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=15
        )

        # Try to expose Telegram's exact response if something fails.
        try:
            data = response.json()
        except ValueError:
            data = {}

        if response.status_code != 200:
            description = data.get(
                "description",
                response.text[:300]
            )
            return False, (
                f"Telegram HTTP {response.status_code}: {description}"
            )

        if not data.get("ok", False):
            return False, (
                f"Telegram API error: {data}"
            )

        return True, "Telegram alert sent successfully."

    except requests.RequestException as exc:
        return False, (
            f"Network / Telegram request error: {exc}"
        )


# ==============================================================================
# TELEGRAM DIAGNOSTICS
# ==============================================================================
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔧 Telegram Diagnostic")

telegram_token, telegram_chat_id = get_telegram_credentials()

if telegram_token:
    st.sidebar.success("✅ Bot Token detected")
else:
    st.sidebar.error("❌ Bot Token missing")

if telegram_chat_id:
    st.sidebar.success("✅ Chat ID detected")
else:
    st.sidebar.error("❌ Chat ID missing")

if st.sidebar.button(
    "📨 TEST TELEGRAM NOW",
    use_container_width=True
):
    ok, status = send_warlord_telegram_alert(
        coin="BENDER SYSTEM TEST",
        price="N/A",
        hpfo_z="N/A",
        reynolds="N/A",
        velocity="N/A",
        action="⏳ TEST MESSAGE",
        allocation="N/A",
        comment=(
            "Kung nababasa mo ito sa Telegram, "
            "buhay ang Streamlit → Telegram connection."
        )
    )

    if ok:
        st.sidebar.success("✅ " + status)
    else:
        st.sidebar.error("❌ " + status)


# ==============================================================================
# DATA HELPERS
# ==============================================================================
@st.cache_data(ttl=300, show_spinner=False)
def download_market_data(ticker):
    df = yf.download(
        ticker,
        period="4y",
        interval="1d",
        progress=False,
        auto_adjust=True,
        threads=False
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


def engineer_eth_hydrodynamics(df):
    df = df.copy()

    close = pd.to_numeric(
        df["Close"],
        errors="coerce"
    )

    volume = pd.to_numeric(
        df["Volume"],
        errors="coerce"
    )

    volume = (
        volume
        .replace(0, np.nan)
        .ffill()
        .fillna(1.0)
    )

    log_close = np.log(
        close.where(close > 0)
    )

    velocity = log_close.diff(7)

    rho = (
        volume
        / volume.rolling(50).mean()
    )

    rho = (
        rho
        .replace([np.inf, -np.inf], np.nan)
        .fillna(1.0)
    )

    dynamic_pressure = (
        0.5
        * rho
        * velocity
        * velocity.abs()
    )

    daily_ret = log_close.diff(1)

    viscosity = (
        daily_ret
        .rolling(20)
        .std()
        * np.sqrt(7)
    )

    viscosity = (
        viscosity
        .replace(0, np.nan)
        .fillna(1e-8)
    )

    reynolds = (
        velocity.abs()
        / viscosity
    )

    q_mean = (
        dynamic_pressure
        .rolling(50)
        .mean()
    )

    q_std = (
        dynamic_pressure
        .rolling(50)
        .std()
        .replace(0, np.nan)
        .fillna(1e-8)
    )

    hpfo_z = (
        dynamic_pressure
        - q_mean
    ) / q_std

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

    if clean.empty:
        return None

    return float(clean.iloc[-1])


def classify_signal(
    hpfo,
    reynolds,
    velocity
):
    if (
        hpfo is None
        or reynolds is None
        or velocity is None
    ):
        return (
            "⚠️ INSUFFICIENT DATA",
            "₱0.00",
            "Kulang ang latest indicator data."
        )

    if (
        hpfo > 1.65
        and reynolds > 0.9
        and velocity > FRICTION_BARRIER
    ):
        return (
            "🚰 OPEN VALVE (BUY)",
            f"₱{CAPITAL_PHP * 0.25:,.2f} (25%)",
            "Strong pressure + flow + velocity confirmation."
        )

    if (
        velocity < 0
        or hpfo < 0
    ):
        return (
            "⛔ EMERGENCY EXIT",
            "₱0.00",
            "Negative velocity o negative HPFO pressure."
        )

    return (
        "⏳ MAINTAIN PRESSURE",
        "Hold Status",
        "Wala pang kumpletong BUY o EXIT confirmation."
    )


# ==============================================================================
# ANTI-SPAM MEMORY FOR CURRENT STREAMLIT SESSION
# ==============================================================================
if "sent_alert_keys" not in st.session_state:
    st.session_state.sent_alert_keys = set()

if st.sidebar.button(
    "♻️ Reset alert memory",
    use_container_width=True
):
    st.session_state.sent_alert_keys = set()
    st.sidebar.info(
        "Alert memory reset. BUY/EXIT signals may send again."
    )


# ==============================================================================
# LIVE SIGNAL DASHBOARD
# ==============================================================================
st.subheader(
    "🎯 LIVE HYDRAULIC SIGNALS "
    "(Bender Override Status)"
)

live_results = []
errors_log = []

with st.spinner(
    "🤖 Bender is scanning the matrix..."
):
    for ticker in WATCHLIST:
        try:
            df = download_market_data(
                ticker
            )

            if df.empty or len(df) < 200:
                errors_log.append(
                    f"{ticker}: kulang o walang market data."
                )
                continue

            df = engineer_eth_hydrodynamics(
                df
            )

            current_price = latest_valid(
                df["Close"]
            )

            if current_price is None:
                errors_log.append(
                    f"{ticker}: walang valid latest price."
                )
                continue

            ma_200 = (
                df["Close"]
                .rolling(200)
                .mean()
            )

            ma200_val = latest_valid(
                ma_200
            )

            if ma200_val is None:
                ma200_val = current_price

            dist_pct = (
                (
                    current_price
                    - ma200_val
                )
                / ma200_val
            ) * 100

            delta = (
                df["Close"]
                .diff()
            )

            gain = (
                delta
                .clip(lower=0)
                .rolling(14)
                .mean()
            )

            loss = (
                -delta
                .clip(upper=0)
                .rolling(14)
                .mean()
            )

            rs = (
                gain
                / (loss + 1e-9)
            )

            rsi = (
                100
                - (100 / (1 + rs))
            )

            rsi_val = latest_valid(
                rsi
            )

            vel = latest_valid(
                df["Velocity"]
            )

            rey = latest_valid(
                df["Reynolds"]
            )

            hpfo = latest_valid(
                df["HPFO_Z"]
            )

            action, allocation, comment = (
                classify_signal(
                    hpfo,
                    rey,
                    vel
                )
            )

            coin_name = ticker.replace(
                "-USD",
                ""
            )

            # --------------------------------------------------------------
            # AUTO TELEGRAM BUY / EXIT
            # --------------------------------------------------------------
            if (
                AUTO_TELEGRAM
                and (
                    "BUY" in action
                    or "EXIT" in action
                )
            ):
                # One notification per coin/action/day
                alert_key = (
                    datetime.now()
                    .strftime("%Y-%m-%d"),
                    coin_name,
                    action
                )

                if (
                    alert_key
                    not in st.session_state.sent_alert_keys
                ):
                    ok, status = (
                        send_warlord_telegram_alert(
                            coin=coin_name,
                            price=f"${current_price:,.2f}",
                            hpfo_z=(
                                round(hpfo, 2)
                                if hpfo is not None
                                else "N/A"
                            ),
                            reynolds=(
                                round(rey, 2)
                                if rey is not None
                                else "N/A"
                            ),
                            velocity=(
                                round(vel, 3)
                                if vel is not None
                                else "N/A"
                            ),
                            action=action,
                            allocation=allocation,
                            comment=comment
                        )
                    )

                    if ok:
                        st.session_state.sent_alert_keys.add(
                            alert_key
                        )
                    else:
                        errors_log.append(
                            f"{coin_name}: {status}"
                        )

            live_results.append({
                "COIN": coin_name,
                "PRICE ($)": f"${current_price:,.2f}",
                "MA200 ($)": f"${ma200_val:,.2f}",
                "DIST %": f"{dist_pct:+.2f}%",
                "RSI": (
                    round(rsi_val, 1)
                    if rsi_val is not None
                    else "N/A"
                ),
                "HPFO Z": (
                    round(hpfo, 2)
                    if hpfo is not None
                    else "N/A"
                ),
                "REYNOLDS": (
                    round(rey, 2)
                    if rey is not None
                    else "N/A"
                ),
                "VELOCITY": (
                    round(vel, 3)
                    if vel is not None
                    else "N/A"
                ),
                "ACTION 📢": action,
                "ALLOCATION": allocation,
                "COMMENTARY 💬": comment
            })

        except Exception as exc:
            errors_log.append(
                f"{ticker}: "
                f"{type(exc).__name__}: {exc}"
            )


if live_results:
    df_live = pd.DataFrame(
        live_results
    )

    def color_coding(val):
        if isinstance(val, str):
            if "🚰" in val:
                return (
                    "color: #00ffcc; "
                    "font-weight: bold;"
                )

            if "⛔" in val:
                return (
                    "color: #ff4d4d; "
                    "font-weight: bold;"
                )

            if "⏳" in val:
                return (
                    "color: #ffcc00;"
                )

        return ""

    st.dataframe(
        df_live.style.map(
            color_coding
        ),
        use_container_width=True,
        hide_index=True
    )

else:
    st.error(
        "Market Data Unavailable."
    )


if errors_log:
    with st.expander(
        "⚠️ Scan / Telegram errors",
        expanded=False
    ):
        for err in errors_log:
            st.write(
                f"- {err}"
            )


# ==============================================================================
# BACKTEST PLACEHOLDER
# ==============================================================================
st.markdown("---")
st.subheader(
    "📊 4-YEAR BACKTEST: "
    "BENDER OVERRIDE "
    "(0.5% Fee Imposed)"
)

with st.expander(
    "Tignan ang 4-Year Lab Report",
    expanded=False
):
    st.write(
        "Backtest temporarily disabled sa notification build "
        "para mas mabilis ang live scan."
    )
