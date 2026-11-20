#!/usr/bin/env python3
"""Preserve daily point-in-time model outputs for genuine forward evaluation."""
import json
from datetime import datetime, timezone
from pathlib import Path

source=Path("data/latest.json")
snapshot=json.loads(source.read_text())
stamp=snapshot.get("updated_at")
if not stamp:
    raise RuntimeError("Snapshot missing updated_at")
day=datetime.fromisoformat(stamp.replace("Z","+00:00")).astimezone(timezone.utc).date().isoformat()
directory=Path("data/history")
directory.mkdir(parents=True,exist_ok=True)
dest=directory/(day+".json")
records=[]
for stock in snapshot.get("stocks",[]):
    records.append({"ticker":stock["ticker"],"as_of":stock.get("as_of"),"price":stock.get("price"),"scores":stock.get("scores"),"opportunity":stock.get("opportunity"),"risk_score":stock.get("risk_score"),"coverage":stock.get("coverage")})
record={"snapshot_date":day,"updated_at":stamp,"source":snapshot.get("source"),"stocks":records,"indices":snapshot.get("indices",[]),"market":snapshot.get("market",{})}
# Do not rewrite an already archived date: it is a historical observation, not a mutable latest view.
if dest.exists():
    print("Existing daily archive preserved:",dest)
else:
    dest.write_text(json.dumps(record,indent=2,allow_nan=False)+"\n")
    print("Archived",len(records),"point-in-time stock scores to",dest)
