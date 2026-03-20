#!/usr/bin/env python3
"""
fetch_all.py — Market Analyst Skill
Standalone parallel data fetch harness.
Can be run independently or imported by build_report.py.

Usage:
  python scripts/fetch_all.py --type weekly --sections all
"""

import asyncio
import json
import os
import argparse
from datetime import date, datetime


# ── yfinance ─────────────────────────────────────────────────────────────────

async def fetch_yfinance(tickers: list[str], period: str = "5d") -> dict:
    """Fetch OHLCV + metadata from yfinance."""
    try:
        import yfinance as yf
        results = {}
        for ticker in tickers:
            data = yf.download(ticker, period=period, interval="1d", progress=False)
            info = yf.Ticker(ticker).fast_info
            results[ticker] = {
                "ohlcv": data.to_dict() if not data.empty else {},
                "current_price": getattr(info, "last_price", None),
                "week_change_pct": _week_change(data),
            }
        return {"status": "ok", "data": results}
    except Exception as e:
        return {"status": "error", "error": str(e), "data": {}}


def _week_change(df) -> float | None:
    """Calculate week-over-week % change from OHLCV dataframe."""
    try:
        closes = df["Close"].dropna()
        if len(closes) >= 2:
            return round((closes.iloc[-1] / closes.iloc[-5] - 1) * 100, 2)
    except Exception:
        pass
    return None


# ── Alpha Vantage ─────────────────────────────────────────────────────────────

async def fetch_alpha_vantage(
    ticker: str,
    indicators: list[str] | None = None
) -> dict:
    """Fetch RSI, MACD, SMA from Alpha Vantage REST API."""
    if indicators is None:
        indicators = ["RSI", "MACD", "SMA"]
    key = os.environ.get("ALPHA_VANTAGE_KEY", "demo")
    base = "https://www.alphavantage.co/query"

    try:
        import httpx
        results = {}
        async with httpx.AsyncClient(timeout=15) as client:
            for func in indicators:
                params = {
                    "function": func,
                    "symbol": ticker,
                    "interval": "daily",
                    "time_period": 14,
                    "series_type": "close",
                    "apikey": key,
                }
                resp = await client.get(base, params=params)
                results[func] = resp.json()
        return {"status": "ok", "ticker": ticker, "data": results}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Polymarket ────────────────────────────────────────────────────────────────

async def fetch_polymarket(tags: list[str] | None = None, limit: int = 10) -> dict:
    """Fetch top markets by tag from Polymarket Gamma API."""
    if tags is None:
        tags = ["economics", "fed", "geopolitics"]
    try:
        import httpx
        results = []
        async with httpx.AsyncClient(timeout=15) as client:
            for tag in tags:
                url = f"https://gamma-api.polymarket.com/markets?limit={limit}&tag={tag}"
                resp = await client.get(url)
                if resp.status_code == 200:
                    markets = resp.json()
                    for m in markets:
                        results.append({
                            "question": m.get("question", ""),
                            "yes_bid": m.get("bestBid", None),
                            "yes_ask": m.get("bestAsk", None),
                            "volume": m.get("volume", None),
                            "tag": tag,
                        })
        return {"status": "ok", "data": results}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Reddit ────────────────────────────────────────────────────────────────────

async def fetch_reddit_sentiment(
    subreddits: list[str] | None = None,
    limit: int = 25
) -> dict:
    """Fetch hot posts + basic sentiment from finance subreddits."""
    if subreddits is None:
        subreddits = ["wallstreetbets", "stocks", "investing"]
    try:
        import praw
        reddit = praw.Reddit(
            client_id=os.environ["REDDIT_CLIENT_ID"],
            client_secret=os.environ["REDDIT_SECRET"],
            user_agent=os.environ.get("REDDIT_USER_AGENT", "market-analyst/1.0"),
        )
        results = {}
        for sub in subreddits:
            posts = []
            for post in reddit.subreddit(sub).hot(limit=limit):
                posts.append({
                    "title": post.title,
                    "score": post.score,
                    "upvote_ratio": post.upvote_ratio,
                    "url": post.url,
                    "num_comments": post.num_comments,
                })
            results[sub] = {
                "posts": posts,
                "avg_upvote_ratio": round(
                    sum(p["upvote_ratio"] for p in posts) / len(posts), 3
                ) if posts else 0,
            }
        return {"status": "ok", "data": results}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ── Orchestrator ──────────────────────────────────────────────────────────────

SECTION_SOURCE_MAP = {
    "market_overview":   ["yfinance"],
    "breaking_news":     [],  # web search (Claude built-in)
    "technical_signals": ["yfinance", "alpha_vantage"],
    "sector_heatmap":    ["yfinance"],
    "polymarket":        ["polymarket"],
    "reddit_sentiment":  ["reddit"],
    "portfolio_pnl":     ["yfinance"],
    "tomorrow_preview":  [],  # web search (Claude built-in)
}


async def fetch_all(active_sections: list[str]) -> dict:
    """
    Run all relevant fetches concurrently based on active sections.
    Returns a unified data dict; failed fetches return None (non-blocking).
    """
    needed_sources: set[str] = set()
    for sec in active_sections:
        needed_sources.update(SECTION_SOURCE_MAP.get(sec, []))

    tasks: dict[str, asyncio.Task] = {}
    loop = asyncio.get_event_loop()

    if "yfinance" in needed_sources:
        tasks["yfinance"] = loop.create_task(
            fetch_yfinance(["SPY", "QQQ", "^VIX", "ES=F", "NQ=F",
                            "XLE", "XLK", "XLF", "XLV", "AAPL", "TSLA", "NVDA"])
        )

    if "alpha_vantage" in needed_sources:
        tasks["alpha_vantage"] = loop.create_task(
            fetch_alpha_vantage("SPY", ["RSI", "MACD", "SMA"])
        )

    if "polymarket" in needed_sources:
        tasks["polymarket"] = loop.create_task(fetch_polymarket())

    if "reddit" in needed_sources:
        tasks["reddit"] = loop.create_task(fetch_reddit_sentiment())

    results: dict = {}
    for name, task in tasks.items():
        try:
            results[name] = await task
        except Exception as e:
            print(f"[WARN] {name} fetch failed: {e}")
            results[name] = {"status": "error", "error": str(e)}

    return results


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fetch market data for report")
    parser.add_argument(
        "--sections", nargs="+",
        default=["market_overview", "technical_signals", "polymarket", "reddit_sentiment"],
        help="Sections to fetch data for"
    )
    parser.add_argument("--output", default=None, help="Save results to JSON file")
    args = parser.parse_args()

    results = asyncio.run(fetch_all(args.sections))

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        print(f"[OK] Saved to {args.output}")
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2, default=str))
