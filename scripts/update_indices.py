#!/usr/bin/env python3
"""Best-effort delayed intraday index quotes, independent of daily stock scores."""
import json
from datetime import datetime, timezone
from pathlib import Path
import yfinance as yf

SYMBOLS = {"S&P 500": "^GSPC", "Nasdaq Composite": "^IXIC", "Dow Jones": "^DJI", "Russell 2000": "^RUT", "RSP (Equal Weight S&P 500)": "RSP", "VTI (Total US Market)": "VTI"}

def main():
    rows = []
    for name, ticker in SYMBOLS.items():
        try:
            h = yf.Ticker(ticker).history(period="5d", interval="5m", auto_adjust=False, prepost=False)
            if h is None or h.empty:
                print("Missing", ticker)
                continue
            close = h["Close"].dropna()
            if close.empty:
                continue
            at = close.index[-1].to_pydatetime()
            if at.tzinfo is None:
                print("Missing timezone", ticker)
                continue
            value = float(close.iloc[-1])
            if not 0 < value < 1000000:
                continue
            rows.append({"name": name, "ticker": ticker, "price": round(value, 4), "as_of": at.astimezone(timezone.utc).isoformat(), "session_date": at.strftime("%Y-%m-%d")})
        except Exception as exc:
            print("Unavailable", ticker, str(exc)[:180])
    if len(rows) < 4 or not any(x["ticker"] == "^GSPC" for x in rows):
        raise RuntimeError("Insufficient intraday data; keeping previous snapshot")
    path = Path("data/index_live.json")
    path.parent.mkdir(exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps({"updated_at": datetime.now(timezone.utc).isoformat(), "source": "Yahoo Finance via yfinance; unofficial, delayed quotes", "indices": rows}, indent=2))
    tmp.replace(path)
    print("Published", len(rows), "index quotes")

if __name__ == "__main__":
    main()
