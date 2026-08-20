"""
app.py — MODULE 9: THE BENDER OVERRIDE (E.S.V.E)
Dashboard only. All math lives in hpfo_engine.py, all sending in notifier.py.
"""

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

import hpfo_engine as eng
from notifier import dispatch, format_signal, get_credentials, send_telegram

st.set_page_config(page_title="Bender Override (E.S.V.E)", layout="wide")

st.title("🛢️ MODULE 9: THE BENDER OVERRIDE (E.S.V.E)")
st.caption("Ethereum-Specific Viscosity Engine — Warlord Jed Racho")
st.info(
    "**LOGIC:** Nakatono ang balbula para sa malapot na liquidity ng Ethereum. "
    "7-day velocity trigger, brutal ejection protocol. "
    "Ang signal ay binabasa sa **huling saradong candle**, hindi sa kalahating-luto na bar ngayon."
)

# ----------------------------------------------------------------------
# SIDEBAR
# ----------------------------------------------------------------------
capital_php = st.sidebar.number_input("War Chest (PHP)", value=560_000.0, step=10_000.0)
fee_rate = st.sidebar.number_input("Fee per side", value=0.005, step=0.001, format="%.4f")
alerts_on = st.sidebar.toggle("Telegram alerts", value=False)

token, chat_id = get_credentials()
if token and chat_id:
    st.sidebar.success("Telegram credentials loaded 🔒")
else:
    st.sidebar.warning("Walang credentials. Ilagay sa .streamlit/secrets.toml")

if st.sidebar.button("Send test alert"):
    ok, detail = send_telegram("🤖 Test. Buhay ang bot, gago.")
    (st.sidebar.success if ok else st.sidebar.error)(detail)

if st.sidebar.button("♻️ Clear cache / rescan"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.caption(
    "Ang dashboard ay hindi scheduler. Para sa 8AM alerts kahit patay ang laptop, "
    "GitHub Actions ang tumatakbo sa scan_and_alert.py."
)


# ----------------------------------------------------------------------
# CACHED SCAN — hindi na mag-re-download tuwing gagalaw ka ng widget
# ----------------------------------------------------------------------
@st.cache_data(ttl=900, show_spinner=False)
def cached_scan(capital: float, fee: float):
    return eng.scan_watchlist(capital, fee_rate=fee)


@st.cache_data(ttl=3600, show_spinner=False)
def cached_backtest(ticker: str, fee: float):
    df = eng.download_ohlcv(ticker)
    if len(df) < 500:
        raise ValueError(f"{ticker}: {len(df)} bars only, need 500+")
    return eng.run_backtest(df, fee)


# ----------------------------------------------------------------------
# 1. LIVE SIGNALS
# ----------------------------------------------------------------------
st.subheader("🎯 LIVE HYDRAULIC SIGNALS")

with st.spinner("Scanning slurry pressure..."):
    signals, errors = cached_scan(capital_php, fee_rate)

if not signals:
    st.error("Walang nakuhang data. Tignan ang errors sa baba.")
else:
    rows = []
    for s in signals:
        icon = "🚰" if "BUY" in s["action"] else ("⛔" if "EXIT" in s["action"] else "⏳")
        rows.append({
            "COIN": s["coin"],
            "PRICE ($)": f"${s['live_price']:,.2f}",
            "MA200 ($)": f"${s['ma200']:,.2f}",
            "DIST %": f"{s['dist_pct']:+.2f}%",
            "RSI": round(s["rsi"], 1),
            "HPFO Z": round(s["hpfo_z"], 2),
            "REYNOLDS": round(s["reynolds"], 2),
            "VELOCITY": round(s["velocity"], 4),
            "ACTION 📢": f"{icon} {s['action']}",
            "ALLOCATION": (f"₱{s['allocation_php']:,.0f}" if s["allocation_php"] else "—"),
            "SIGNAL BAR": s["signal_date"],
        })

    def color_coding(val):
        if isinstance(val, str):
            if "🚰" in val:
                return "color: #00ffcc; font-weight: bold;"
            if "⛔" in val:
                return "color: #ff4d4d; font-weight: bold;"
            if "⏳" in val:
                return "color: #ffcc00;"
        return ""

    st.dataframe(pd.DataFrame(rows).style.map(color_coding), use_container_width=True)

if errors:
    with st.expander(f"⚠️ {len(errors)} ticker(s) failed — ito ang dahilan"):
        for t, msg in errors:
            st.write(f"**{t}** — {msg}")

# Manual dispatch. Deliberately NOT automatic: ang Streamlit ay nag-rerun
# tuwing may pipindutin ka, at ang auto-send ay katumbas ng spam sa cellphone mo.
if signals:
    col_a, col_b = st.columns([1, 3])
    with col_a:
        if st.button("📤 Push signals to Telegram", disabled=not alerts_on):
            for line in dispatch(signals, errors, heartbeat=True):
                st.write(line)
    with col_b:
        if not alerts_on:
            st.caption("I-on muna ang Telegram alerts sa sidebar.")

    with st.expander("👀 Preview ng mensahe"):
        st.code(format_signal(signals[0]), language="html")


# ----------------------------------------------------------------------
# 2. BACKTEST MATRIX
# ----------------------------------------------------------------------
st.markdown("---")
st.subheader("📊 4-YEAR BACKTEST (fees on both sides, next-bar execution)")

with st.expander("Buksan ang lab report", expanded=False):
    plt.style.use("dark_background")

    results, bt_errors = [], []
    plot_data = []

    prog = st.progress(0.0)
    for i, ticker in enumerate(eng.BACKTEST_TICKERS):
        try:
            bt = cached_backtest(ticker, fee_rate)
            name = ticker.replace("-USD", "")
            results.append({
                "Asset": name,
                "_roi": bt["algo_roi"],
                "Algo ROI": f"{bt['algo_roi']:.1f}%",
                "HODL ROI": f"{bt['hodl_roi']:.1f}%",
                "Max DD": f"{bt['max_dd']:.1f}%",
                "Sharpe (all days)": f"{bt['sharpe_all']:.2f}",
                "Sharpe (in-pos)": f"{bt['sharpe_in_pos']:.2f}",
                "Win Rate": f"{bt['win_rate']:.1f}%",
                "Profit Fctr": ("∞" if bt["profit_factor"] == float("inf")
                                else f"{bt['profit_factor']:.2f}"),
                "Avg Win": f"+{bt['avg_win']:.1f}%",
                "Avg Loss": f"{bt['avg_loss']:.1f}%",
                "Trades": bt["total_trades"],
                "Exposure": f"{bt['exposure_pct']:.1f}%",
            })
            plot_data.append((name, bt))
        except Exception as exc:
            bt_errors.append((ticker, f"{type(exc).__name__}: {exc}"))
        prog.progress((i + 1) / len(eng.BACKTEST_TICKERS))
    prog.empty()

    if plot_data:
        top = plot_data[:4]

        fig, axes = plt.subplots(2, 2, figsize=(16, 10))
        fig.suptitle("E.S.V.E Engine vs Buy & Hold", fontsize=16, fontweight="bold", color="white")
        axes = axes.flatten()

        fig_dd, axes_dd = plt.subplots(2, 2, figsize=(16, 7))
        fig_dd.suptitle("🌊 UNDERWATER DRAWDOWN", fontsize=16, fontweight="bold", color="#ff4d4d")
        axes_dd = axes_dd.flatten()

        for idx, (name, bt) in enumerate(top):
            eq = bt["equity"]
            closes = bt["closes"]
            index = bt["index"]

            ax = axes[idx]
            ax.plot(index, eq, label="Bender Override", color="#ffcc00", linewidth=2)
            ax.plot(index, closes / closes[0], label="Buy & Hold", color="#777777",
                    linewidth=1.5, alpha=0.8)
            ax.fill_between(index, eq.min(), eq.max(),
                            where=(bt["target_pos"].to_numpy() == 1),
                            color="#ffcc00", alpha=0.10)
            ax.set_title(name, fontsize=12, fontweight="bold", color="white")
            ax.legend(loc="upper left", frameon=False, labelcolor="white")
            ax.grid(True, color="#333333", linestyle="--", alpha=0.5)
            ax.spines["top"].set_visible(False)
            ax.spines["right"].set_visible(False)

            axd = axes_dd[idx]
            dd_pct = bt["drawdown"] * 100          # <-- ang sikat na `drawdown100` bug
            axd.fill_between(index, dd_pct, 0, color="#ff4d4d", alpha=0.3)
            axd.plot(index, dd_pct, color="#ff4d4d", linewidth=1.2)
            axd.set_title(f"{name} Drawdown %", fontsize=11, color="white")
            axd.grid(True, color="#333333", linestyle="--", alpha=0.5)
            axd.spines["top"].set_visible(False)
            axd.spines["right"].set_visible(False)

        for j in range(len(top), 4):
            axes[j].axis("off")
            axes_dd[j].axis("off")

        fig.tight_layout(); fig.subplots_adjust(top=0.92)
        fig_dd.tight_layout(); fig_dd.subplots_adjust(top=0.88)

        st.pyplot(fig)
        st.pyplot(fig_dd)
        plt.close(fig); plt.close(fig_dd)   # kung hindi mo isasara, lalamon ng RAM

    if results:
        st.markdown("### 🏆 THE BENDER LAB REPORT")
        rep = (pd.DataFrame(results)
               .sort_values("_roi", ascending=False)
               .drop(columns=["_roi"])
               .reset_index(drop=True))
        st.dataframe(rep, use_container_width=True)

    if bt_errors:
        st.warning("Backtest failures: " + "; ".join(f"{t} ({m})" for t, m in bt_errors))

    st.caption(
        "Basahin ang **Exposure** bago ang ROI. Mababang exposure + mataas na "
        "Sharpe (all days) = artifact ng mga flat na araw, hindi skill. "
        "Ang parameters (1.65 / 0.9 / 7-day) ay tinuno sa ETH sa loob ng "
        "nakalipas na 4 na taon — walang out-of-sample test dito."
    )
