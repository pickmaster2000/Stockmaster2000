#!/usr/bin/env python3
"""Daily, best-effort public market snapshot. No paid API keys."""
import json, math, os, time
from datetime import datetime, timezone
from pathlib import Path
import yfinance as yf
import pandas as pd

SYMBOLS = """AAPL MSFT NVDA AMZN GOOGL META BRK-B AVGO TSLA JPM V UNH XOM MA COST HD PG JNJ ABBV WMT NFLX ORCL CRM AMD ADBE BAC KO PEP CVX MRK CSCO IBM GE CAT MCD DIS TMO ABT TXN QCOM AMGN INTU NOW UBER PLTR PANW CRWD MU LRCX AMAT KLAC ADP SBUX NKE LOW DE GS MS SCHW BLK SPGI ICE CME USB PFE GILD BMY MDT HON UPS RTX LMT NOC BA COP SLB EOG OXY SO DUK NEE AEP ED WM RSG LIN APD SHW ECL TGT CVS C VS PYPL SQ COIN HOOD ROKU SHOP SNOW DDOG NET MDB SOFI RIVN LCID IONQ RKLB ASTS OKLO SMR HIMS CELH CAVA DUOL AFRM""".split()
INDICES={"S&P 500":"^GSPC","Nasdaq Composite":"^IXIC","Dow Jones":"^DJI","Russell 2000":"^RUT","RSP (Equal Weight S&P 500)":"RSP","VTI (Total US Market)":"VTI"}
def number(v):
    try:
        f=float(v)
        return f if math.isfinite(f) else None
    except (ValueError,TypeError): return None
def clamp(v): return max(0,min(100,round(v)))
def grade(v,low,high): return 50 if v is None else clamp(100*(v-low)/(high-low))
def inverse(v,low,high): return 50 if v is None else 100-grade(v,low,high)
def safe_info(t):
    try: return t.info or {}
    except Exception as e:
        print("Info unavailable",t.ticker,str(e)[:120]);return {}
def score(i):
    pe=number(i.get("trailingPE")); forward=number(i.get("forwardPE"))
    pb=number(i.get("priceToBook")); roe=number(i.get("returnOnEquity"))
    margin=number(i.get("profitMargins")); revenue=number(i.get("revenueGrowth"))
    earnings=number(i.get("earningsGrowth")); yield_=number(i.get("dividendYield"))
    payout=number(i.get("payoutRatio")); debt=number(i.get("debtToEquity"))
    cap=number(i.get("marketCap")); fcf=number(i.get("freeCashflow"))
    # Yahoo Finance may return yield as a fraction or in percentage units.
    dividend_rate=number(i.get("dividendRate"))
    current_price=number(i.get("currentPrice"))
    if dividend_rate is not None and current_price and current_price>0:
        yield_=dividend_rate/current_price
    elif yield_ is not None and yield_>=0.10:
        yield_/=100
    if yield_ is not None and not (0<=yield_<=0.25):
        yield_=None
    value=clamp(.35*inverse(forward or pe,8,40)+.20*inverse(pb,1,12)+.20*grade(roe,0,.3)+.15*grade(margin,0,.25)+.10*inverse(debt,0,250))
    growth=clamp(.40*grade(revenue,-.05,.35)+.35*grade(earnings,-.1,.5)+.15*grade(margin,-.05,.25)+.10*grade(roe,0,.3))
    income=clamp(.45*grade(yield_,0,.07)+.30*inverse(payout,0.3,1.2)+.15*grade(fcf,0,10000000000)+.10*inverse(debt,0,250))
    if yield_ is None or yield_<=0: income=0
    elif yield_<.01: income=min(income,30)
    speculative=clamp(.35*grade(revenue,0,.65)+.25*grade(earnings,-.3,.8)+.20*inverse(cap,1e9,50e9)+.20*grade(margin,-.5,.2))
    risk=clamp(.4*grade(debt,0,300)+.25*inverse(margin,-.3,.25)+.2*inverse(cap,5e8,200e9)+.15*grade(payout,.3,1.5))
    coverage=sum(v is not None for v in (pe,forward,pb,roe,margin,revenue,earnings,yield_,payout,debt,cap,fcf))
    return dict(scores=dict(value=value,growth=growth,income=income,speculative=speculative),risk_score=risk,coverage=coverage,metrics=dict(pe=pe,forward_pe=forward,pb=pb,roe=roe,margin=margin,revenue_growth=revenue,earnings_growth=earnings,dividend_yield=yield_,payout=payout,market_cap=cap))
def history(t,period="1y"):
    try:
        h=t.history(period=period,auto_adjust=True)
        return h if h is not None and not h.empty else None
    except Exception as e:
        print("History unavailable",t.ticker,str(e)[:120]);return None
def main():
    out={"mode":"live","updated_at":datetime.now(timezone.utc).isoformat(),"source":"Yahoo Finance via yfinance (unofficial; delayed, missing, or revised data possible)","stocks":[],"indices":[],"market":{}}
    for j,sym in enumerate(SYMBOLS):
        try:
            t=yf.Ticker(sym);i=safe_info(t)
            h=history(t,"6mo")
            if not i or h is None: continue
            q=score(i)
            if q["coverage"]<5: continue
            closes=h["Close"].dropna()
            if closes.empty: continue
            last=number(closes.iloc[-1]);ma50=number(closes.tail(50).mean());ma200=number(closes.tail(200).mean()) if len(closes)>=200 else None
            entry=clamp(50+(15 if ma50 and last>ma50 else -15)+(15 if ma200 and last>ma200 else -10))
            out["stocks"].append(dict(ticker=sym,name=i.get("shortName") or sym,sector=i.get("sector") or "Unknown",price=last,as_of=str(closes.index[-1].date()),scores=q["scores"],risk_score=q["risk_score"],risk=("High" if q["risk_score"]>=65 else "Moderate" if q["risk_score"]>=35 else "Lower"),entry_score=entry,coverage=q["coverage"],metrics=q["metrics"],status="Delayed public feed"))
        except Exception as e: print("Skipped",sym,str(e)[:120])
        if j%20==0: print("Processed",j+1,"of",len(SYMBOLS))
    for name,sym in INDICES.items():
        try:
            h=history(yf.Ticker(sym),"1y")
            if h is None: continue
            c=h["Close"].dropna()
            if c.empty: continue
            peak=number(c.max());last=number(c.iloc[-1])
            out["indices"].append(dict(name=name,ticker=sym,close=last,peak=peak,drawdown_pct=round((last/peak-1)*100,2),levels={str(p):round(peak*(1-p/100),2) for p in (5,10,15,20)},as_of=str(c.index[-1].date()),basis="Highest daily close within past 1 year"))
        except Exception as e: print("Index skipped",sym,str(e)[:120])
    sp=next((i for i in out["indices"] if i["ticker"]=="^GSPC"),None)
    out["market"]={"vix":"Not yet connected","trend":("S&P 500 "+str(sp["drawdown_pct"])+"% from 1y peak") if sp else "Unavailable","entry":"Model-specific scores; not a trade signal"}
    if not out["stocks"] and not out["indices"]: raise RuntimeError("No usable data; refusing to overwrite prior snapshot")
    Path("data").mkdir(exist_ok=True)
    temp=Path("data/latest.json.tmp");temp.write_text(json.dumps(out,indent=2,allow_nan=False));temp.replace("data/latest.json")
    print("Saved",len(out["stocks"]),"stocks and",len(out["indices"]),"indexes")
if __name__=="__main__":main()
