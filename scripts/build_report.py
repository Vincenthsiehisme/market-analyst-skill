#!/usr/bin/env python3
"""
build_report.py — Market Analyst Skill
End-to-end report generation entry point.

Usage:
  python build_report.py --type pre --mode A --date 2026-03-18
  python build_report.py --type weekly --mode B
"""

import argparse
import asyncio
from datetime import date
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────

REPORT_TYPES = ["pre", "post", "weekly", "monthly"]

# Sections included per (report_type, mode)
# True = always include, False = skip, "A" = Mode A only
SECTION_MAP = {
    "pre":     [True,  True,  True,  False, True,  False, "A",  True ],
    "post":    [True,  True,  True,  True,  False, True,  "A",  True ],
    "weekly":  [True,  True,  True,  True,  True,  True,  "A",  False],
    "monthly": [True,  True,  True,  True,  False, False, "A",  False],
}

SECTION_NAMES = [
    "market_overview",
    "breaking_news",
    "technical_signals",
    "sector_heatmap",
    "polymarket",
    "reddit_sentiment",
    "portfolio_pnl",
    "tomorrow_preview",
]


def get_active_sections(report_type: str, mode: str) -> list[str]:
    """Return list of section names to include based on report type and mode."""
    rules = SECTION_MAP[report_type]
    active = []
    for section, rule in zip(SECTION_NAMES, rules):
        if rule is True:
            active.append(section)
        elif rule == "A" and mode == "A":
            active.append(section)
    return active


# ── Data Fetch ───────────────────────────────────────────────────────────────

async def fetch_yfinance(tickers: list[str]) -> dict:
    """Fetch price data, VIX, futures from yfinance."""
    import yfinance as yf
    results = {}
    for ticker in tickers:
        data = yf.download(ticker, period="5d", interval="1d", progress=False)
        results[ticker] = data
    return results


async def fetch_alpha_vantage(ticker: str, indicators: list[str]) -> dict:
    """Fetch technical indicators from Alpha Vantage."""
    import os, httpx
    key = os.environ.get("ALPHA_VANTAGE_KEY", "demo")
    results = {}
    for func in indicators:
        url = (
            f"https://www.alphavantage.co/query"
            f"?function={func}&symbol={ticker}&apikey={key}"
        )
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=10)
            results[func] = resp.json()
    return results


async def fetch_polymarket() -> list[dict]:
    """Fetch top economics/geopolitics markets from Polymarket."""
    import httpx
    url = "https://gamma-api.polymarket.com/markets?limit=20&tag=economics"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
        return resp.json()


async def fetch_reddit_sentiment(subreddits: list[str]) -> list[dict]:
    """Fetch top posts from finance subreddits."""
    import os, praw
    reddit = praw.Reddit(
        client_id=os.environ["REDDIT_CLIENT_ID"],
        client_secret=os.environ["REDDIT_SECRET"],
        user_agent=os.environ.get("REDDIT_USER_AGENT", "market-analyst/1.0"),
    )
    posts = []
    for sub in subreddits:
        for post in reddit.subreddit(sub).hot(limit=10):
            posts.append({
                "subreddit": sub,
                "title": post.title,
                "score": post.score,
                "url": post.url,
            })
    return posts


async def fetch_all(active_sections: list[str]) -> dict:
    """Run all relevant fetches concurrently."""
    tasks = {}

    tasks["yfinance"] = fetch_yfinance(["SPY", "QQQ", "^VIX", "ES=F", "NQ=F"])

    if "technical_signals" in active_sections:
        tasks["alpha_vantage"] = fetch_alpha_vantage("SPY", ["RSI", "MACD", "SMA"])

    if "polymarket" in active_sections:
        tasks["polymarket"] = fetch_polymarket()

    if "reddit_sentiment" in active_sections:
        tasks["reddit"] = fetch_reddit_sentiment(
            ["wallstreetbets", "stocks", "investing"]
        )

    results = {}
    for name, coro in tasks.items():
        try:
            results[name] = await coro
        except Exception as e:
            print(f"[WARN] {name} fetch failed: {e}")
            results[name] = None

    return results


# ── Report Assembly ──────────────────────────────────────────────────────────

def build_report(data: dict, active_sections: list[str], report_type: str, mode: str) -> dict:
    """Assemble report content dict from fetched data."""
    report = {"sections": {}, "metadata": {"type": report_type, "mode": mode}}

    for section in active_sections:
        # Placeholder — implement per-section builders
        report["sections"][section] = f"[{section} content — implement builder]"

    return report


def render_pdf(report: dict, lang: str, output_path: Path):
    """Render report to PDF using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph
    from reportlab.lib.styles import getSampleStyleSheet

    doc = SimpleDocTemplate(str(output_path), pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    title = "市場分析報告" if lang == "zh-TW" else "市场分析报告"
    story.append(Paragraph(title, styles["Title"]))

    for section_name, content in report["sections"].items():
        story.append(Paragraph(content, styles["Normal"]))

    doc.build(story)
    print(f"[OK] PDF written: {output_path}")


# ── CLI Entry ────────────────────────────────────────────────────────────────

async def main(args):
    report_type = args.type
    mode = args.mode.upper()
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[1] Report type: {report_type}, Mode: {mode}")

    active_sections = get_active_sections(report_type, mode)
    print(f"[2] Active sections: {active_sections}")

    print("[3] Fetching data...")
    data = await fetch_all(active_sections)

    print("[4] Building report...")
    report = build_report(data, active_sections, report_type, mode)

    print("[5/6] Rendering PDFs...")
    date_str = args.date or str(date.today())
    for lang, suffix in [("zh-TW", "TC"), ("zh-CN", "SC")]:
        path = output_dir / f"report_{report_type}_{date_str}_{suffix}.pdf"
        render_pdf(report, lang, path)

    print("[7] Distribution: Manual — send PDFs via Resend dashboard")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Market Analyst Report Generator")
    parser.add_argument("--type", choices=REPORT_TYPES, required=True)
    parser.add_argument("--mode", choices=["A", "B"], default="B")
    parser.add_argument("--date", default=None, help="Report date YYYY-MM-DD")
    parser.add_argument("--output", default="./output", help="Output directory")
    args = parser.parse_args()
    asyncio.run(main(args))
