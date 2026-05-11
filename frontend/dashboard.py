"""Streamlit Trading Dashboard — connects to the FastAPI backend."""

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
    "**Layer 3/4 Strategy** — Daily change → Liquidity check → "
    "Premium growth → Signal generation"
)

# ── Sidebar ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Controls")
    if st.button("🔄 Run Scan Now", use_container_width=True):
        with st.spinner("Scanning..."):
            result = api_post("/scan")
        if result:
            st.success(f"{result['signals_generated']} signal(s) generated")

    st.divider()
    st.header("Portfolio")
    portfolio = api_get("/portfolio")
    if portfolio:
        st.metric("Balance", f"₹{portfolio['balance']:,.2f}")
        st.metric("P/L", f"₹{portfolio['total_profit_loss']:,.2f}")

# ── Tabs ────────────────────────────────────────────────────────────
tab_signals, tab_stocks, tab_history, tab_charts = st.tabs(
    ["📊 Signals", "📋 Stocks", "📜 Trade History", "📈 Charts"]
)

# ── Signals Tab ─────────────────────────────────────────────────────
with tab_signals:
    st.subheader("Latest Trading Signals")
    signals = api_get("/signals?limit=50")
    if signals:
        df = pd.DataFrame(signals)
        if not df.empty:
            df_display = df[
                ["symbol", "signal", "ltp", "daily_change", "spread",
                 "premium_growth", "confidence", "created_at"]
            ].copy()
            df_display.columns = [
                "Stock", "Signal", "LTP (₹)", "Change %", "Spread %",
                "Premium Growth %", "Confidence", "Time",
            ]

            def color_signal(val: str) -> str:
                if val == "BUY":
                    return "background-color: #27ae60; color: white"
                if val == "SELL":
                    return "background-color: #e74c3c; color: white"
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
                    title="Daily Change by Stock",
                    color_discrete_map={
                        "BUY": "#27ae60",
                        "SELL": "#e74c3c",
                        "HOLD": "#f39c12",
                    },
                )
                st.plotly_chart(fig, use_container_width=True)
            with col2:
                fig = px.scatter(
                    df_display,
                    x="Spread %",
                    y="Premium Growth %",
                    size="Confidence",
                    color="Signal",
                    hover_name="Stock",
                    title="Spread vs Premium Growth",
                    color_discrete_map={
                        "BUY": "#27ae60",
                        "SELL": "#e74c3c",
                        "HOLD": "#f39c12",
                    },
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No signals yet. Click 'Run Scan Now' in the sidebar.")
    else:
        st.info("Could not fetch signals. Is the backend running?")

# ── Stocks Tab ──────────────────────────────────────────────────────
with tab_stocks:
    st.subheader("Tracked Stocks")
    stocks = api_get("/stocks")
    if stocks:
        df_stocks = pd.DataFrame(stocks)
        st.dataframe(df_stocks, use_container_width=True, hide_index=True)
    else:
        st.info("No stocks loaded yet. Run a scan first.")

    st.divider()
    st.subheader("Add a Stock")
    with st.form("add_stock"):
        new_symbol = st.text_input("Symbol (e.g. RELIANCE)")
        new_name = st.text_input("Company Name (optional)")
        submitted = st.form_submit_button("Add")
        if submitted and new_symbol:
            try:
                resp = requests.post(
                    f"{API_URL}/stocks",
                    params={"symbol": new_symbol, "name": new_name or None},
                    timeout=10,
                )
                if resp.status_code == 200:
                    st.success(f"Added {new_symbol.upper()}")
                else:
                    st.warning(resp.json().get("detail", "Error adding stock"))
            except requests.RequestException as exc:
                st.error(f"Error: {exc}")

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
                            title=f"{selected} Option Premium",
                        )
                        st.plotly_chart(fig_prem, use_container_width=True)
                else:
                    st.info("No price data yet for this stock.")
    else:
        st.info("Run a scan first to load stocks.")

# ── Footer ──────────────────────────────────────────────────────────
st.divider()
st.caption("Trading Stock Scanner v1.0 — Demo/Educational Use Only")
