# Data Sources Reference

## 1. Financial Datasets (MCP)
- **Data**: Fundamentals, SEC filings, insider trades, institutional holdings
- **Setup**: Requires MCP server connection; configure in Claude tool settings
- **Fallback**: Use SEC EDGAR direct API if MCP unavailable

## 2. yfinance (Python)
```bash
pip install yfinance
```
```python
import yfinance as yf
# Index data
spy = yf.download("SPY", period="5d", interval="1d")
# VIX
vix = yf.download("^VIX", period="1d")
# Futures
es = yf.download("ES=F", period="1d")
```
- **Rate limit**: ~2000 req/hour, no key needed
- **Fallback**: Alpha Vantage TIME_SERIES_DAILY

## 3. Alpha Vantage (REST API)
- **Key**: Set as `ALPHA_VANTAGE_KEY` env var
- **Free tier**: 25 requests/day, 500/month
- **Endpoints used**:
  - `RSI`, `MACD`, `SMA` — technical indicators
  - `TIME_SERIES_DAILY_ADJUSTED` — price fallback
- **Fallback**: Compute indicators manually from yfinance OHLCV data using `pandas-ta`

## 4. Polymarket
- **Method**: Public API `https://gamma-api.polymarket.com/markets`
- **No key needed**
- **Filter**: markets tagged `economics`, `fed`, `geopolitics`
- **Fallback**: Skip Section 5 if unavailable

## 5. Reddit (praw)
```bash
pip install praw
```
- **Subreddits**: `wallstreetbets`, `stocks`, `investing`
- **Credentials**: `REDDIT_CLIENT_ID`, `REDDIT_SECRET`, `REDDIT_USER_AGENT`
- **Method**: Top 25 hot posts, simple upvote-weighted sentiment
- **Fallback**: Skip Section 6 if unavailable

## 6. Web Search
- **Method**: Built-in Claude search tool
- **Queries**: "[date] market news", "Fed calendar", "earnings today"
- **Always available** — primary news source
