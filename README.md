# market-analyst

> Automated market analysis report generation skill for Claude Code.

A 7-step pipeline that fetches multi-source financial data and generates
localized (Traditional/Simplified Chinese) market reports as PDF.

## Features

- **4 report types** — Pre-market 盤前日報, Post-market 盤後日報, Weekly 週報, Monthly 月報
- **6 data sources** — Financial Datasets (MCP), yfinance, Alpha Vantage, Polymarket, Reddit, Web search
- **MODE A / B** — With or without personal portfolio P&L (Section 7)
- **8 conditional sections** — Included based on report type × mode
- **Bilingual output** — 繁體中文版 (primary, 89%) + 簡體中文版 (secondary, 11%)
- **PDF distribution** — ReportLab rendering, Resend API hook for email delivery

## Structure

```
market-analyst/
├── SKILL.md                  # Skill definition — Claude reads this
├── README.md                 # This file
├── references/
│   ├── data-sources.md       # API setup, rate limits, fallbacks for all 6 sources
│   └── term-glossary.md      # 50+ financial terms 繁↔簡 override table
└── scripts/
    └── build_report.py       # End-to-end report generation entry point
```

## Installation (Claude Code)

```bash
# Install from .skill package
claude skill install market-analyst.skill

# Or clone this repo and point Claude Code to the directory
git clone https://github.com/YOUR_USERNAME/market-analyst.git
```

## Usage (Claude Code)

Once installed, trigger naturally in any conversation:

```
盤前日報
幫我出本週週報
Generate post-market report with my portfolio
月報 MODE A
```

## Manual Usage (Python)

```bash
pip install yfinance pandas pandas-ta reportlab praw httpx opencc-python-reimplemented

# Public report (no portfolio)
python scripts/build_report.py --type weekly --mode B

# With portfolio P&L
python scripts/build_report.py --type post --mode A --date 2026-03-18
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ALPHA_VANTAGE_KEY` | For Section 3 | Alpha Vantage API key (free tier: 25 req/day) |
| `REDDIT_CLIENT_ID` | For Section 6 | Reddit app client ID |
| `REDDIT_SECRET` | For Section 6 | Reddit app secret |
| `REDDIT_USER_AGENT` | Optional | Default: `market-analyst/1.0` |
| `RESEND_API_KEY` | For Section 7 dist. | Resend email API (reserved, not yet wired) |

### Getting API Keys

- **Alpha Vantage** — [alphavantage.co](https://www.alphavantage.co/support/#api-key) (free)
- **Reddit** — [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps) → create "script" app
- **Resend** — [resend.com](https://resend.com) (for email distribution)

## Report Sections

| # | Section | Pre | Post | Weekly | Monthly | Portfolio |
|---|---------|:---:|:----:|:------:|:-------:|:---------:|
| 1 | Market overview | ✅ | ✅ | ✅ | ✅ | — |
| 2 | Breaking news | ✅ | ✅ | ✅ | ✅ | — |
| 3 | Technical signals | ✅ | ✅ | ✅ | ✅ | — |
| 4 | Sector heatmap | — | ✅ | ✅ | ✅ | — |
| 5 | Polymarket | ✅ | — | ✅ | — | — |
| 6 | Reddit sentiment | — | ✅ | ✅ | — | — |
| 7 | Portfolio P&L | — | ✅ | ✅ | ✅ | Mode A only |
| 8 | Tomorrow preview | ✅ | ✅ | — | — | — |

## Dependencies

```
yfinance
pandas
pandas-ta
reportlab
praw
httpx
opencc-python-reimplemented
```

## License

MIT
