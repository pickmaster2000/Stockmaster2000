#!/usr/bin/env python3
"""Historical PRICE-ONLY strategy test. Does NOT backtest StockMaster fundamental scores.
Uses historical adjusted daily closes, monthly decisions, next-close execution, no leverage.
Current curated universe creates survivorship/selection bias. Educational research only.
"""
import json
from pathlib import Path
from datetime import datetime,timezone
import pandas as pd
import yfinance as yf
from update_market import SYMBOLS

def closes(ticker):
    try:
        h=yf.Ticker(ticker).history(period="5y",auto_adjust=True)
        if h is None or h.empty:return None
        s=h["Close"].dropna().astype(float)
        s.index=pd.to_datetime(s.index).tz_localize(None).normalize()
        return s[~s.index.duplicated(keep="last")]
    except Exception as exc:
        print("Skipped",ticker,str(exc)[:90]);return None

def test():
    benchmark=closes("SPY")
    if benchmark is None or len(benchmark)<500:raise RuntimeError("SPY history unavailable")
    prices={"SPY":benchmark}
    for ticker in SYMBOLS:
        s=closes(ticker)
        if s is not None and len(s)>=250:prices[ticker]=s
    frame=pd.DataFrame(prices).sort_index()
    # Decisions at month-end close; trade at the following close. Returns are
    # measured from execution close to next execution close, with zero cash yield.
    dates=frame.index
    months=dates.to_series().groupby(dates.to_period("M")).last().tolist()
    decisions=[d for d in months if dates.get_loc(d)>=250]
    observations=[]
    for i in range(len(decisions)-1):
        decision=decisions[i]
        start=dates.get_loc(decision)+1
        next_decision=decisions[i+1]
        end=dates.get_loc(next_decision)+1
        if end>=len(dates):continue
        entry,exit_=dates[start],dates[end]
        selected=[]
        for ticker in SYMBOLS:
            if ticker not in frame:continue
            series=frame[ticker].loc[:decision].dropna()
            if len(series)<200:continue
            p=float(series.iloc[-1]);ma50=float(series.iloc[-50:].mean());ma200=float(series.iloc[-200:].mean())
            if p>ma50>ma200 and pd.notna(frame.at[entry,ticker]) and pd.notna(frame.at[exit_,ticker]):
                selected.append(ticker)
        returns=[float(frame.at[exit_,t]/frame.at[entry,t]-1) for t in selected]
        strategy=sum(returns)/len(returns) if returns else 0.0
        spy=float(frame.at[exit_,"SPY"]/frame.at[entry,"SPY"]-1)
        observations.append({"decision":str(decision.date()),"entry":str(entry.date()),"exit":str(exit_.date()),"holdings":len(selected),"strategy_return_pct":round(strategy*100,3),"spy_return_pct":round(spy*100,3)})
    if len(observations)<12:raise RuntimeError("Insufficient completed test periods")
    def stats(key):
        equity=1.;peak=1.;max_dd=0.;wins=0
        for o in observations:
            r=o[key]/100
            equity*=1+r
            peak=max(peak,equity)
            max_dd=min(max_dd,equity/peak-1)
            wins+=r>0
        years=(pd.Timestamp(observations[-1]["exit"])-pd.Timestamp(observations[0]["entry"])).days/365.25
        return {"total_return_pct":round((equity-1)*100,2),"cagr_pct":round((equity**(1/years)-1)*100,2),"max_drawdown_pct":round(max_dd*100,2),"positive_periods":wins,"periods":len(observations)}
    result={"generated_at":datetime.now(timezone.utc).isoformat(),"test_type":"Historical technical proxy ONLY; not a backtest of current fundamental scores","strategy":"Equal weight all available curated stocks whose close > 50-day MA > 200-day MA at month end; cash if none; next-close execution","benchmark":"SPY adjusted closing prices","assumptions":"No transaction costs, taxes, slippage or cash interest. Current ticker list is retrospectively applied, creating survivorship and selection bias. Daily adjusted close data may be revised.","symbols_requested":len(SYMBOLS),"symbols_with_history":len(prices)-1,"periods":observations,"strategy_stats":stats("strategy_return_pct"),"benchmark_stats":stats("spy_return_pct")}
    Path("data").mkdir(exist_ok=True)
    Path("data/backtest.json").write_text(json.dumps(result,indent=2,allow_nan=False)+"\n")
    print("Backtest complete",result["strategy_stats"],result["benchmark_stats"])
if __name__=="__main__":test()
