import math
from datetime import date, timedelta

import numpy as np
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="NSE Swing Trading Assistant", page_icon="📈", layout="wide")

DEFAULT_WATCHLIST = ["CHENNPETRO", "RELIANCE", "TCS", "INFY", "HDFCBANK", "ICICIBANK", "SBIN", "TATAMOTORS", "ITC", "LT"]

st.title("📈 NSE Weekly Swing Trading Assistant")
st.caption("Cash swing trading • Technical setup + position sizing • Signal/calculation only (no broker orders)")

with st.sidebar:
    st.header("Trading settings")
    capital = st.number_input("Trading capital (₹)", min_value=1000, max_value=100000000, value=50000, step=5000)
    risk_pct = st.slider("Maximum planned risk per trade (%)", 0.25, 2.0, 1.0, 0.25)
    rr1 = st.selectbox("Primary reward:risk target", [2.0, 3.0], index=0, format_func=lambda x: f"1:{int(x)}")
    lookback = st.selectbox("Historical data", ["6mo", "1y", "2y", "5y"], index=1)
    volume_multiple = st.slider("Volume confirmation threshold (× 20-day average)", 1.0, 2.5, 1.2, 0.1)
    st.caption("Data source: Yahoo Finance via yfinance. Data may be delayed, incomplete or adjusted. Verify with your broker before trading.")

st.subheader("Watchlist")
watch_text = st.text_input(
    "NSE symbols (comma-separated; without .NS)",
    value=", ".join(DEFAULT_WATCHLIST),
    help="Example: CHENNPETRO, RELIANCE, TCS. The app appends .NS for Yahoo Finance."
)
symbols = list(dict.fromkeys([s.strip().upper().replace(".NS", "") for s in watch_text.split(",") if s.strip()]))

col_a, col_b = st.columns([1, 1])
with col_a:
    selected = st.selectbox("Analyze stock", symbols if symbols else ["CHENNPETRO"])
with col_b:
    st.write("")
    st.write("")
    refresh = st.button("🔄 Refresh market data", type="primary")

@st.cache_data(ttl=900, show_spinner=False)
def fetch_history(symbol: str, period: str) -> pd.DataFrame:
    ticker = yf.Ticker(f"{symbol}.NS")
    df = ticker.history(period=period, interval="1d", auto_adjust=False, actions=False)
    if df is None or df.empty:
        return pd.DataFrame()
    df = df.reset_index()
    # yfinance may name the date column Date or Datetime
    date_col = "Date" if "Date" in df.columns else ("Datetime" if "Datetime" in df.columns else df.columns[0])
    df = df.rename(columns={date_col: "Date"})
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.tz_localize(None)
    for col in ["Open", "High", "Low", "Close", "Volume"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["Date", "High", "Low", "Close"]).sort_values("Date")
    return df

if refresh:
    fetch_history.clear()

def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["EMA20"] = d["Close"].ewm(span=20, adjust=False).mean()
    d["EMA50"] = d["Close"].ewm(span=50, adjust=False).mean()
    d["VolAvg20"] = d["Volume"].rolling(20).mean()
    d["VolRatio"] = d["Volume"] / d["VolAvg20"]
    prev_close = d["Close"].shift(1)
    tr = pd.concat([
        d["High"] - d["Low"],
        (d["High"] - prev_close).abs(),
        (d["Low"] - prev_close).abs()
    ], axis=1).max(axis=1)
    d["ATR14"] = tr.rolling(14).mean()
    d["Support20"] = d["Low"].rolling(20).min()
    d["Resistance20"] = d["High"].rolling(20).max()
    d["Support50"] = d["Low"].rolling(50).min()
    return d

def analyze(df: pd.DataFrame, vol_threshold: float):
    d = add_indicators(df)
    last = d.iloc[-1]
    prev = d.iloc[-2] if len(d) > 1 else last
    bullish_trend = bool(last["Close"] > last["EMA20"] > last["EMA50"])
    ema_reclaim = bool(prev["Close"] <= prev["EMA20"] and last["Close"] > last["EMA20"])
    breakout = bool(last["Close"] > prev["High"] and last["VolRatio"] >= vol_threshold) if pd.notna(last["VolRatio"]) else False
    near_support = bool(last["Close"] > last["Support20"] and last["Close"] <= last["Support20"] * 1.03)
    if bullish_trend and breakout:
        status = "Bullish breakout confirmation"
    elif bullish_trend and (ema_reclaim or near_support):
        status = "Potential pullback setup — wait for confirmation"
    elif bullish_trend:
        status = "Bullish trend — no fresh trigger"
    else:
        status = "No bullish setup / wait"
    return d, status, bullish_trend, breakout

risk_amount = capital * risk_pct / 100
with st.spinner(f"Fetching {selected}.NS historical prices..."):
    history = fetch_history(selected, lookback)

if history.empty:
    st.error(f"No price data returned for {selected}.NS. Check the symbol or try again later.")
    st.info("Examples: CHENNPETRO, RELIANCE, TCS, INFY, SBIN. Symbols must be valid Yahoo Finance NSE tickers.")
    st.stop()

data, status, bullish, breakout = analyze(history, volume_multiple)
last = data.iloc[-1]
last_date = pd.to_datetime(last["Date"]).date()
close = float(last["Close"])
ema20 = float(last["EMA20"]) if pd.notna(last["EMA20"]) else np.nan
ema50 = float(last["EMA50"]) if pd.notna(last["EMA50"]) else np.nan
support = float(last["Support20"]) if pd.notna(last["Support20"]) else np.nan
resistance = float(last["Resistance20"]) if pd.notna(last["Resistance20"]) else np.nan
atr = float(last["ATR14"]) if pd.notna(last["ATR14"]) else np.nan
vol_ratio = float(last["VolRatio"]) if pd.notna(last["VolRatio"]) else np.nan

st.divider()
st.subheader(f"{selected} — technical snapshot")
st.caption(f"Last returned daily bar: {last_date}. This is not guaranteed to be real-time market data.")
m1, m2, m3, m4 = st.columns(4)
m1.metric("Latest close", f"₹{close:,.2f}")
m2.metric("EMA 20", f"₹{ema20:,.2f}" if np.isfinite(ema20) else "N/A")
m3.metric("EMA 50", f"₹{ema50:,.2f}" if np.isfinite(ema50) else "N/A")
m4.metric("Volume / 20D avg", f"{vol_ratio:.2f}×" if np.isfinite(vol_ratio) else "N/A")

if "Bullish breakout" in status:
    st.success(f"Rule-based status: {status}")
elif "Potential" in status or "Bullish trend" in status:
    st.warning(f"Rule-based status: {status}")
else:
    st.info(f"Rule-based status: {status}")
st.caption("Status is a mechanical screen, not a recommendation. Signals can be wrong and may not account for corporate events or market gaps.")

# Chart with close and EMAs
chart = data.set_index("Date")[["Close", "EMA20", "EMA50"]].tail(180)
st.line_chart(chart, height=340)
left, right = st.columns(2)
with left:
    st.markdown("#### Support / resistance estimates")
    st.metric("20-session support estimate", f"₹{support:,.2f}" if np.isfinite(support) else "N/A")
    st.metric("20-session resistance estimate", f"₹{resistance:,.2f}" if np.isfinite(resistance) else "N/A")
    st.caption("Rolling 20-session low/high are rough reference levels, not guaranteed support or resistance.")
with right:
    st.markdown("#### Volatility")
    st.metric("ATR (14 sessions)", f"₹{atr:,.2f}" if np.isfinite(atr) else "N/A")
    st.metric("Planned risk budget", f"₹{risk_amount:,.2f}")
    st.caption("ATR measures recent price range. It is not a prediction of the maximum loss.")

st.divider()
st.subheader("Trade planner")
st.write("Set a hypothetical entry and stop-loss after checking the chart. The app calculates quantity within both your risk budget and available capital.")
p1, p2, p3 = st.columns(3)
with p1:
    entry = st.number_input("Planned entry (₹)", min_value=0.0, value=float(round(close, 2)), step=1.0, format="%.2f")
with p2:
    default_stop = max(0.05, round(min(close * 0.97, support if np.isfinite(support) and support < close else close * 0.97), 2))
    stop = st.number_input("Stop-loss (₹)", min_value=0.05, value=float(default_stop), step=1.0, format="%.2f")
with p3:
    use_atr_stop = st.checkbox("Suggest stop using 1.5 × ATR", value=False)
    if use_atr_stop and np.isfinite(atr) and entry > 0:
        stop = max(0.05, round(entry - 1.5 * atr, 2))
        st.caption(f"Suggested stop: ₹{stop:,.2f}")

if entry > 0 and stop > 0 and stop < entry:
    risk_per_share = entry - stop
    qty_risk = math.floor(risk_amount / risk_per_share)
    qty_capital = math.floor(capital / entry)
    qty = max(0, min(qty_risk, qty_capital))
    target2 = entry + 2 * risk_per_share
    target3 = entry + 3 * risk_per_share
    target_primary = entry + rr1 * risk_per_share
    planned_loss = qty * risk_per_share
    investment = qty * entry
    potential_primary = qty * (target_primary - entry)
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Suggested quantity", f"{qty} shares")
    c2.metric("Capital used", f"₹{investment:,.2f}")
    c3.metric("Planned loss at stop", f"₹{planned_loss:,.2f}")
    c4.metric(f"Potential profit at 1:{int(rr1)}", f"₹{potential_primary:,.2f}")
    st.write(f"**Target 1 (1:2):** ₹{target2:,.2f} · **Target 2 (1:3):** ₹{target3:,.2f}")
    if qty == 0:
        st.warning("Risk per share is too large for your risk budget, or capital is insufficient. Reduce risk per share or skip the trade.")
    if planned_loss > risk_amount + 1e-8:
        st.error("Calculated planned risk exceeds your configured budget. Do not place the trade.")
else:
    st.warning("Entry must be above stop-loss. Enter a valid hypothetical setup to calculate position sizing.")

st.divider()
st.subheader("Weekly review checklist")
check_items = [
    "Weekly trend and market context checked",
    "Daily close confirmed above planned breakout level",
    "Volume compared with 20-session average",
    "Support, stop-loss and targets recorded before entry",
    "Reward-to-risk ratio is at least 1:2",
    "Upcoming results/news and gap risk checked",
    "Position size fits risk budget and available capital",
    "Trade journal updated with outcome and lessons",
]
checks = {}
check_cols = st.columns(2)
for i, item in enumerate(check_items):
    with check_cols[i % 2]:
        checks[item] = st.checkbox(item, key=f"review_{i}")
complete = sum(checks.values())
st.progress(complete / len(check_items), text=f"Weekly review completed: {complete}/{len(check_items)}")

st.subheader("Trade journal")
if "journal" not in st.session_state:
    st.session_state.journal = pd.DataFrame(columns=["Date", "Symbol", "Side", "Entry", "Stop", "Target", "Qty", "Exit", "P&L", "Notes"])
with st.form("journal_form"):
    j1, j2, j3 = st.columns(3)
    with j1:
        jdate = st.date_input("Trade date", value=date.today())
        jsymbol = st.text_input("Symbol", value=selected).upper().strip()
        jside = st.selectbox("Side", ["BUY"])
    with j2:
        jentry = st.number_input("Actual entry (₹)", min_value=0.0, value=float(round(close, 2)), step=1.0)
        jstop = st.number_input("Stop (₹)", min_value=0.0, value=float(round(stop, 2)) if stop > 0 else 0.0, step=1.0)
        jtarget = st.number_input("Target (₹)", min_value=0.0, value=float(round(entry + 2*(entry-stop), 2)) if entry > stop else float(round(close*1.04, 2)), step=1.0)
    with j3:
        jqty = st.number_input("Quantity", min_value=0, value=int(qty) if entry > stop else 0, step=1)
        jexit = st.number_input("Exit price (₹; 0 if open)", min_value=0.0, value=0.0, step=1.0)
        jnotes = st.text_input("Notes")
    submitted = st.form_submit_button("Add journal row")
    if submitted:
        pnl = (jexit - jentry) * jqty if jexit > 0 else np.nan
        new_row = pd.DataFrame([{"Date": str(jdate), "Symbol": jsymbol, "Side": jside, "Entry": jentry, "Stop": jstop, "Target": jtarget, "Qty": int(jqty), "Exit": jexit if jexit > 0 else "", "P&L": pnl, "Notes": jnotes}])
        st.session_state.journal = pd.concat([st.session_state.journal, new_row], ignore_index=True)

if not st.session_state.journal.empty:
    st.dataframe(st.session_state.journal, use_container_width=True, hide_index=True)
    st.download_button("Download trade journal CSV", st.session_state.journal.to_csv(index=False).encode("utf-8"), file_name="nse_trade_journal.csv", mime="text/csv")
else:
    st.info("No journal rows yet. Add a trade above; export the journal regularly because this demo stores it in the current Streamlit session.")

st.divider()
st.markdown("### Data, limitations and risk notice")
st.markdown("""
- **Market data:** Yahoo Finance history through `yfinance`, using NSE symbols with `.NS` suffix. This is convenient for prototyping but is not an exchange-authorized guaranteed real-time feed.
- **Data quality:** Prices may be delayed, missing, adjusted, or unavailable due to rate limits. Check the timestamp and verify prices in your broker terminal before any decision.
- **Signals:** EMA, rolling high/low and volume checks are simple rules. They do not guarantee future returns and do not include all corporate actions, liquidity conditions, circuit limits, or market gaps.
- **Risk:** The ₹500 limit is planned risk only. Gap-downs, slippage, and transaction charges can cause a larger realized loss. Avoid leverage; this app does not place orders.
- **No investment advice:** This is an educational analysis tool. Test it on historical data and paper-trade before using real capital.
""")

st.caption("Version 1.0 • No broker connection • No automated order execution")
