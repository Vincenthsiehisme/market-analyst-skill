---
name: market-analyst
description: >
  Automated market analysis report generation system. Use this skill whenever the user
  requests stock market reports, financial analysis, pre-market or post-market summaries,
  weekly/monthly market reviews, or any structured financial report generation workflow.
  Also triggers on phrases like "幫我出報告", "盤前日報", "盤後分析", "週報", "月報",
  portfolio analysis, or any request to generate a market analyst report with data fetching
  and PDF output. Always use this skill when the user wants to create, automate, or run
  any part of the market analyst report pipeline — even if they only mention one step like
  "fetch yfinance data" or "build a report template".
---

# Market Analyst Skill — Workflow Architecture v1.0

A 7-step automated pipeline for generating localized (Traditional/Simplified Chinese) financial
market reports with multi-source data fetching, technical indicators, and PDF distribution.

---

## Step 1 — Trigger

Identify the **report type** from the user's natural language command.

| Report Type | 中文 | Schedule | Data Scope |
|-------------|------|----------|------------|
| Pre-market  | 盤前日報 | ET 8:00 | Overnight news, futures, pre-market movers |
| Post-market | 盤後日報 | ET 17:00 | Day's price action, volume, intraday events |
| Weekly      | 週報 | Fri close | Weekly performance, sector rotation, macro |
| Monthly     | 月報 | Month-end | Monthly returns, portfolio attribution, themes |

**Input modes:**
- `minimal` — just report type, use defaults for everything else
- `contextual` — report type + optional date/tickers
- `detailed` — full specification including custom sections

---

## Step 2 — Portfolio Gate

Before generating, determine report **mode**:

| Mode | Condition | Behavior |
|------|-----------|----------|
| MODE A — With portfolio | User provides ticker, shares, cost basis, trade history | Include Portfolio P&L (Section 7), personalized analysis |
| MODE B — Without portfolio | No personal data provided | Skip Section 7, generate public/generic version |

> Always ask the user: "Do you want to include personal portfolio data?" if not explicitly stated.

---

## Step 3 — Parallel Data Fetch

Fetch from **6 sources concurrently**. Document which sources are available in the current environment.

| Source | Data | Method | Cost |
|--------|------|--------|------|
| **Financial Datasets** | Fundamentals, SEC filings, insider trades, institutional holdings | MCP | Paid |
| **yfinance** | Index prices, sector ETFs, VIX, futures | Python `yfinance` | Free |
| **Alpha Vantage** | RSI, MACD, SMA, technical indicators | REST API (key required) | Freemium |
| **Polymarket** | Geopolitical odds, Fed rate bets | Web scrape / API | Free |
| **Reddit** | WSB, r/stocks, r/investing sentiment | Python `praw` | Free |
| **Web search** | Breaking news, econ calendar, geopolitics | Built-in search tool | Built-in |

**Implementation notes:**
- Run fetches in parallel using `asyncio` or `concurrent.futures`
- Cache results to avoid re-fetching on retry
- If a source fails, log the error and continue — do not block report generation
- See `references/data-sources.md` for API setup and fallback strategies

---

## Step 4 — Processing Pipeline

Four sequential stages after data fetch:

```
1. Integrate  →  2. Indicators  →  3. Charts  →  4. Template
```

| Stage | Description | Libraries |
|-------|-------------|-----------|
| **1 Integrate** | Merge all fetched data into a unified dataframe; resolve ticker conflicts; align timestamps | `pandas` |
| **2 Indicators** | Compute derived metrics: RSI, MACD, SMA20/50/200, Bollinger Bands, sector momentum | `pandas-ta` or `ta-lib` |
| **3 Charts** | Generate visual assets: candlestick, sector heatmap, P&L curve, technical overlays | `matplotlib`, `plotly` |
| **4 Template** | Populate report template with data + chart assets | `ReportLab` (PDF) |

**Chart output format:** PNG @ 300dpi, embedded in PDF via ReportLab `ImageReader`.

---

## Step 5 — Report Structure

8 sections, **conditionally included** based on report type and portfolio mode.

| # | Section | Pre | Post | Weekly | Monthly | Portfolio required |
|---|---------|-----|------|--------|---------|-------------------|
| 1 | Market overview | ✅ | ✅ | ✅ | ✅ | No |
| 2 | Breaking news | ✅ | ✅ | ✅ | ✅ | No |
| 3 | Technical signals | ✅ | ✅ | ✅ | ✅ | No |
| 4 | Sector heatmap | ❌ | ✅ | ✅ | ✅ | No |
| 5 | Polymarket | ✅ | ❌ | ✅ | ❌ | No |
| 6 | Reddit sentiment | ❌ | ✅ | ✅ | ❌ | No |
| 7 | Portfolio P&L | ❌ | ✅ | ✅ | ✅ | **Yes (Mode A only)** |
| 8 | Tomorrow preview | ✅ | ✅ | ❌ | ❌ | No |

> Build section inclusion logic as a config dict keyed by `(report_type, mode)`.

---

## Step 6 — Output

Generate **two localized versions** of every report:

| Version | Language | Audience | Priority |
|---------|----------|----------|----------|
| 繁體中文版 | Traditional Chinese | Taiwan + HK | Primary (89% of subscribers) |
| 簡體中文版 | Simplified Chinese | Mainland CN + NA | Secondary (11%) |

**Localization guidelines:**
- Financial terminology must be localized, not just character-converted
  - e.g., 股票 vs 股份, 漲跌幅 vs 涨跌幅, 除權 vs 除权
- Use `opencc` Python library for base conversion, then apply term overrides from `references/term-glossary.md`
- Both versions share the same charts; only text content differs

---

## Step 7 — Distribution

| Channel | Status | Notes |
|---------|--------|-------|
| Email (PDF attachment) | Manual for now | Resend API integration reserved |
| Email API | Reserved | `resend` Python SDK, not yet automated |

**Delivery details:**
- Recipients: catedward.com paid subscribers
- Format: PDF attachment via Resend
- Manual workflow: generate PDF → send via Resend dashboard until API is wired up

**When Resend API is ready**, implement:
```python
import resend
resend.Emails.send({
  "from": "reports@catedward.com",
  "to": subscriber_list,
  "subject": report_subject,
  "attachments": [{"filename": pdf_filename, "content": pdf_base64}]
})
```

---

## Quick Reference — Full Pipeline

```
User command
    ↓
[Step 1] Parse report type (pre/post/weekly/monthly) + input mode
    ↓
[Step 2] Check portfolio data → MODE A or MODE B
    ↓
[Step 3] Parallel fetch: Financial Datasets + yfinance + Alpha Vantage
                       + Polymarket + Reddit + Web search
    ↓
[Step 4] Integrate → Indicators → Charts → Template
    ↓
[Step 5] Build 8 sections (conditional by type + mode)
    ↓
[Step 6] Render 繁體中文版 (primary) + 簡體中文版 (secondary)
    ↓
[Step 7] Distribute via email (PDF attachment)
```

---

## Reference Files

- `references/data-sources.md` — API keys setup, rate limits, fallback strategies for all 6 sources
- `references/term-glossary.md` — Financial terminology 繁↔簡 override table
- `references/report-templates/` — ReportLab template files per report type
- `scripts/fetch_all.py` — Parallel data fetching harness
- `scripts/build_report.py` — End-to-end report generation entry point
