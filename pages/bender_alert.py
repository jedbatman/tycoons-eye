# ==============================================================================
# BENDER SCHEDULED MARKET SCANNER
# Runs without Streamlit.
#
# MORNING:
#   8:10 AM Asia/Manila
#   Uses the latest COMPLETED daily candle.
#
# NIGHT:
#   10:00 PM Asia/Manila
#   Uses the current/latest daily data as an intraday risk check.
#
# Telegram:
#   Sends ONE consolidated report per scheduled run.
# ==============================================================================

import os
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests
import yfinance as yf


# ==============================================================================
# CONFIGURATION
# ==============================================================================
MANILA_TZ = ZoneInfo("Asia/Manila")

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

FEE_RATE = 0.005
FRICTION_BARRIER = FEE_RATE * 3.0  # 0.015

# Capital can be overridden with a GitHub Actions environment variable.
CAPITAL_PHP = float(os.getenv("CAPITAL_PHP", "560000"))

# Allocation safeguards:
# - Original Bender rule: max 25% per BUY asset
# - New safeguard: total allocation can never exceed 100% of capital
MAX_PER_ASSET_PCT = 25.0
MAX_TOTAL_ALLOCATION_PCT = 100.0


# ==============================================================================
# HELPERS
# ==============================================================================
def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value.strip()


def get_scan_mode() -> str:
    mode = os.getenv("SCAN_MODE", "MANUAL").strip().upper()

    if mode not in {"MORNING", "NIGHT", "MANUAL"}:
        mode = "MANUAL"

    return mode


def normalize_yfinance_columns(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.columns, pd.MultiIndex):
        if "Close" in df.columns.get_level_values(0):
            df.columns = df.columns.get_level_values(0)
        elif "Close" in df.columns.get_level_values(-1):
            df.columns = df.columns.get_level_values(-1)

    return df


def download_market_data(ticker: str) -> pd.DataFrame:
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

    df = normalize_yfinance_columns(df.copy())

    required = {"Close", "Volume"}
    if not required.issubset(set(df.columns)):
        return pd.DataFrame()

    df = df.dropna(subset=["Close"]).copy()

    return df


def index_date_utc(index_value):
    ts = pd.Timestamp(index_value)

    if ts.tzinfo is None:
        return ts.date()

    return ts.tz_convert("UTC").date()


def use_completed_daily_candle_only(df: pd.DataFrame) -> pd.DataFrame:
    """
    At the morning scan, avoid using a newly-opened partial daily candle.

    If Yahoo Finance already includes a row for the current UTC date,
    drop that row and use the previous completed daily bar.
    """
    if df.empty:
        return df

    today_utc = datetime.now(timezone.utc).date()
    last_row_date = index_date_utc(df.index[-1])

    if last_row_date >= today_utc and len(df) > 1:
        return df.iloc[:-1].copy()

    return df


def engineer_eth_hydrodynamics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    close = pd.to_numeric(df["Close"], errors="coerce")
    volume = pd.to_numeric(df["Volume"], errors="coerce")

    volume = (
        volume
        .replace(0, np.nan)
        .ffill()
        .fillna(1.0)
    )

    log_close = np.log(close.where(close > 0))

    # 7-day log-price velocity
    velocity = log_close.diff(7)

    # Relative volume density
    rho = volume / volume.rolling(50).mean()
    rho = (
        rho
        .replace([np.inf, -np.inf], np.nan)
        .fillna(1.0)
    )

    # Bender-style dynamic pressure
    dynamic_pressure = (
        0.5
        * rho
        * velocity
        * velocity.abs()
    )

    # 20-day volatility / "viscosity"
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

    # Reynolds-style metric
    reynolds = velocity.abs() / viscosity

    # HPFO Z pressure score
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


def latest_valid(series: pd.Series):
    clean = (
        pd.to_numeric(series, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )

    if clean.empty:
        return None

    return float(clean.iloc[-1])


def calculate_rsi(close: pd.Series, window: int = 14):
    delta = close.diff()

    gain = (
        delta
        .clip(lower=0)
        .rolling(window)
        .mean()
    )

    loss = (
        -delta
        .clip(upper=0)
        .rolling(window)
        .mean()
    )

    rs = gain / (loss + 1e-9)

    return 100 - (100 / (1 + rs))


def classify_signal(hpfo, reynolds, velocity):
    if hpfo is None or reynolds is None or velocity is None:
        return "DATA"

    if (
        hpfo > 1.65
        and reynolds > 0.9
        and velocity > FRICTION_BARRIER
    ):
        return "BUY"

    if velocity < 0 or hpfo < 0:
        return "EXIT"

    return "HOLD"


# ==============================================================================
# SCAN
# ==============================================================================
def scan_one_asset(ticker: str, scan_mode: str) -> dict:
    df = download_market_data(ticker)

    if df.empty or len(df) < 200:
        raise RuntimeError("Kulang o walang market data.")

    # Morning report should rely on a fully completed daily candle.
    if scan_mode == "MORNING":
        df = use_completed_daily_candle_only(df)

    if len(df) < 200:
        raise RuntimeError("Kulang ang completed daily data.")

    df = engineer_eth_hydrodynamics(df)

    close = pd.to_numeric(df["Close"], errors="coerce")

    current_price = latest_valid(close)
    hpfo = latest_valid(df["HPFO_Z"])
    reynolds = latest_valid(df["Reynolds"])
    velocity = latest_valid(df["Velocity"])

    ma200 = latest_valid(
        close.rolling(200).mean()
    )

    rsi = latest_valid(
        calculate_rsi(close)
    )

    if current_price is None:
        raise RuntimeError("Walang valid latest price.")

    if ma200 is None:
        ma200 = current_price

    dist_pct = (
        ((current_price - ma200) / ma200) * 100
        if ma200 != 0
        else np.nan
    )

    signal = classify_signal(
        hpfo=hpfo,
        reynolds=reynolds,
        velocity=velocity,
    )

    bar_date = str(pd.Timestamp(df.index[-1]).date())

    return {
        "ticker": ticker,
        "coin": ticker.replace("-USD", ""),
        "price": current_price,
        "ma200": ma200,
        "dist_pct": dist_pct,
        "rsi": rsi,
        "hpfo": hpfo,
        "reynolds": reynolds,
        "velocity": velocity,
        "signal": signal,
        "bar_date": bar_date,
        "allocation_pct": 0.0,
        "allocation_php": 0.0,
    }


def apply_portfolio_allocation(results: list[dict]) -> None:
    """
    Original rule: 25% per BUY.

    Problem:
    5+ simultaneous BUY signals would exceed 100% of the war chest.

    Fix:
    allocation_pct = min(25%, 100% / number_of_BUYs)

    Examples:
      1 BUY  -> 25% allocated
      2 BUYs -> 25% each = 50%
      4 BUYs -> 25% each = 100%
      8 BUYs -> 12.5% each = 100%
    """
    buys = [
        row
        for row in results
        if row["signal"] == "BUY"
    ]

    if not buys:
        return

    allocation_pct = min(
        MAX_PER_ASSET_PCT,
        MAX_TOTAL_ALLOCATION_PCT / len(buys),
    )

    allocation_php = (
        CAPITAL_PHP
        * allocation_pct
        / 100.0
    )

    for row in buys:
        row["allocation_pct"] = allocation_pct
        row["allocation_php"] = allocation_php


# ==============================================================================
# TELEGRAM MESSAGE
# ==============================================================================
def fmt(value, decimals=2, signed=False):
    if value is None:
        return "N/A"

    try:
        if not np.isfinite(value):
            return "N/A"
    except TypeError:
        return "N/A"

    if signed:
        return f"{value:+.{decimals}f}"

    return f"{value:.{decimals}f}"


def build_report(
    results: list[dict],
    errors: list[str],
    scan_mode: str,
) -> str:
    now_manila = datetime.now(MANILA_TZ)

    if scan_mode == "MORNING":
        title = "☀️ BENDER DAILY WARLORD SCAN"
        subtitle = (
            "Completed daily-candle scan "
            "(pangunahing signal ng araw)"
        )
    elif scan_mode == "NIGHT":
        title = "🌙 BENDER NIGHT RISK CHECK"
        subtitle = (
            "Intraday / partial-candle check "
            "(pangalawang risk scan)"
        )
    else:
        title = "🧪 BENDER MANUAL SCAN"
        subtitle = "Manual test run"

    buys = [
        row
        for row in results
        if row["signal"] == "BUY"
    ]

    exits = [
        row
        for row in results
        if row["signal"] == "EXIT"
    ]

    holds = [
        row
        for row in results
        if row["signal"] == "HOLD"
    ]

    data_rows = [
        row
        for row in results
        if row["signal"] == "DATA"
    ]

    lines = [
        title,
        now_manila.strftime("%Y-%m-%d %I:%M %p PHT"),
        subtitle,
        "",
    ]

    # --------------------------------------------------------------------------
    # BUY
    # --------------------------------------------------------------------------
    lines.append("🚰 BUY / OPEN VALVE")

    if buys:
        for row in buys:
            lines.append(
                f"{row['coin']}: "
                f"HPFO {fmt(row['hpfo'])} | "
                f"Rey {fmt(row['reynolds'])} | "
                f"Vel {fmt(row['velocity'], 3)} | "
                f"₱{row['allocation_php']:,.0f} "
                f"({row['allocation_pct']:.2f}%)"
            )
    else:
        lines.append("None")

    # --------------------------------------------------------------------------
    # EXIT
    # --------------------------------------------------------------------------
    lines.extend([
        "",
        "⛔ EMERGENCY EXIT",
    ])

    if exits:
        for row in exits:
            lines.append(
                f"{row['coin']}: "
                f"HPFO {fmt(row['hpfo'])} | "
                f"Rey {fmt(row['reynolds'])} | "
                f"Vel {fmt(row['velocity'], 3)}"
            )
    else:
        lines.append("None")

    # --------------------------------------------------------------------------
    # HOLD
    # --------------------------------------------------------------------------
    lines.extend([
        "",
        "⏳ HOLD / MAINTAIN PRESSURE",
    ])

    if holds:
        lines.append(
            ", ".join(
                row["coin"]
                for row in holds
            )
        )
    else:
        lines.append("None")

    # --------------------------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------------------------
    total_alloc_php = sum(
        row["allocation_php"]
        for row in buys
    )

    total_alloc_pct = sum(
        row["allocation_pct"]
        for row in buys
    )

    lines.extend([
        "",
        "💼 PORTFOLIO SUMMARY",
        f"War Chest: ₱{CAPITAL_PHP:,.0f}",
        (
            f"Planned BUY allocation: "
            f"₱{total_alloc_php:,.0f} "
            f"({total_alloc_pct:.2f}%)"
        ),
        (
            f"BUY {len(buys)} | "
            f"HOLD {len(holds)} | "
            f"EXIT {len(exits)}"
        ),
    ])

    if results:
        dates = sorted(
            set(
                row["bar_date"]
                for row in results
            )
        )

        lines.append(
            "Market bar date(s): "
            + ", ".join(dates)
        )

    if data_rows:
        lines.append(
            f"Insufficient-data assets: "
            f"{', '.join(row['coin'] for row in data_rows)}"
        )

    if errors:
        lines.extend([
            "",
            "⚠️ DATA WARNINGS",
            ", ".join(errors),
        ])

    lines.extend([
        "",
        (
            "⚠️ Experimental signal engine lamang. "
            "Walang automatic trade execution."
        ),
    ])

    return "\n".join(lines)


def send_telegram(message: str) -> None:
    token = require_env(
        "TELEGRAM_BOT_TOKEN"
    )

    chat_id = require_env(
        "TELEGRAM_CHAT_ID"
    )

    url = (
        f"https://api.telegram.org/"
        f"bot{token}/sendMessage"
    )

    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": True,
        },
        timeout=20,
    )

    try:
        data = response.json()
    except ValueError:
        data = {}

    if response.status_code != 200:
        description = data.get(
            "description",
            response.text[:500],
        )

        raise RuntimeError(
            f"Telegram HTTP "
            f"{response.status_code}: "
            f"{description}"
        )

    if not data.get("ok", False):
        raise RuntimeError(
            f"Telegram API error: {data}"
        )


# ==============================================================================
# MAIN
# ==============================================================================
def main():
    scan_mode = get_scan_mode()

    print(
        f"Starting Bender scheduled scan. "
        f"Mode={scan_mode}"
    )

    results = []
    errors = []

    for ticker in WATCHLIST:
        try:
            row = scan_one_asset(
                ticker=ticker,
                scan_mode=scan_mode,
            )

            results.append(row)

            print(
                f"{row['coin']}: "
                f"{row['signal']} | "
                f"HPFO={fmt(row['hpfo'])} | "
                f"REY={fmt(row['reynolds'])} | "
                f"VEL={fmt(row['velocity'], 3)}"
            )

        except Exception as exc:
            coin = ticker.replace(
                "-USD",
                ""
            )

            error_text = (
                f"{coin}: "
                f"{type(exc).__name__}"
            )

            errors.append(
                error_text
            )

            print(
                f"ERROR {ticker}: {exc}",
                file=sys.stderr,
            )

    apply_portfolio_allocation(
        results
    )

    report = build_report(
        results=results,
        errors=errors,
        scan_mode=scan_mode,
    )

    print("\n--- TELEGRAM REPORT ---")
    print(report)
    print("--- END REPORT ---\n")

    # Even if one or two assets fail, send the remaining useful report.
    if not results:
        raise RuntimeError(
            "No market assets were scanned successfully."
        )

    send_telegram(report)

    print(
        "Telegram report sent successfully."
    )


if __name__ == "__main__":
    main()
