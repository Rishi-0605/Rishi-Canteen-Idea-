# FORTUNE SECURITIES: Indian Equity Research Agent

A personal research and portfolio-intelligence agent for NSE/BSE-listed companies. It reads your holdings, works
through a company's filings, disclosures and prices, does the arithmetic with every number traced to a source,
keeps a research memory, and tells you what changed since the last report.

**It is not a trading bot.** No module can place an order, and it neither asks for nor stores brokerage or
trading credentials.

## Requirements

Python 3.11 or newer (the config loader uses `tomllib`), plus `pandas`, `openpyxl` and `requests`
(`requirements.txt`). Tested on Python 3.13.

## Quick start (synthetic sample data first)

```bash
cd fortune-securities
python3 -m unittest discover -s tests          # 113 offline tests
python3 scripts/demo_sample.py                 # the whole workflow on fictional data, in a temp folder

python3 -m fortune_research --sample --as-of 2026-10-20 ask "Analyse my portfolio"
python3 -m fortune_research --sample --as-of 2026-10-20 ask "Analyse Sample Manufacturing"
python3 -m fortune_research --sample show SAMPLEMFG --section forensic
```

The sample companies (`SAMPLEMFG`, `SAMPLEPEERA`, ...) are fictional, and every report built from them carries a
SYNTHETIC banner. `--sample` uses its own database (`data/sample/`), so it never mixes with your real research.

## Using it with your own data

1. `cp config/settings.example.toml config/settings.toml` (git-ignored) and edit it.
2. Put broker exports in `data/portfolio/` (git-ignored) and list them under `[portfolio]`. If the import cannot
   find a column, add your broker's header names to `config/column_maps.toml`.
3. `python3 -m fortune_research import-portfolio` validates and reconciles. Resolve what it reports (bonus/split
   not in transactions, cost differences) before relying on P&L.
4. Company data: the NSE/BSE network adapters are disabled by default (see below). Until they are enabled and
   verified, enter figures from filings into `data/manual/` in the layout in [docs/DATA_FORMATS.md](docs/DATA_FORMATS.md),
   with the filing's URL, period and publication date on every row.
5. Set the valuation judgement inputs (`risk_free_rate` with its date and source, `equity_risk_premium`). The DCF
   does not run without them.
6. Use it: `ask "Analyse <name | NSE symbol | BSE code | ISIN>"`, `ask "Analyse my portfolio"`, `ask "What has changed?"`.

In Claude Code, the skills in `../.claude/skills/fortune-*` drive the same commands: `fortune-research` is the
orchestrator, and there is one skill per module.

## Modules

| # | Module | Code | Skill |
| --- | --- | --- | --- |
| 1 | Portfolio reader | `portfolio/reader.py`, `portfolio/reconcile.py` | fortune-portfolio-reader |
| 2 | Stock researcher | `identity.py`, `providers/`, `agent.py` | fortune-stock-researcher |
| 3 | News monitor | `analysis/news.py`, `providers/rss.py` | fortune-news-monitor |
| 4 | Financial analyst | `analysis/financials.py`, `analysis/quality.py` | fortune-financial-analyst |
| 5 | Forensic analyst | `analysis/forensic.py` | fortune-forensic-analyst |
| 6 | Valuation analyst | `analysis/valuation.py` | fortune-valuation-analyst |
| 7 | Technical analyst | `analysis/technical.py` | fortune-technical-analyst |
| 8 | Portfolio analyst | `analysis/portfolio.py` | fortune-portfolio-analyst |
| 9 | Risk analyst | `analysis/risk.py` | fortune-risk-analyst |
| 10 | Research memory | `memory/store.py`, `memory/diff.py` | fortune-research-memory |
| 11 | Report generator | `report/markdown.py`, `report/excel.py` | fortune-report-generator |

Architecture, the review of the reference projects (and what in them is US-only), and the data-source options
with costs and coverage: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Status: what is tested and what is not

| Component | Status |
| --- | --- |
| Portfolio import (CSV/XLSX, aliases, preamble rows), validation, reconciliation | Tested (unit + sample workflow) |
| Financial ratios, growth, TTM, reconciliation checks, staleness | Tested against hand-computed values |
| Forensic, valuation (multiples, peers, DCF, P/B-ROE), technical, risk, news classification | Tested |
| Portfolio weights, concentration, XIRR, benchmark replay, fit | Tested |
| SQLite memory, comparison, invalidation re-tests | Tested (two-stage sample) |
| Markdown + Excel reports with citations | Tested (citations resolve, workbook opens) |
| HTTP client: retries, backoff, cache, source log, redaction | Tested with a fake transport |
| Local-file provider | Tested; this is the working data path today |
| NSE / BSE / Yahoo / RSS adapters | **Parsers tested on hand-written format fixtures only. Not verified against live endpoints**, which the build sandbox blocks. Disabled by default |
| NSE XBRL results parser, annual-report PDF extraction, corporate-action feed | Not built (planned) |

## What needs credentials, infrastructure or manual input

- **Network access** to NSE/BSE/Yahoo hosts. Enable `[providers.nse]` etc. only after reviewing each site's terms,
  then run `python3 -m fortune_research providers --check`.
- **Paid vendor APIs** (optional): add a provider class and name its key's environment variable (`api_key_env`).
  Keys are never stored in files. The config loader refuses inline secrets.
- **Scheduling** (daily news, quarterly re-analysis): cron, or a Claude scheduled task running `ask "What has changed?"`.
- **Manual input**: annual-report governance facts (`governance.json`, with page numbers), sector and peers
  (`company.json`), valuation assumptions, and corporate actions that explain reconciliation breaks.

## Data-integrity rules

Every figure is a `Fact` (value, unit, period, basis, source URL, publisher, official or not, publication date,
retrieval time) or a `Metric` (formula plus the facts it came from). Missing inputs give `n/a`; nothing is
imputed. Units are normalised to INR crore, and unknown units are rejected. Statements are reconciled, stale data
is labelled, and disclosures published after the analysis date are excluded. Unofficial sources (Yahoo, news)
are marked everywhere they appear.

Not investment advice.
