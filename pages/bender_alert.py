# ==============================================================================
# MODULE 9: THE BENDER OVERRIDE (E.S.V.E)
# Ethereum-Specific Viscosity Engine
# Cleaned / repaired version with Telegram integration
# ==============================================================================

import os
import warnings
from datetime import datetime

import matplotlib.pyplot as plt
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
    layout="wide",
)

st.title("🛢️ MODULE 9: THE BENDER OVERRIDE (E.S.V.E)")
st.markdown(
    "**Powered by Warlord Jed Racho x Chaotic Genius Engine** | "
    "Ethereum-Specific Viscosity Engine"
)
st.info(
    "💡 **LOGIC:** Ang engine na ito ay gumagamit ng 7-Day Velocity, "
    "Reynolds-style flow metric, HPFO Z pressure score, at brutal exit rule. "
    "Signal dashboard lamang ito; hindi ito automatic trade executor."
)

# ==============================================================================
# CHEAT SHEET
# ==============================================================================
with st.expander("📖 BENDER'S CHEAT SHEET", expanded=True):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### 1. HPFO Z")
        st.caption("Pressure")
        st.write("🌊 **> +1.65:** Strong Buy pressure")
        st.write("💧 **< 0.0:** Exit pressure")

    with col2:
        st.markdown("### 2. REYNOLDS")
        st.caption("Flow")
        st.write("🟢 **> 0.9:** Flow threshold passed")
        st.write("🔴 **< 0.9:** Weak / noisy flow")

    with col3:
        st.markdown("### 3. VELOCITY")
        st.caption("7-Day log-price movement")
        st.write("🚀 **> 0.015:** Positive velocity threshold")
        st.write("💥 **< 0.0:** Emergency exit trigger")

    with col4:
        st.markdown("### 4. THE VALVE")
        st.caption("Action")
        st.write("🚰 **OPEN VALVE:** BUY")
        st.write("⛔ **EMERGENCY EXIT:** SELL / EXIT")
        st.write("⏳ **MAINTAIN PRESSURE:** HOLD")

st.markdown("---")

# ==============================================================================
# CONFIGURATION
# ==============================================================================
WATCHLIST = [
    "BTC-USD",
    "ETH-USD",
    "SOL-USD",
    "ADA-USD",
    "AVAX-USD",
    "XRP-USD",
    "XLM-USD",
    "LINK-USD",
    "DOGE-USD",
    "PEPE-USD",
    "SHIB-USD",
]

BACKTEST_TICKERS = [
    "ETH-USD",
    "BTC-USD",
    "SOL-USD",
    "XLM-USD",
    "XRP-USD",
    "ADA-USD",
]

CAPITAL_PHP = st.sidebar.number_input(
    "War Chest (PHP)",
    min_value=0.0,
    value=560000.0,
    step=10000.0,
)

FEE_RATE = 0.005
FRICTION_BARRIER = FEE_RATE * 3.0

st.sidebar.caption("Telegram alerts: BUY / EXIT only")
st.write(f"⏳ **Live Scan Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# ==============================================================================
# SECRET / CONFIG HELPERS
# ==============================================================================
def get_secret(name: str, default=None):
    """
    Priority:
      1) Streamlit secrets
      2) Environment variables
      3) default
    """
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass

    return os.getenv(name, default)


def telegram_is_configured() -> bool:
    return bool(get_secret("TELEGRAM_BOT_TOKEN")) and bool(
        get_secret("TELEGRAM_CHAT_ID")
    )


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
    comment,
):
    token = get_secret("TELEGRAM_BOT_TOKEN")
    chat_id = get_secret("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        return False, "Telegram secrets are not configured."

    if "BUY" in action:
        emoji = "🌊💸🚀"
        vibe_check = (
            f"GISING! Nagkaroon ng BUY signal sa {coin}. "
            "Suriin muna ang signal bago gumawa ng aktuwal na trade."
        )
    elif "EXIT" in action or "SELL" in action:
        emoji = "🚨📉🛑"
        vibe_check = (
            f"EMERGENCY EXIT signal sa {coin}. "
            "Humina ang flow ayon sa engine."
        )
    else:
        emoji = "🚰🛌"
        vibe_check = f"HOLD muna sa {coin}. Wala pang malinaw na valve action."

    message = (
        f"{emoji} WARLORD QUANT AGENT ALERT {emoji}\n\n"
        f"{vibe_check}\n\n"
        f"📊 Asset: {coin}\n"
        f"💰 Live Price: {price}\n"
        f"📈 HPFO Z (Pressure): {hpfo_z}\n"
        f"🌊 Reynolds (Flow): {reynolds}\n"
        f"🏎️ Velocity (Speed): {velocity}\n"
        f"⚙️ Command: {action}\n"
        f"💼 Allocation: {allocation}\n\n"
        f"💡 Commentary: {comment}\n\n"
        f"⚠️ Signal alert lamang ito. Walang automatic trade na isinasagawa."
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": str(chat_id),
        "text": message,
        "disable_web_page_preview": True,
    }

    try:
        response = requests.post(url, json=payload, timeout=15)
        response.raise_for_status()

        data = response.json()
        if not data.get("ok", False):
            return False, f"Telegram API returned an error: {data}"

        return True, "Telegram alert sent."

    except requests.RequestException as exc:
        return False, f"Telegram request failed: {exc}"
    except ValueError as exc:
        return False, f"Telegram returned invalid JSON: {exc}"


# ==============================================================================
# DATA HELPERS
# ==============================================================================
def normalize_yfinance_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    yfinance can return MultiIndex columns depending on version / ticker count.
    Convert them into simple OHLCV column names.
    """
    if isinstance(df.columns, pd.MultiIndex):
        # For a single ticker, the first level is normally OHLCV.
        if "Close" in df.columns.get_level_values(0):
            df.columns = df.columns.get_level_values(0)
        elif "Close" in df.columns.get_level_values(-1):
            df.columns = df.columns.get_level_values(-1)

    return df


@st.cache_data(ttl=900, show_spinner=False)
def download_market_data(ticker: str, period="4y", interval="1d") -> pd.DataFrame:
    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        progress=False,
        auto_adjust=True,
        threads=False,
    )

    if df is None:
        return pd.DataFrame()

    df = normalize_yfinance_columns(df.copy())

    required = {"Close", "Volume"}
    if not required.issubset(set(df.columns)):
        return pd.DataFrame()

    df = df.dropna(subset=["Close"]).copy()
    return df


# ==============================================================================
# E.S.V.E PHYSICS ENGINE
# ==============================================================================
def engineer_eth_hydrodynamics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    close = pd.to_numeric(df["Close"], errors="coerce")
    volume = pd.to_numeric(df["Volume"], errors="coerce")

    volume = volume.replace(0, np.nan).ffill().fillna(1.0)

    log_close = np.log(close.where(close > 0))
    velocity = log_close.diff(7)

    volume_mean_50 = volume.rolling(50, min_periods=20).mean()
    rho = volume / volume_mean_50
    rho = rho.replace([np.inf, -np.inf], np.nan).fillna(1.0)

    dynamic_pressure = 0.5 * rho * velocity * velocity.abs()

    daily_ret = log_close.diff(1)
    viscosity = daily_ret.rolling(20, min_periods=10).std() * np.sqrt(7)
    viscosity = viscosity.replace(0, np.nan)

    reynolds = velocity.abs() / viscosity

    q_mean = dynamic_pressure.rolling(50, min_periods=20).mean()
    q_std = dynamic_pressure.rolling(50, min_periods=20).std()
    q_std = q_std.replace(0, np.nan)

    hpfo_z = (dynamic_pressure - q_mean) / q_std

    df["Velocity"] = velocity.replace([np.inf, -np.inf], np.nan)
    df["Reynolds"] = reynolds.replace([np.inf, -np.inf], np.nan)
    df["HPFO_Z"] = hpfo_z.replace([np.inf, -np.inf], np.nan)

    return df


def latest_number(series: pd.Series):
    clean = pd.to_numeric(series, errors="coerce").replace(
        [np.inf, -np.inf], np.nan
    ).dropna()

    if clean.empty:
        return None

    return float(clean.iloc[-1])


def classify_signal(hpfo, reynolds, velocity, capital_php):
    if hpfo is None or reynolds is None or velocity is None:
        return (
            "⚠️ INSUFFICIENT DATA",
            "₱0.00",
            "Hindi sapat ang latest indicator data.",
        )

    if hpfo > 1.65 and reynolds > 0.9 and velocity > FRICTION_BARRIER:
        return (
            "🚰 OPEN VALVE (BUY)",
            f"₱{capital_php * 0.25:,.2f} (25%)",
            "Strong pressure + flow + velocity confirmation.",
        )

    if velocity < 0 or hpfo < 0:
        return (
            "⛔ EMERGENCY EXIT",
            "₱0.00",
            "Negative velocity o negative HPFO pressure.",
        )

    return (
        "⏳ MAINTAIN PRESSURE",
        "Hold Status",
        "Wala pang kumpletong BUY o EXIT confirmation.",
    )


# ==============================================================================
# OPTIONAL TELEGRAM TEST
# ==============================================================================
with st.sidebar.expander("📲 Telegram"):
    if telegram_is_configured():
        st.success("Telegram secrets detected.")

        if st.button("Send Test Message"):
            ok, status = send_warlord_telegram_alert(
                coin="SYSTEM TEST",
                price="N/A",
                hpfo_z="N/A",
                reynolds="N/A",
                velocity="N/A",
                action="⏳ MAINTAIN PRESSURE",
                allocation="N/A",
                comment="Telegram connection test lamang.",
            )

            if ok:
                st.success(status)
            else:
                st.error(status)
    else:
        st.warning(
            "Walang TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID. "
            "Ilagay sila sa Streamlit Secrets o environment variables."
        )


# ==============================================================================
# 1. LIVE SIGNAL DASHBOARD
# ==============================================================================
st.subheader("🎯 LIVE HYDRAULIC SIGNALS (Bender Override Status)")

live_results = []
live_errors = []

with st.spinner("🤖 Bender is scanning the matrix for slurry pressure..."):
    for ticker in WATCHLIST:
        try:
            df = download_market_data(ticker, period="4y", interval="1d")

            if df.empty or len(df) < 200:
                live_errors.append(f"{ticker}: kulang o walang market data.")
                continue

            df = engineer_eth_hydrodynamics(df)

            current_price = latest_number(df["Close"])
            if current_price is None:
                live_errors.append(f"{ticker}: walang valid latest price.")
                continue

            ma_200 = df["Close"].rolling(200).mean()
            ma200_val = latest_number(ma_200)
            if ma200_val is None:
                ma200_val = current_price

            dist_pct = (
                ((current_price - ma200_val) / ma200_val) * 100
                if ma200_val != 0
                else np.nan
            )

            delta = df["Close"].diff()
            gain = delta.clip(lower=0).rolling(window=14).mean()
            loss = (-delta.clip(upper=0)).rolling(window=14).mean()
            rs = gain / (loss + 1e-9)
            rsi = 100 - (100 / (1 + rs))
            rsi_val = latest_number(rsi)

            vel = latest_number(df["Velocity"])
            rey = latest_number(df["Reynolds"])
            hpfo = latest_number(df["HPFO_Z"])

            action, allocation, comment = classify_signal(
                hpfo=hpfo,
                reynolds=rey,
                velocity=vel,
                capital_php=CAPITAL_PHP,
            )

            coin_name = ticker.replace("-USD", "")

            # BUY / EXIT alerts only.
            # NOTE: A Streamlit rerun can send the same alert again.
            if "BUY" in action or "EXIT" in action:
                ok, telegram_status = send_warlord_telegram_alert(
                    coin=coin_name,
                    price=f"${current_price:,.2f}",
                    hpfo_z=round(hpfo, 2) if hpfo is not None else "N/A",
                    reynolds=round(rey, 2) if rey is not None else "N/A",
                    velocity=round(vel, 3) if vel is not None else "N/A",
                    action=action,
                    allocation=allocation,
                    comment=comment,
                )

                if not ok and telegram_is_configured():
                    live_errors.append(f"{ticker}: {telegram_status}")

            live_results.append(
                {
                    "COIN": coin_name,
                    "PRICE ($)": f"${current_price:,.2f}",
                    "MA200 ($)": f"${ma200_val:,.2f}",
                    "DIST %": (
                        f"{dist_pct:+.2f}%"
                        if np.isfinite(dist_pct)
                        else "N/A"
                    ),
                    "RSI": round(rsi_val, 1) if rsi_val is not None else "N/A",
                    "HPFO Z": round(hpfo, 2) if hpfo is not None else "N/A",
                    "REYNOLDS": round(rey, 2) if rey is not None else "N/A",
                    "VELOCITY": round(vel, 3) if vel is not None else "N/A",
                    "ACTION 📢": action,
                    "ALLOCATION": allocation,
                    "COMMENTARY 💬": comment,
                }
            )

        except Exception as exc:
            live_errors.append(f"{ticker}: {type(exc).__name__}: {exc}")

if live_results:
    df_live = pd.DataFrame(live_results)

    def color_coding(val):
        if isinstance(val, str):
            if "🚰" in val:
                return "font-weight: bold;"
            if "⛔" in val:
                return "font-weight: bold;"
        return ""

    st.dataframe(
        df_live.style.map(color_coding),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.error("Market Data Unavailable.")

if live_errors:
    with st.expander("⚠️ Scan warnings / errors", expanded=False):
        for err in live_errors:
            st.write(f"- {err}")


# ==============================================================================
# 2. THE WARLORD BACKTEST MATRIX
# ==============================================================================
st.markdown("---")
st.subheader("📊 4-YEAR BACKTEST: BENDER OVERRIDE (0.5% Fee Imposed)")

with st.expander(
    "Tignan ang 4-Year Lab Report & Drawdown Graphs",
    expanded=False,
):
    st.write("🤖 Executing Warlord Physics Simulation...")

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    axes = np.asarray(axes).flatten()
    fig.suptitle(
        "E.S.V.E Engine vs Buy & Hold",
        fontsize=16,
        fontweight="bold",
    )

    fig_dd, axes_dd = plt.subplots(2, 2, figsize=(16, 6))
    axes_dd = np.asarray(axes_dd).flatten()
    fig_dd.suptitle(
        "Underwater Drawdown (Bender Ejection Status)",
        fontsize=16,
        fontweight="bold",
    )

    bt_results = []
    bt_errors = []
    plot_slot = 0

    with st.spinner("Executing Thermodynamic Audits..."):
        for ticker in BACKTEST_TICKERS:
            try:
                df = download_market_data(
                    ticker,
                    period="4y",
                    interval="1d",
                )

                if df.empty or len(df) < 500:
                    bt_errors.append(f"{ticker}: kulang sa 500 observations.")
                    continue

                df = engineer_eth_hydrodynamics(df)

                buy_cond = (
                    (df["HPFO_Z"] > 1.65)
                    & (df["Reynolds"] > 0.9)
                    & (df["Velocity"] > FRICTION_BARRIER)
                )

                sell_cond = (
                    (df["Velocity"] < 0)
                    | (df["HPFO_Z"] < 0)
                )

                df["Raw_Signal"] = np.where(
                    buy_cond,
                    1.0,
                    np.where(sell_cond, 0.0, np.nan),
                )

                df["Raw_Signal"] = (
                    pd.Series(df["Raw_Signal"], index=df.index)
                    .ffill()
                    .fillna(0.0)
                )

                # Shift one bar to reduce look-ahead bias:
                # today's signal is acted on starting next bar.
                df["Target_Pos"] = df["Raw_Signal"].shift(1).fillna(0.0)

                close_series = pd.to_numeric(
                    df["Close"],
                    errors="coerce",
                )

                valid_mask = close_series.notna()
                df = df.loc[valid_mask].copy()
                close_series = close_series.loc[valid_mask]

                closes = close_series.to_numpy(dtype=float)
                target_pos = df["Target_Pos"].to_numpy(dtype=float)
                n = len(df)

                if n < 2:
                    bt_errors.append(f"{ticker}: kulang ang clean data.")
                    continue

                equity = np.ones(n, dtype=float)
                market_exposure = np.zeros(n, dtype=float)
                in_pos = False
                entry_equity = 1.0
                trades = []

                for i in range(1, n):
                    if in_pos:
                        previous_close = closes[i - 1]
                        current_close = closes[i]

                        if previous_close > 0:
                            equity[i] = (
                                equity[i - 1]
                                * (current_close / previous_close)
                            )
                        else:
                            equity[i] = equity[i - 1]

                        market_exposure[i] = 1.0
                    else:
                        equity[i] = equity[i - 1]

                    current_target = target_pos[i]

                    if (not in_pos) and current_target == 1:
                        equity[i] *= (1 - FEE_RATE)
                        entry_equity = equity[i]
                        in_pos = True
                        market_exposure[i] = 1.0

                    elif in_pos and current_target == 0:
                        equity[i] *= (1 - FEE_RATE)
                        in_pos = False
                        market_exposure[i] = 0.0

                        if entry_equity > 0:
                            trades.append(
                                (equity[i] / entry_equity) - 1.0
                            )

                # Close any open position at the end for realized backtest stats.
                if in_pos:
                    equity[-1] *= (1 - FEE_RATE)

                    if entry_equity > 0:
                        trades.append(
                            (equity[-1] / entry_equity) - 1.0
                        )

                df["Equity"] = equity

                # ------------------------------------------------------------------
                # KPIs
                # ------------------------------------------------------------------
                algo_roi = (equity[-1] - 1.0) * 100
                hodl_roi = (
                    (closes[-1] / closes[0] - 1.0) * 100
                    if closes[0] > 0
                    else np.nan
                )

                cum_max = np.maximum.accumulate(equity)
                drawdown = np.divide(
                    equity,
                    cum_max,
                    out=np.ones_like(equity),
                    where=cum_max != 0,
                ) - 1.0

                max_dd = np.min(drawdown) * 100

                strat_returns = (
                    pd.Series(equity)
                    .pct_change()
                    .replace([np.inf, -np.inf], np.nan)
                    .dropna()
                )

                if len(strat_returns) > 1 and strat_returns.std() > 0:
                    sharpe = (
                        strat_returns.mean()
                        / strat_returns.std()
                    ) * np.sqrt(365)
                else:
                    sharpe = 0.0

                trades_array = np.asarray(trades, dtype=float)
                total_trades = len(trades_array)

                if total_trades > 0:
                    wins = trades_array[trades_array > 0]
                    losses = trades_array[trades_array <= 0]

                    win_rate = (len(wins) / total_trades) * 100
                    gross_profit = np.sum(wins)
                    gross_loss = np.abs(np.sum(losses))

                    if gross_loss > 0:
                        profit_factor = gross_profit / gross_loss
                    elif gross_profit > 0:
                        profit_factor = np.inf
                    else:
                        profit_factor = 0.0

                    avg_win = (
                        np.mean(wins) * 100
                        if len(wins) > 0
                        else 0.0
                    )

                    avg_loss = (
                        np.mean(losses) * 100
                        if len(losses) > 0
                        else 0.0
                    )
                else:
                    win_rate = 0.0
                    profit_factor = 0.0
                    avg_win = 0.0
                    avg_loss = 0.0

                exposure = (
                    np.sum(market_exposure) / n
                ) * 100

                bt_results.append(
                    {
                        "Asset": ticker.replace("-USD", ""),
                        "Raw_ROI": algo_roi,
                        "Algo ROI": f"{algo_roi:.1f}%",
                        "HODL ROI": (
                            f"{hodl_roi:.1f}%"
                            if np.isfinite(hodl_roi)
                            else "N/A"
                        ),
                        "Max DD": f"{max_dd:.1f}%",
                        "Sharpe": f"{sharpe:.2f}",
                        "Win Rate": f"{win_rate:.1f}%",
                        "Profit Fctr": (
                            "∞"
                            if np.isinf(profit_factor)
                            else f"{profit_factor:.2f}"
                        ),
                        "Avg Win": f"+{avg_win:.1f}%",
                        "Avg Loss": f"{avg_loss:.1f}%",
                        "Trades": total_trades,
                        "Exposure": f"{exposure:.1f}%",
                    }
                )

                # ------------------------------------------------------------------
                # Plot first 4 successful backtests
                # ------------------------------------------------------------------
                if plot_slot < 4:
                    ax = axes[plot_slot]
                    ax.plot(
                        df.index,
                        df["Equity"],
                        label="Bender Override",
                        linewidth=2,
                    )
                    ax.plot(
                        df.index,
                        closes / closes[0],
                        label="Buy & Hold",
                        linewidth=1.5,
                        alpha=0.8,
                    )
                    ax.set_title(
                        ticker.replace("-USD", ""),
                        fontsize=12,
                        fontweight="bold",
                    )
                    ax.legend(loc="upper left", frameon=False)
                    ax.grid(True, linestyle="--", alpha=0.5)
                    ax.spines["top"].set_visible(False)
                    ax.spines["right"].set_visible(False)

                    ax_dd = axes_dd[plot_slot]
                    ax_dd.fill_between(
                        df.index,
                        drawdown * 100,
                        0,
                        alpha=0.3,
                    )
                    ax_dd.plot(
                        df.index,
                        drawdown * 100,
                        linewidth=1.2,
                    )
                    ax_dd.set_title(
                        f"{ticker.replace('-USD', '')} Drawdown %",
                        fontsize=11,
                    )
                    ax_dd.grid(True, linestyle="--", alpha=0.5)
                    ax_dd.spines["top"].set_visible(False)
                    ax_dd.spines["right"].set_visible(False)

                    plot_slot += 1

            except Exception as exc:
                bt_errors.append(
                    f"{ticker}: {type(exc).__name__}: {exc}"
                )

    # Hide unused axes if fewer than four successful plots.
    for i in range(plot_slot, 4):
        axes[i].set_visible(False)
        axes_dd[i].set_visible(False)

    fig.tight_layout()
    fig.subplots_adjust(top=0.92)

    fig_dd.tight_layout()
    fig_dd.subplots_adjust(top=0.90)

    st.pyplot(fig, use_container_width=True)
    st.pyplot(fig_dd, use_container_width=True)

    plt.close(fig)
    plt.close(fig_dd)

    st.markdown("### 🏆 THE BENDER LAB REPORT")

    if bt_results:
        df_report = pd.DataFrame(bt_results)

        df_report = (
            df_report
            .sort_values(by="Raw_ROI", ascending=False)
            .drop(columns=["Raw_ROI"])
            .reset_index(drop=True)
        )

        st.dataframe(
            df_report,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.warning("Walang sapat na backtest result.")

    if bt_errors:
        with st.expander("⚠️ Backtest warnings / errors", expanded=False):
            for err in bt_errors:
                st.write(f"- {err}")

st.markdown("---")
st.subheader(
    "🍺 BENDER'S FINAL WORD: Signal engine ito, hindi crystal ball. "
    "Sukatin ang performance bago magtiwala ng totoong kapital."
)
