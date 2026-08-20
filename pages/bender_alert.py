# ==============================================================================
# MODULE 9: THE BENDER OVERRIDE (E.S.V.E)
# Telegram Agent Active Version | Repaired from Brother Eye's version
# ==============================================================================

import warnings
from datetime import datetime

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import streamlit as st
import yfinance as yf

warnings.filterwarnings("ignore")

# ==========================================
# PAGE SETTINGS & HEADER
# ==========================================
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
    "💡 **LOGIC:** Ang makinang ito ay nakatono para sa malapot at mabigat "
    "na liquidity ng Ethereum. May 7-Day Velocity trigger at Brutal Ejection "
    "Protocol para iwasan ang dambuhalang bear market drops!"
)

# --- BENDER'S CHEAT SHEET ---
with st.expander(
    "📖 BENDER'S CHEAT SHEET (Ang Bagong Warlord Physics)",
    expanded=True
):
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

# ==========================================
# CONFIGURATION
# ==========================================
WATCHLIST = [
    "BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "AVAX-USD",
    "XRP-USD", "XLM-USD", "LINK-USD",
    "DOGE-USD", "PEPE-USD", "SHIB-USD"
]

BACKTEST_TICKERS = [
    "ETH-USD", "BTC-USD", "SOL-USD",
    "XLM-USD", "XRP-USD", "ADA-USD"
]

CAPITAL_PHP = st.sidebar.number_input(
    "War Chest (PHP)",
    value=560000.0,
    step=10000.0
)

FEE_RATE = 0.005  # 0.5% PDAX Fee
FRICTION_BARRIER = FEE_RATE * 3.0  # 0.015

st.write(
    f"⏳ **Live Scan Time:** "
    f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
)

# ==========================================
# TELEGRAM CONFIG
# ==========================================
# Ilagay sa Streamlit Cloud:
# App -> Settings -> Secrets
#
# TELEGRAM_BOT_TOKEN = "NEW_TOKEN_HERE"
# TELEGRAM_CHAT_ID = "YOUR_CHAT_ID_HERE"
#
# Huwag i-hardcode ang bot token sa public GitHub repo.

def get_secret(name):
    try:
        return st.secrets[name]
    except Exception:
        return None


# ==========================================
# TELEGRAM AGENT NOTIFICATION FUNCTION
# ==========================================
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
    token = get_secret("TELEGRAM_BOT_TOKEN")
    chat_id = get_secret("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return False, "Telegram secrets missing."

    if "BUY" in action:
        emoji = "🌊💸🚀"
        vibe_check = (
            f"GAGO GISING!!! Nagbabaha ng pera sa {coin}! "
            f"Patakbuhin mo na ang water pump sa PDAX!"
        )

    elif "EXIT" in action:
        emoji = "🚨📉🛑"
        vibe_check = (
            f"PUTANGINA TUMAKBO KA NA SA BUNKER!!! "
            f"Bagsak ang agos sa {coin}! Ligtas ang kapital!"
        )

    else:
        emoji = "🚰🛌"
        vibe_check = (
            f"Matulog ka na muna o mag-semento sa Burgos. "
            f"Nag-iipon lang ng bwelo si {coin}."
        )

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

    # IMPORTANT:
    # Ito ang tamang Telegram Bot API endpoint.
    url = f"https://api.telegram.org/bot{token}/sendMessage"

    payload = {
        "chat_id": str(chat_id),
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True
    }

    try:
        response = requests.post(
            url,
            json=payload,
            timeout=15
        )
        response.raise_for_status()

        data = response.json()

        if not data.get("ok", False):
            return False, str(data)

        return True, "Telegram alert sent."

    except requests.RequestException as e:
        return False, f"Telegram error: {e}"


# ==========================================
# THE ALIEN PHYSICS ENGINE (E.S.V.E)
# ==========================================
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
        .fillna(1)
    )

    log_close = np.log(close.where(close > 0))

    velocity = log_close.diff(7)

    rho = volume / volume.rolling(50).mean()
    rho = rho.replace(
        [np.inf, -np.inf],
        np.nan
    ).fillna(1.0)

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

    reynolds = velocity.abs() / viscosity

    q_mean = dynamic_pressure.rolling(50).mean()

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


# ==========================================
# YFINANCE HELPER
# ==========================================
def download_data(ticker):
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
        else:
            df.columns = df.columns.get_level_values(-1)

    return df


# ==========================================
# 1. LIVE SIGNAL DASHBOARD
# ==========================================
st.subheader(
    "🎯 LIVE HYDRAULIC SIGNALS "
    "(Bender Override Status)"
)

with st.spinner(
    "🤖 Bender is scanning the matrix..."
):
    live_results = []
    live_errors = []

    for ticker in WATCHLIST:
        try:
            df = download_data(ticker)

            if df.empty or len(df) < 200:
                continue

            df = engineer_eth_hydrodynamics(df)

            current_price = float(
                df["Close"].iloc[-1]
            )

            ma_200 = (
                df["Close"]
                .rolling(200)
                .mean()
            )

            ma200_val = (
                float(ma_200.iloc[-1])
                if len(ma_200.dropna()) > 0
                else current_price
            )

            dist_pct = (
                (current_price - ma200_val)
                / ma200_val
            ) * 100

            delta = df["Close"].diff()

            gain = (
                delta
                .where(delta > 0, 0)
                .rolling(window=14)
                .mean()
            )

            loss = (
                -delta
                .where(delta < 0, 0)
                .rolling(window=14)
                .mean()
            )

            rs = gain / (loss + 1e-9)

            rsi = 100 - (
                100 / (1 + rs)
            )

            rsi_val = float(
                rsi.iloc[-1]
            )

            vel = float(
                df["Velocity"].iloc[-1]
            )

            rey = float(
                df["Reynolds"].iloc[-1]
            )

            hpfo = float(
                df["HPFO_Z"].iloc[-1]
            )

            # ==========================================
            # BENDER SIGNAL LOGIC
            # ==========================================
            if (
                hpfo > 1.65
                and rey > 0.9
                and vel > FRICTION_BARRIER
            ):
                action = "🚰 OPEN VALVE (BUY)"

                allocation = (
                    f"₱{CAPITAL_PHP * 0.25:,.2f} "
                    f"(25%)"
                )

                comment = (
                    "Strong pressure + flow + "
                    "velocity confirmation."
                )

            elif (
                vel < 0
                or hpfo < 0
            ):
                action = "⛔ EMERGENCY EXIT"

                allocation = "₱0.00"

                comment = (
                    "Bumabagsak ang agos! "
                    "Brutal Ejection!"
                )

            else:
                action = (
                    "⏳ MAINTAIN PRESSURE"
                )

                allocation = "Hold Status"

                comment = (
                    "Wala pang kumpletong "
                    "BUY o EXIT confirmation."
                )

            coin_name = ticker.replace(
                "-USD",
                ""
            )

            # ==========================================
            # TELEGRAM TRIGGER
            # ==========================================
            # BUY at EXIT lang para hindi spam ang HOLD.
            if (
                "BUY" in action
                or "EXIT" in action
            ):
                ok, telegram_status = (
                    send_warlord_telegram_alert(
                        coin=coin_name,
                        price=f"${current_price:,.2f}",
                        hpfo_z=round(hpfo, 2),
                        reynolds=round(rey, 2),
                        velocity=round(vel, 3),
                        action=action,
                        allocation=allocation,
                        comment=comment
                    )
                )

                if not ok:
                    live_errors.append(
                        f"{coin_name}: "
                        f"{telegram_status}"
                    )

            live_results.append({
                "COIN": coin_name,
                "PRICE ($)": (
                    f"${current_price:,.2f}"
                ),
                "MA200 ($)": (
                    f"${ma200_val:,.2f}"
                ),
                "DIST %": (
                    f"{dist_pct:+.2f}%"
                ),
                "RSI": round(
                    rsi_val,
                    1
                ),
                "HPFO Z": round(
                    hpfo,
                    2
                ),
                "REYNOLDS": round(
                    rey,
                    2
                ),
                "VELOCITY": round(
                    vel,
                    3
                ),
                "ACTION 📢": action,
                "ALLOCATION": allocation,
                "COMMENTARY 💬": comment
            })

        except Exception as e:
            live_errors.append(
                f"{ticker}: "
                f"{type(e).__name__}: {e}"
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

    if live_errors:
        with st.expander(
            "⚠️ Scan / Telegram errors",
            expanded=False
        ):
            for err in live_errors:
                st.write(
                    f"- {err}"
                )


# ==========================================
# 2. THE WARLORD BACKTEST MATRIX
# ==========================================
st.markdown("---")

st.subheader(
    "📊 4-YEAR BACKTEST: "
    "BENDER OVERRIDE "
    "(0.5% Fee Imposed)"
)

with st.expander(
    "Tignan ang 4-Year Lab Report "
    "& Drawdown Graphs",
    expanded=False
):
    fig, axes = plt.subplots(
        2,
        2,
        figsize=(16, 10)
    )

    axes = np.asarray(
        axes
    ).flatten()

    fig.suptitle(
        "E.S.V.E Engine vs Buy & Hold",
        fontsize=16,
        fontweight="bold"
    )

    fig_dd, axes_dd = plt.subplots(
        2,
        2,
        figsize=(16, 6)
    )

    axes_dd = np.asarray(
        axes_dd
    ).flatten()

    fig_dd.suptitle(
        "Underwater Drawdown "
        "(Bender Ejection Status)",
        fontsize=16,
        fontweight="bold"
    )

    bt_results = []
    bt_errors = []
    plot_index = 0

    for ticker in BACKTEST_TICKERS:
        try:
            df = download_data(
                ticker
            )

            if (
                df.empty
                or len(df) < 500
            ):
                continue

            df = engineer_eth_hydrodynamics(
                df
            )

            buy_cond = (
                (df["HPFO_Z"] > 1.65)
                & (df["Reynolds"] > 0.9)
                & (
                    df["Velocity"]
                    > FRICTION_BARRIER
                )
            )

            sell_cond = (
                (df["Velocity"] < 0)
                | (df["HPFO_Z"] < 0)
            )

            df["Raw_Signal"] = np.where(
                buy_cond,
                1.0,
                np.where(
                    sell_cond,
                    0.0,
                    np.nan
                )
            )

            df["Raw_Signal"] = (
                df["Raw_Signal"]
                .ffill()
                .fillna(0.0)
            )

            # One-bar shift:
            # signal today -> action next bar
            df["Target_Pos"] = (
                df["Raw_Signal"]
                .shift(1)
                .fillna(0.0)
            )

            closes = (
                df["Close"]
                .astype(float)
                .to_numpy()
            )

            target_pos = (
                df["Target_Pos"]
                .astype(float)
                .to_numpy()
            )

            n = len(df)

            equity = np.ones(
                n,
                dtype=float
            )

            in_pos = False
            entry_equity = 1.0
            trades = []

            for i in range(
                1,
                n
            ):
                if in_pos:
                    equity[i] = (
                        equity[i - 1]
                        * (
                            closes[i]
                            / closes[i - 1]
                        )
                    )
                else:
                    equity[i] = (
                        equity[i - 1]
                    )

                if (
                    not in_pos
                    and target_pos[i] == 1
                ):
                    equity[i] *= (
                        1 - FEE_RATE
                    )

                    entry_equity = equity[i]

                    in_pos = True

                elif (
                    in_pos
                    and target_pos[i] == 0
                ):
                    equity[i] *= (
                        1 - FEE_RATE
                    )

                    in_pos = False

                    trades.append(
                        (
                            equity[i]
                            / entry_equity
                        ) - 1.0
                    )

            # Close remaining open trade
            if in_pos:
                equity[-1] *= (
                    1 - FEE_RATE
                )

                trades.append(
                    (
                        equity[-1]
                        / entry_equity
                    ) - 1.0
                )

            df["Equity"] = equity

            # ==========================================
            # KPIs
            # ==========================================
            algo_roi = (
                equity[-1] - 1.0
            ) * 100

            hodl_roi = (
                (
                    closes[-1]
                    / closes[0]
                ) - 1.0
            ) * 100

            cum_max = np.maximum.accumulate(
                equity
            )

            drawdown = (
                equity
                / cum_max
            ) - 1.0

            max_dd = (
                np.min(drawdown)
                * 100
            )

            bt_results.append({
                "Asset": ticker.replace(
                    "-USD",
                    ""
                ),
                "Raw_ROI": algo_roi,
                "Algo ROI": (
                    f"{algo_roi:.1f}%"
                ),
                "HODL ROI": (
                    f"{hodl_roi:.1f}%"
                ),
                "Max DD": (
                    f"{max_dd:.1f}%"
                ),
                "Trades": len(
                    trades
                )
            })

            # ==========================================
            # CHARTS: first 4 successful assets
            # ==========================================
            if plot_index < 4:
                ax = axes[
                    plot_index
                ]

                ax.plot(
                    df.index,
                    df["Equity"],
                    label="Bender Override",
                    linewidth=2
                )

                ax.plot(
                    df.index,
                    closes / closes[0],
                    label="Buy & Hold",
                    linewidth=1.5,
                    alpha=0.75
                )

                ax.set_title(
                    ticker.replace(
                        "-USD",
                        ""
                    )
                )

                ax.legend(
                    loc="upper left",
                    frameon=False
                )

                ax.grid(
                    True,
                    linestyle="--",
                    alpha=0.4
                )

                ax_dd = axes_dd[
                    plot_index
                ]

                ax_dd.fill_between(
                    df.index,
                    drawdown * 100,
                    0,
                    alpha=0.3
                )

                ax_dd.plot(
                    df.index,
                    drawdown * 100,
                    linewidth=1.2
                )

                ax_dd.set_title(
                    f"{ticker.replace('-USD', '')} "
                    f"Drawdown %"
                )

                ax_dd.grid(
                    True,
                    linestyle="--",
                    alpha=0.4
                )

                plot_index += 1

        except Exception as e:
            bt_errors.append(
                f"{ticker}: "
                f"{type(e).__name__}: {e}"
            )

    # Hide unused chart slots
    for i in range(
        plot_index,
        4
    ):
        axes[i].set_visible(
            False
        )

        axes_dd[i].set_visible(
            False
        )

    fig.tight_layout()
    fig.subplots_adjust(
        top=0.92
    )

    fig_dd.tight_layout()
    fig_dd.subplots_adjust(
        top=0.90
    )

    st.pyplot(
        fig,
        use_container_width=True
    )

    st.pyplot(
        fig_dd,
        use_container_width=True
    )

    plt.close(fig)
    plt.close(fig_dd)

    if bt_results:
        df_report = (
            pd.DataFrame(
                bt_results
            )
            .sort_values(
                by="Raw_ROI",
                ascending=False
            )
            .drop(
                columns=[
                    "Raw_ROI"
                ]
            )
            .reset_index(
                drop=True
            )
        )

        st.dataframe(
            df_report,
            use_container_width=True,
            hide_index=True
        )

    if bt_errors:
        with st.expander(
            "⚠️ Backtest errors",
            expanded=False
        ):
            for err in bt_errors:
                st.write(
                    f"- {err}"
                )
