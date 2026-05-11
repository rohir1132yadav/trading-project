"""Streamlit Trading Dashboard — connects to the FastAPI backend.

Stocks are auto-selected by the system. Signals are generated automatically
each morning and displayed here. Users can also trigger a manual scan.
"""

import os

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://backend:8000/api")

st.set_page_config(
    page_title="Trading Stock Scanner",
    page_icon="📈",
    layout="wide",
)


def api_get(endpoint: str):
    try:
        resp = requests.get(f"{API_URL}{endpoint}", timeout=10)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        st.error(f"API error: {exc}")
        return None


def api_post(endpoint: str):
    try:
        resp = requests.post(f"{API_URL}{endpoint}", timeout=30)
        resp.raise_for_status()
        return resp.json()
    except requests.RequestException as exc:
        st.error(f"API error: {exc}")
        return None


# ── Header ──────────────────────────────────────────────────────────
st.title("📈 Trading Stock Scanner")
st.markdown(
    "**Layer 3/4 Strategy** — System auto-selects stocks with >2% daily change "
    "→ Liquidity: (Ask-Bid)/Spot < 40% → ATM premium growth > 4% "
    "→ Trade at Ask price"
)
st.caption(
    "Stocks are auto-selected by the system. "
    "Signals are generated every morning and displayed automatically."
)

# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Controls")
    if st.button("🔄 Run Scan Now", use_container_width=True):
        with st.spinner("Scanning all stocks..."):
            result = api_post("/scan")
        if result:
            st.success(f"{result['signals_generated']} BUY signal(s) generated")

    st.divider()
    st.header("Portfolio")
    portfolio = api_get("/portfolio")
    if portfolio:
        st.metric("Balance", f"₹{portfolio['balance']:,.2f}")
        st.metric("P/L", f"₹{portfolio['total_profit_loss']:,.2f}")

    st.divider()
    st.caption(
        "Scan runs automatically every morning.\n\n"
        "**Pipeline:**\n"
        "1. Fetch all 25 stocks\n"
        "2. Filter: Change > 2%\n"
        "3. Liquidity: (Ask-Bid)/Spot < 40%\n"
        "4. ATM Premium Growth > 4%\n"
        "5. Trade at Ask price"
    )

# ── Tabs ────────────────────────────────────────────────────────────
tab_signals, tab_stocks, tab_history, tab_charts = st.tabs(
    ["📊 Signals", "📋 Auto-Selected Stocks", "📜 Trade History", "📈 Charts"]
)

# ── Signals Tab ─────────────────────────────────────────────────────
with tab_signals:
    st.subheader("Auto-Generated Trading Signals")
    st.caption(
        "Only BUY signals are shown — stocks that passed all filters "
        "(daily change > 2%, liquidity spread < 40%, ATM premium growth > 4%)"
    )
    signals = api_get("/signals?limit=50")
    if signals:
        df = pd.DataFrame(signals)
        if not df.empty:
            display_cols = [
                "symbol", "signal", "ltp", "daily_change", "spread",
                "premium_growth", "confidence", "notes", "created_at",
            ]
            available_cols = [c for c in display_cols if c in df.columns]
            df_display = df[available_cols].copy()

            col_rename = {
                "symbol": "Stock",
                "signal": "Signal",
                "ltp": "Spot (₹)",
                "daily_change": "Change %",
                "spread": "Spread (Ask-Bid)/Spot %",
                "premium_growth": "ATM Premium Growth %",
                "confidence": "Confidence",
                "notes": "Trade Details",
                "created_at": "Generated At",
            }
            df_display.rename(
                columns={k: v for k, v in col_rename.items() if k in df_display.columns},
                inplace=True,
            )

            def color_signal(val: str) -> str:
                if val == "BUY":
                    return "background-color: #27ae60; color: white"
                return "background-color: #f39c12; color: white"

            styled = df_display.style.applymap(
                color_signal, subset=["Signal"]
            )
            st.dataframe(styled, use_container_width=True, hide_index=True)

            col1, col2 = st.columns(2)
            with col1:
                fig = px.bar(
                    df_display,
                    x="Stock",
                    y="Change %",
                    color="Signal",
                    title="Daily Change by Stock (Auto-Selected > 2%)",
                    color_discrete_map={"BUY": "#27ae60"},
                )
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.scatter(
                    df_display,
                    x="Spread (Ask-Bid)/Spot %",
                    y="ATM Premium Growth %",
                    size="Confidence",
                    color="Signal",
                    hover_name="Stock",
                    title="Spread vs ATM Premium Growth",
                    color_discrete_map={"BUY": "#27ae60"},
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info(
                "No signals yet. Signals are generated automatically each morning. "
                "You can also click 'Run Scan Now' in the sidebar."
            )
    else:
        st.info("Could not fetch signals. Is the backend running?")

# ── Stocks Tab ──────────────────────────────────────────────────────
with tab_stocks:
    st.subheader("System Stock Universe (Auto-Selected)")
    st.caption(
        "These 25 stocks are monitored automatically by the system. "
        "Stocks with >2% daily change are filtered for trading signals."
    )
    stocks = api_get("/stocks")
    if stocks:
        df_stocks = pd.DataFrame(stocks)
        st.dataframe(df_stocks, use_container_width=True, hide_index=True)
    else:
        st.info("No stocks loaded yet. Run a scan first.")

# ── Trade History Tab ───────────────────────────────────────────────
with tab_history:
    st.subheader("Trade History")
    trades = api_get("/history")
    if trades:
        df_trades = pd.DataFrame(trades)
        if not df_trades.empty:
            st.dataframe(df_trades, use_container_width=True, hide_index=True)
        else:
            st.info("No trades executed yet.")
    else:
        st.info("Could not fetch trade history.")

# ── Charts Tab ──────────────────────────────────────────────────────
with tab_charts:
    st.subheader("Price Chart")
    stocks_list = api_get("/stocks")
    if stocks_list:
        symbols = [s["symbol"] for s in stocks_list]
        selected = st.selectbox("Select Stock", symbols if symbols else ["RELIANCE"])
        if selected:
            prices = api_get(f"/prices/{selected}?limit=100")
            if prices:
                df_prices = pd.DataFrame(prices)
                if not df_prices.empty:
                    df_prices["recorded_at"] = pd.to_datetime(df_prices["recorded_at"])
                    df_prices = df_prices.sort_values("recorded_at")

                    fig = go.Figure(data=[
                        go.Candlestick(
                            x=df_prices["recorded_at"],
                            open=df_prices["open"],
                            high=df_prices["high"],
                            low=df_prices["low"],
                            close=df_prices["ltp"],
                            name=selected,
                        )
                    ])
                    fig.update_layout(
                        title=f"{selected} Price History",
                        xaxis_title="Time",
                        yaxis_title="Price (₹)",
                    )
                    st.plotly_chart(fig, use_container_width=True)

                    col1, col2 = st.columns(2)
                    with col1:
                        fig_vol = px.bar(
                            df_prices, x="recorded_at", y="volume",
                            title=f"{selected} Volume",
                        )
                        st.plotly_chart(fig_vol, use_container_width=True)
                    with col2:
                        fig_prem = px.line(
                            df_prices, x="recorded_at", y="premium",
                            title=f"{selected} ATM Option Premium",
                        )
                        st.plotly_chart(fig_prem, use_container_width=True)
                else:
                    st.info("No price data yet for this stock.")
    else:
        st.info("Run a scan first to load stocks.")

# ── Footer ──────────────────────────────────────────────────────────
st.divider()
st.caption("Trading Stock Scanner v1.1 — Demo/Educational Use Only")
