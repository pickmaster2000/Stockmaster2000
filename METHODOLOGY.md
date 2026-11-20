# StockMaster 2000: methodology and limitations

Daily snapshot is collected through an unofficial Yahoo Finance interface using yfinance. It can fail, lag, change fields, or be rate limited. No paid API is required. GitHub Actions schedule is best effort and may be delayed. The workflow can also be run manually under Actions > Refresh market data > Run workflow.

## Stock universe
A curated list of approximately 100 US-listed tickers in scripts/update_market.py. **Top opportunities means top-ranked within this list, not across the whole market.** The list is not exhaustive and selection introduces bias.

## Scores
All four model scores are 0–100 heuristic weighted combinations of normalized financial ratios. Value uses P/E, price/book, ROE, margins and debt. Growth uses revenue and earnings growth, margins and ROE. Income uses dividend yield, payout ratio, free cash flow and debt. Speculative Growth uses revenue/earnings growth, market cap and margin. Missing inputs receive a neutral 50 in each component; stocks with fewer than 5 of 12 tracked fundamentals are excluded. Scores are NOT validated predictions or recommendations. Risk is an independent heuristic using debt, margins, market cap and payout ratio. Entry score uses the latest close versus 50/200-day averages; if 200 days are unavailable, it is treated conservatively. No look-ahead or backtest is claimed.

## Correction tracker
Uses highest *daily close within the previous 1 year* and latest daily close, which differs from all-time-high or intraday-high definitions. A 10% drawdown from that reference is labeled a correction. Calculated levels are not price targets or predictions. ETF adjusted closing history may reflect dividends/splits; do not compare mechanically with intraday quotes.

## Known gaps
On-demand arbitrary-ticker lookup, VIX/FRED macro data, comprehensive market breadth, sector-relative valuation, portfolio features, automated fundamentals validation, backtesting and full historical audit trail are not yet implemented. Do not rely on this tool for execution decisions. Verify all prices and filings with primary sources.

## Historical technical strategy test (separate from fundamental models)
The `Historical technical backtest` GitHub Action runs `scripts/backtest.py` and writes `data/backtest.json`. It uses approximately five years of adjusted daily closing prices for the CURRENT curated ticker universe. At each month-end close, it selects stocks with close > 50-day average > 200-day average, equally weights them, and measures next-close to next-close returns until the following rebalance. When no stocks qualify, it holds zero-return cash. SPY is the benchmark. The output reports compounded total return, annualized return, maximum drawdown and monthly observations.

**This does not backtest the four fundamental models or the Buying Opportunity score.** Using today's ticker universe creates survivorship/selection bias, and the test omits transaction costs, taxes, slippage and cash interest. The historical signal may overfit, and results are not predictive. A reliable fundamental backtest requires point-in-time financial statements, historical constituents and delisted companies, plus realistic filing/reporting lags.

## Forward test of the actual model
Each successful market-data refresh archives the first score snapshot for that UTC day in `data/history/YYYY-MM-DD.json`. Do not overwrite old observations with revised fundamentals. Once enough forward history has accumulated, subsequent stock returns can be compared to scores and benchmarks without leaking future information. The archive begins when this feature is deployed; it does not reconstruct old scores.
