# ==============================================================================
# BENDER AUTOMATIC SCHEDULED SCANNER
# Runs from GitHub Actions, NOT Streamlit.
#
# 8:10 AM Asia/Manila = Daily Report
# 10:00 PM Asia/Manila = Night Risk Check
# ==============================================================================

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests
import yfinance as yf

MANILA_TZ = ZoneInfo("Asia/Manila")

WATCHLIST = [
    "BTC-USD", "ETH-USD", "SOL-USD", "ADA-USD", "AVAX-USD",
    "XRP-USD", "XLM-USD", "LINK-USD", "DOGE-USD", "PEPE-USD", "SHIB-USD"
]

FEE_RATE = 0.005
FRICTION_BARRIER = FEE_RATE * 3.0
CAPITAL_PHP = float(os.getenv("CAPITAL_PHP", "560000"))

MAX_PER_ASSET_PCT = 25.0
MAX_TOTAL_ALLOCATION_PCT = 100.0


def require_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(
            f"Missing GitHub Actions secret/environment variable: {name}"
        )
    return value.strip()


def normalize_columns(df):
    if isinstance(df.columns, pd.MultiIndex):
        if "Close" in df.columns.get_level_values(0):
            df.columns = df.columns.get_level_values(0)
        elif "Close" in df.columns.get_level_values(-1):
            df.columns = df.columns.get_level_values(-1)
    return df


def download_data(ticker):
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

    df = normalize_columns(df.copy())

    if "Close" not in df.columns or "Volume" not in df.columns:
        return pd.DataFrame()

    return df


def use_completed_candle(df):
    if df.empty:
        return df

    today_utc = datetime.now(timezone.utc).date()
    last_ts = pd.Timestamp(df.index[-1])

    last_date = (
        last_ts.tz_convert("UTC").date()
        if last_ts.tzinfo is not None
        else last_ts.date()
    )

    if last_date >= today_utc and len(df) > 1:
        return df.iloc[:-1].copy()

    return df


def engine(df):
    df = df.copy()

    close = pd.to_numeric(df["Close"], errors="coerce")
    volume = pd.to_numeric(df["Volume"], errors="coerce")
    volume = volume.replace(0, np.nan).ffill().fillna(1.0)

    log_close = np.log(close.where(close > 0))
    velocity = log_close.diff(7)

    rho = volume / volume.rolling(50).mean()
    rho = rho.replace([np.inf, -np.inf], np.nan).fillna(1.0)

    dynamic_pressure = 0.5 * rho * velocity * velocity.abs()

    daily_ret = log_close.diff()
    viscosity = daily_ret.rolling(20).std() * np.sqrt(7)
    viscosity = viscosity.replace(0, np.nan).fillna(1e-8)

    reynolds = velocity.abs() / viscosity

    q_mean = dynamic_pressure.rolling(50).mean()
    q_std = dynamic_pressure.rolling(50).std().replace(0, np.nan).fillna(1e-8)
    hpfo = (dynamic_pressure - q_mean) / q_std

    df["Velocity"] = velocity
    df["Reynolds"] = reynolds
    df["HPFO_Z"] = hpfo

    return df


def latest(series):
    clean = (
        pd.to_numeric(series, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )
    return None if clean.empty else float(clean.iloc[-1])


def classify(hpfo, reynolds, velocity):
    if hpfo is None or reynolds is None or velocity is None:
        return "DATA"

    if hpfo > 1.65 and reynolds > 0.9 and velocity > FRICTION_BARRIER:
        return "BUY"

    if velocity < 0 or hpfo < 0:
        return "EXIT"

    return "HOLD"


def scan_asset(ticker, mode):
    df = download_data(ticker)

    if df.empty or len(df) < 200:
        raise RuntimeError("Insufficient data")

    if mode == "MORNING":
        df = use_completed_candle(df)

    df = engine(df)

    close = pd.to_numeric(df["Close"], errors="coerce")
    price = latest(close)
    hpfo = latest(df["HPFO_Z"])
    reynolds = latest(df["Reynolds"])
    velocity = latest(df["Velocity"])

    return {
        "coin": ticker.replace("-USD", ""),
        "price": price,
        "hpfo": hpfo,
        "reynolds": reynolds,
        "velocity": velocity,
        "signal": classify(hpfo, reynolds, velocity),
        "allocation_pct": 0.0,
        "allocation_php": 0.0,
    }


def allocate(results):
    buys = [r for r in results if r["signal"] == "BUY"]

    if not buys:
        return

    pct = min(
        MAX_PER_ASSET_PCT,
        MAX_TOTAL_ALLOCATION_PCT / len(buys)
    )

    php = CAPITAL_PHP * pct / 100.0

    for row in buys:
        row["allocation_pct"] = pct
        row["allocation_php"] = php


def fmt(value, decimals=2):
    if value is None:
        return "N/A"
    try:
        if not np.isfinite(value):
            return "N/A"
    except TypeError:
        return "N/A"
    return f"{value:.{decimals}f}"


def build_report(results, errors, mode):
    now = datetime.now(MANILA_TZ)

    if mode == "MORNING":
        title = "☀️ BENDER DAILY REPORT — 8:10 AM"
        note = "Completed daily-candle signal"
    elif mode == "NIGHT":
        title = "🌙 BENDER RISK CHECK — 10:00 PM"
        note = "Intraday / partial daily-candle risk check"
    else:
        title = "🧪 BENDER MANUAL GITHUB RUN"
        note = "Manual GitHub Actions test"

    buys = [r for r in results if r["signal"] == "BUY"]
    exits = [r for r in results if r["signal"] == "EXIT"]
    holds = [r for r in results if r["signal"] == "HOLD"]

    lines = [
        title,
        now.strftime("%Y-%m-%d %I:%M %p PHT"),
        note,
        "",
        "🚰 BUY / OPEN VALVE",
    ]

    if buys:
        for r in buys:
            lines.append(
                f"{r['coin']}: HPFO {fmt(r['hpfo'])} | "
                f"Rey {fmt(r['reynolds'])} | "
                f"Vel {fmt(r['velocity'], 3)} | "
                f"₱{r['allocation_php']:,.0f} "
                f"({r['allocation_pct']:.2f}%)"
            )
    else:
        lines.append("None")

    lines += ["", "⛔ EMERGENCY EXIT"]
    lines.append(
        ", ".join(r["coin"] for r in exits)
        if exits else "None"
    )

    lines += ["", "⏳ HOLD / MAINTAIN PRESSURE"]
    lines.append(
        ", ".join(r["coin"] for r in holds)
        if holds else "None"
    )

    total_pct = sum(r["allocation_pct"] for r in buys)
    total_php = sum(r["allocation_php"] for r in buys)

    lines += [
        "",
        "💼 PORTFOLIO",
        f"War Chest: ₱{CAPITAL_PHP:,.0f}",
        f"Planned BUY allocation: ₱{total_php:,.0f} ({total_pct:.2f}%)",
        f"BUY {len(buys)} | HOLD {len(holds)} | EXIT {len(exits)}",
    ]

    if errors:
        lines += ["", "⚠️ DATA WARNINGS", ", ".join(errors)]

    lines += [
        "",
        "⚠️ Experimental signal engine only. No automatic trade execution."
    ]

    return "\n".join(lines)


def telegram_send(text):
    token = require_env("TELEGRAM_BOT_TOKEN")
    chat_id = require_env("TELEGRAM_CHAT_ID")

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    response = requests.post(
        url,
        json={
            "chat_id": chat_id,
            "text": text,
            "disable_web_page_preview": True,
        },
        timeout=20,
    )

    try:
        data = response.json()
    except ValueError:
        data = {}

    if response.status_code != 200:
        raise RuntimeError(
            f"Telegram HTTP {response.status_code}: "
            f"{data.get('description', response.text[:300])}"
        )

    if not data.get("ok", False):
        raise RuntimeError(f"Telegram API error: {data}")


def main():
    mode = os.getenv("SCAN_MODE", "MANUAL").upper()

    results = []
    errors = []

    for ticker in WATCHLIST:
        try:
            results.append(scan_asset(ticker, mode))
        except Exception as exc:
            errors.append(
                f"{ticker.replace('-USD','')}: {type(exc).__name__}"
            )

    if not results:
        raise RuntimeError("No successful market scans.")

    allocate(results)

    report = build_report(results, errors, mode)

    print(report)
    telegram_send(report)
    print("Telegram report sent successfully.")


if __name__ == "__main__":
    main()
