# NSE Weekly Swing Trading Assistant

A Streamlit app for technical screening and cash swing-trade planning across NSE-listed equities. Defaults include CHENNPETRO and common NSE symbols.

## Features
- Automatic historical daily price fetch via Yahoo Finance (`SYMBOL.NS`) using `yfinance`
- 20 EMA, 50 EMA, 20-session rolling support/resistance estimates, ATR(14), and volume ratio
- Simple rule-based status (not a buy/sell recommendation)
- Position sizing constrained by capital and maximum planned risk
- 1:2 and 1:3 target calculations
- Weekly review checklist
- Trade journal with CSV download
- Refreshable cached market data

## Setup (Windows)
1. Install Python 3.10+ from python.org.
2. Extract this ZIP to a folder.
3. Open Command Prompt / PowerShell in the extracted folder.
4. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   If PowerShell blocks activation, use `.\.venv\Scripts\activate.bat` from Command Prompt.

5. Install dependencies:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

6. Run:

   ```powershell
   streamlit run app.py
   ```

7. Open the local URL Streamlit prints (normally `http://localhost:8501`).

## Setup (macOS/Linux)
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Data source notes
- The app uses Yahoo Finance historical data through `yfinance`, with NSE ticker suffix `.NS`.
- This is not a guaranteed real-time or exchange-authorized market data feed. Availability, timestamps, adjustments, and rate limits may vary.
- Verify the current price, liquidity, corporate actions, and order details with your broker before trading.
- If data fetch fails, check ticker spelling, internet access, and try again later.

## Strategy logic (v1)
- Trend: close > EMA20 > EMA50.
- Breakout flag: latest close above previous day's high and volume ratio >= chosen threshold.
- Potential pullback flag: bullish trend plus EMA20 reclaim or close within 3% above rolling 20-session low.
- Support/resistance: rolling 20-session low/high estimates.
- Position size: min(floor(risk budget / (entry - stop)), floor(capital / entry)).
- Default risk budget: 1% of capital (₹500 at ₹50,000).
- Targets: entry + 2R and entry + 3R.

These are educational screening rules, not validated predictive signals. Test and paper-trade before risking money.

## Limitations
- No broker integration, order placement, push alerts, or persistent database.
- Journal is stored in the active Streamlit session; download the CSV regularly.
- Technical levels are approximate. Gaps/slippage/costs can exceed the planned risk budget.
- Does not include a full backtesting engine or corporate-event calendar.
- Historical adjusted/unadjusted data behavior can vary by provider.

## Testing
Run:
```bash
pytest -q
```
