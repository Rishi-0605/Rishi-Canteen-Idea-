# FORTUNE SECURITIES: Indian Equity Research Agent

A personal research and portfolio-intelligence agent for NSE/BSE-listed companies. It reads your holdings, works
through a company's filings, disclosures and prices, does the arithmetic with every number traced to a source,
keeps a research memory, and tells you what changed since the last report.

**It is not a trading bot.** No module can place an order, and it neither asks for nor stores brokerage or
trading credentials.

> **Live data status (2026-10-29): not yet verified.** The exchange, Yahoo, news and company-website connectors are
> written and tested on hand-written format fixtures, but every live endpoint was unreachable from the build
> environment (`health --symbol BEL` reported all of them DOWN). Live research is **not production-ready** until
> `health` passes on your network and extracted figures have been checked with `verify`.
> Details: [docs/PROVIDERS.md](docs/PROVIDERS.md).

## Requirements

Python 3.11 or newer (the config loader uses `tomllib`), plus `pandas`, `openpyxl`, `requests`, `pypdf` and,
for tests only, `reportlab` (see `requirements.txt`). Tested on Python 3.13. Network access to the hosts in
docs/PROVIDERS.md is needed for live data.

## 1. Test the installation (offline)

```bash
cd fortune-securities
python3 -m unittest discover -s tests          # 146 offline tests (sample data + format fixtures)
python3 scripts/demo_sample.py                 # full workflow on fictional data, in a temp folder
python3 -m fortune_research --sample health --symbol SAMPLEMFG    # health check on the local sample provider
```

The sample companies (`SAMPLEMFG`, ...) are fictional, and every report built from them carries a SYNTHETIC banner.
`--sample` uses its own database (`data/sample/`).

## 2. Set up live data

```bash
cp config/settings.example.toml config/settings.toml     # git-ignored; edit this copy
```

In `config/settings.toml`:

1. Enable the sources you are allowed to use (read their terms in docs/PROVIDERS.md):
   ```toml
   [providers.nse]
   enabled = true
   [providers.bse]
   enabled = true
   [providers.yahoo]      # unofficial fallback; optional
   enabled = true
   [providers.rss]        # optional
   enabled = true
   feeds = ["https://news.google.com/rss/search?q=%22{query}%22&hl=en-IN&gl=IN&ceid=IN:en"]
   ```
2. Set the valuation judgement inputs. DCF and cost-of-equity methods do not run without them:
   ```toml
   [valuation]
   risk_free_rate = 0.0          # 10Y G-sec yield as a decimal, from RBI DBIE / CCIL
   risk_free_rate_as_of = "YYYY-MM-DD"
   risk_free_rate_source = "URL you read it from"
   equity_risk_premium = 0.0     # your assumption
   ```
3. Check every source with a real retrieval, and save the raw responses as fixtures:
   ```bash
   python3 -m fortune_research health --symbol BEL --capture data/fixtures/live
   ```
   Read the table. **OPERATIONAL** means data came back and suits every listed use. **PARTIAL** means data came
   back but some uses are unsuitable (the reason is printed). **CONNECTED_NO_DATA** means the server answered
   (perhaps HTTP 200) but no usable data came back. **DOWN** means no response. An HTTP 200 is never counted as a
   data retrieval. The report is saved under `data/health/`.

## 3. Research a stock (BEL as the first company)

```bash
python3 -m fortune_research resolve BEL                    # identity: NSE symbol, BSE code, ISIN check digit
python3 -m fortune_research ask "Analyse BEL"              # or: Analyse Bharat Electronics / a BSE code / an ISIN
python3 -m fortune_research show BEL --section quality     # missing, stale, inconsistent data
python3 -m fortune_research show BEL --section sources     # every source with URL, locator, dates
python3 -m fortune_research verify BEL                     # writes a worksheet of every reported figure
#   open each source_url, find the figure at its locator (XBRL element@context or PDF page), fill
#   checked_value / checked_by / checked_on, then:
python3 -m fortune_research verify BEL --record data/verification/BEL_record<N>.csv
python3 -m fortune_research ask "Analyse BEL"              # the report now shows the verification result
```

Company documents (annual reports, results PDFs, investor presentations, call transcripts) can be listed in
`companies/BEL/company.json` under `investor_relations` (fetched when `[providers.ir]` is enabled), or downloaded
yourself into `data/manual/companies/BEL/documents/` with a `documents.json` manifest (docs/DATA_FORMATS.md):

```bash
python3 -m fortune_research documents BEL --find "Revenue from operations"   # page, line, numbers, unit
```

If a live source fails, the affected analysis stops or reports the missing inputs. It never falls back to sample
data. A company that cannot be resolved because the securities masters failed says so (and exits with code 2).

Other commands: `ask "Analyse my portfolio"`, `ask "What has changed?"`, `history BEL`, `sources`, `providers`.

## 4. Your portfolio (when you are ready)

Put broker exports in `data/portfolio/` (git-ignored), list them under `[portfolio]`, then run
`python3 -m fortune_research import-portfolio` and resolve what it reports before `ask "Analyse my portfolio"`.

## What the agent does to keep research honest

- **Every figure is cited**, and the summary's *Key figures and evidence* table marks each one **reported**
  (copied from a filing), **calculated** (formula shown) or **estimate** (model output depending on stated assumptions).
- **Point in time**: figures published after the analysis date are excluded (`--as-of` reproduces a past view).
  A figure with no publication date is assumed public at the SEBI LODR deadline, and the report says so.
  Corporate actions apply only from their ex-date.
- **Splits and bonuses**: unadjusted exchange prices are back-adjusted, and per-share figures from filings
  published before an ex-date are restated. Restatements in later filings win over earlier ones, with a warning.
- **Periods**: quarterly versus 6/9-month year-to-date contexts are kept apart. Non-12-month years and
  non-March year ends are flagged and labelled (`FY2025-Dec`).
- **Missing, stale, inconsistent data** is listed in the data-quality section. The DCF and other methods say
  exactly which input stopped them.
- **Identity**: the ISIN check digit is validated, NSE and BSE codes must map to one ISIN, and a filing that names a
  different company is discarded.

## Modules

| # | Module | Code | Skill |
| --- | --- | --- | --- |
| 1 | Portfolio reader | `portfolio/reader.py`, `portfolio/reconcile.py` | fortune-portfolio-reader |
| 2 | Stock researcher | `identity.py`, `providers/`, `documents.py`, `agent.py` | fortune-stock-researcher |
| 3 | News monitor | `analysis/news.py`, `providers/rss.py` | fortune-news-monitor |
| 4 | Financial analyst | `analysis/financials.py`, `analysis/quality.py`, `providers/xbrl.py` | fortune-financial-analyst |
| 5 | Forensic analyst | `analysis/forensic.py` | fortune-forensic-analyst |
| 6 | Valuation analyst | `analysis/valuation.py` | fortune-valuation-analyst |
| 7 | Technical analyst | `analysis/technical.py`, `analysis/corporate_actions.py` | fortune-technical-analyst |
| 8 | Portfolio analyst | `analysis/portfolio.py` | fortune-portfolio-analyst |
| 9 | Risk analyst | `analysis/risk.py` | fortune-risk-analyst |
| 10 | Research memory | `memory/store.py`, `memory/diff.py`, `verify.py` | fortune-research-memory |
| 11 | Report generator | `report/markdown.py`, `report/excel.py` | fortune-report-generator |
| - | Health check | `health.py` | (see fortune-stock-researcher) |

Architecture and the reference-project review: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).
Provider status, limits and licensing: [docs/PROVIDERS.md](docs/PROVIDERS.md). Input formats: [docs/DATA_FORMATS.md](docs/DATA_FORMATS.md).

## Status

| Component | Status |
| --- | --- |
| Analysis modules, reports, memory, comparison | Tested offline (sample data, hand-computed values) |
| Local files and manually downloaded PDFs | **Operational** (the working data path today) |
| Health check, verification worksheet, raw-response capture | Tested offline; the health check has run live and correctly reported all sources DOWN |
| NSE (master, bhavcopy, results XBRL, announcements, corporate actions, shareholding), BSE (master, announcements), Yahoo, IR websites, news RSS | **Written; parsers tested on hand-written format fixtures; NOT verified live** |
| Shareholding XBRL (pledge, FII/DII), BSE results, OCR, pre-2024 bhavcopy | Not implemented |

Not investment advice.
