#!/usr/bin/env python3
"""Fail automated refreshes before publishing empty, malformed, or implausible snapshots."""
import json,math,sys
from datetime import datetime,timezone
from pathlib import Path

def check_snapshot(path,minimum=75):
    d=json.loads(Path(path).read_text())
    stamp=datetime.fromisoformat(d["updated_at"].replace("Z","+00:00"))
    if stamp.tzinfo is None:raise ValueError("Timestamp must have timezone")
    age=(datetime.now(timezone.utc)-stamp).total_seconds()
    if not (-600<age<10800):raise ValueError(f"Unexpected snapshot age {age/3600:.1f}h")
    stocks=d.get("stocks",[])
    if len(stocks)<minimum:raise ValueError(f"Only {len(stocks)} stocks; expected at least {minimum}")
    symbols=set()
    for s in stocks:
        ticker=s["ticker"]
        if ticker in symbols:raise ValueError("Duplicate ticker "+ticker)
        symbols.add(ticker)
        price=s.get("price")
        if not isinstance(price,(float,int)) or not math.isfinite(price) or price<=0:raise ValueError("Invalid price "+ticker)
        for key,val in s.get("scores",{}).items():
            if not isinstance(val,(float,int)) or not 0<=val<=100:raise ValueError(f"Invalid {key} score for {ticker}")
        risk=s.get("risk_score")
        if risk is None or not 0<=risk<=100:raise ValueError("Invalid risk for "+ticker)
    indices=d.get("indices",[])
    if len(indices)<4:raise ValueError("Too few indices: "+str(len(indices)))
    vix=d.get("market",{}).get("vix")
    if isinstance(vix,dict) and not (0<float(vix["value"])<150):raise ValueError("Invalid VIX")
    print(f"Validated {len(stocks)} stocks, {len(indices)} indices; VIX: {vix}")
if __name__=="__main__":
    check_snapshot(sys.argv[1] if len(sys.argv)>1 else "data/latest.json")
