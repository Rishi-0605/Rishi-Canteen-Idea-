# FORTUNE SECURITIES Indian Equity Research Agent: Architecture

This is a research and portfolio-intelligence system for NSE/BSE-listed equities.
It reads data, does arithmetic, keeps a record and writes reports. **It does not
place orders, and it does not hold or ask for brokerage or trading credentials.**

## 1. What was taken from the reference projects

Reviewed (October 2026): `Jakeschincariol/trader-skill` (11 skills) and
`Jakeschincariol/day-trader-skill` (11 skills). Both are MIT-licensed. They were
read, not installed, and none of their code is vendored here.

| Pattern in the references | Kept? | How it appears here |
| --- | --- | --- |
| One folder per skill, each with a `SKILL.md` and a small Python tool | Yes | `.claude/skills/fortune-*` (at the repo root). Each skill calls the shared Python package |
| Plain-Python tools that are deterministic and testable offline (`--offline DIR` + fixtures) | Yes | Every provider has an offline or local-file mode, and the tests run with no network |
| "Filed numbers first, never invent a number, say what is derived" (`trader-analyst`) | Yes, made stricter | Every number is a `Fact` that carries its source, period, unit and retrieval time. Missing data stays missing |
| State in a project folder that each skill reads and writes | Yes, made stricter | A SQLite research memory instead of loose JSON files |
| Seen-item dedupe for news (`trader-news`) | Yes | Announcement fingerprints are stored and compared across analyses |
| Polite fetching (identify yourself, rate limit) | Yes | `providers/http.py`: rate limit, retries with backoff, cache and source log |
| Broker / order execution (`trader-broker`, Alpaca MCP) | **No** | Out of scope. No module can place an order |

### Components that are US-specific and unsuitable for Indian markets

| Reference component | Why it does not transfer |
| --- | --- |
| SEC EDGAR XBRL `companyfacts`, `company_tickers.json`, CIKs (`trader-analyst`, `trader-news`) | US registrants only. Indian issuers file with NSE/BSE under SEBI LODR, and companies are identified by ISIN, NSE symbol and BSE scrip code |
| 8-K item 2.02 as "the earnings release" | India uses Reg. 33 LODR financial-results filings and Reg. 30 material-event disclosures on NSE/BSE |
| US GAAP concepts (`RevenueFromContractWithCustomer...`) | Ind AS line items (Revenue from operations, Other income, Finance costs, ...). Standalone and consolidated statements must be kept apart |
| 13F copycat (`trader-copycat`) | No Indian equivalent. The closest disclosures are quarterly shareholding patterns and SAST filings |
| House PTR / "Pelosi" tracker | US Congress disclosure. The Indian analogues are SEBI PIT insider disclosures and SAST Reg. 29/31 (pledge) filings |
| NYSE calendar, ET timezone, 9:30-16:00 session | NSE/BSE trading-holiday calendar, IST, 09:15-15:30 session, T+1 settlement |
| Alpaca broker MCP, paper trading, bracket orders | Order execution is excluded entirely |
| Wash-sale / US tax lots (`trader-tax`) | Indian STCG/LTCG rules, grandfathering and STT are different. Not built; a tax-aware module would need its own design |
| Yahoo `region=US` RSS, Nasdaq Trader symbol lists, Stooq `.us` | Wrong market. Yahoo `.NS`/`.BO` charts can be used as an **unofficial** price fallback only |
| Day-trading scanner, entry/exit timer, Monte-Carlo "time machine" | Out of scope for a research system |

## 2. Module map

```
fortune-securities/
  fortune_research/
    models.py            Source, Fact, Metric, Finding, DataIssue (provenance on every number)
    config.py            settings.toml loader; env-var credential lookup (never stored in files)
    identity.py          resolve "name / symbol / scrip code / ISIN" -> verified Security
    providers/           replaceable data-provider layer
      base.py              Provider interface + capability names
      registry.py          per-capability provider priority, fallback, provenance tagging
      http.py              HTTP client: rate limit, retries, backoff, SQLite cache, source log
      local_files.py       local CSV/JSON provider (manual input, sample data) - works today
      nse.py               NSE official archives / JSON endpoints (written, NOT verified live)
      bse.py               BSE official API (written, NOT verified live)
      yahoo.py             Yahoo .NS/.BO chart + split events (unofficial; flagged)
      xbrl.py              Reg. 33 results XBRL instance parser (config/xbrl_map.toml)
      ir.py                company investor-relations websites (PDF documents)
      rss.py               news feeds with publisher allowlist and near-duplicate merging
    documents.py         PDF text with page numbers, unit detection, line-item locator (review-only)
    health.py            provider health check: connection vs retrieval vs suitability per calculation
    verify.py            independent verification worksheet (figures vs original documents)
    analysis/corporate_actions.py   split/bonus parsing, price back-adjustment, per-share restatement
    analysis/lookahead.py           point-in-time availability (LODR deadlines when dates are unknown)
    portfolio/
      reader.py            [module 1] CSV/XLSX import, column aliases, account identifiers
      reconcile.py         holdings vs transactions reconciliation, validation
    analysis/
      financials.py        [module 4] growth, margins, EPS, ROE, ROCE, debt, cash flow, working capital
      forensic.py          [module 5] pledging, ownership change, auditor, RPT, accrual-quality flags
      valuation.py         [module 6] multiples, peer comps, DCF, P/B-ROE for financials
      technical.py         [module 7] SMA/EMA, RSI, MACD, support/resistance, volume, volatility
      portfolio.py         [module 8] allocation, concentration, sector exposure, XIRR vs benchmark, fit
      risk.py              [module 9] downside scenarios, liquidity, balance-sheet, invalidation rules
      news.py              [module 3] announcement classification (SEBI LODR categories), materiality
      quality.py           unit checks, statement reconciliation, staleness detection
    memory/
      store.py             [module 10] SQLite research memory + global source log
      diff.py              compare two analyses; re-test previous invalidation conditions
    report/
      markdown.py          [module 11] cited Markdown report
      excel.py             [module 11] .xlsx export (openpyxl)
    agent.py             [module 2] orchestrator: analyse company / portfolio / what changed
    cli.py               command line + natural-language command parsing
  config/                settings.example.toml, column_maps.toml
  sample_data/           SYNTHETIC companies, prices, portfolio (+ generator script)
  tests/                 unittest suite (offline)
  data/                  (git-ignored) your real portfolio, manual data, research.db, reports
```

### Data flow for "Analyse SYMBOL"

```
identity.resolve ──► registry (profile, financials, prices, announcements,
       │                      shareholding, governance, peers) ──► quality checks
       ▼                                                               │
 memory.previous ◄──────────────────────────────────────────────────── │
       │        financials ─► forensic ─► valuation ─► technical ─► risk ─► portfolio fit
       ▼                                                               │
   diff.compare ◄─────────────── analysis record ──────────────────────┘
       │                               │
       ▼                               ▼
 report.markdown / report.excel   memory.save (metrics, sources, findings,
                                   assumptions, invalidation rules)
```

## 3. Data-integrity rules (enforced in code)

1. **Every number has provenance.** A `Fact` holds its value, unit, period end,
   period type (FY/Q/POINT), basis (consolidated/standalone), source URL,
   publisher, whether the source is official, publication date and retrieval
   timestamp. A `Metric` holds its formula and the facts it was computed from.
2. **Missing stays missing.** A ratio whose input is absent is `None` and is
   reported as "not available" along with the input it lacked. No imputation, no
   defaults.
3. **Units are normalised and checked.** Amounts are converted to INR crore
   (lakh, million, rupee and crore inputs are accepted). An unknown unit is
   rejected.
4. **Statements are reconciled.** Checks include P&L arithmetic
   (PBT − tax = PAT), the balance sheet (assets = equity + liabilities),
   four quarters summing to the FY, and reported EPS against PAT ÷ shares.
   Mismatches become data-quality issues in the report.
5. **Staleness is explicit.** Each dataset is aged against `as_of`
   (prices > 5 days, quarterly results > 140 days after period end, shareholding
   > 120 days, annual > 456 days). Stale data is labelled in the report.
6. **Official before unofficial.** The provider priority is NSE/BSE/company
   filings, then licensed vendors, then unofficial sources. A number from an
   unofficial source is marked as such in the report.
7. **Synthetic data is labelled.** Sample data carries `synthetic: true`, and
   every report built from it carries a banner saying so.
8. **Credentials only from environment variables.** `config.py` resolves
   `api_key_env = "NAME"` to `os.environ["NAME"]` at call time, and nothing writes
   that value to disk or into a report.

## 4. Data-source options (Indian equities)

Prices and terms change, so check them before subscribing. "Official" means
the exchange or regulator, or the company itself.

| Source | Data | Official? | Cost | Limitations | Coverage | Status here |
| --- | --- | --- | --- | --- | --- | --- |
| NSE website JSON endpoints (`nseindia.com/api/...`) | Quotes, corporate announcements, shareholding, corporate actions, board meetings | Yes | Free | Undocumented and liable to change. Needs browser-like headers and session cookies, is rate-limited, and the ToS restrict automated or commercial use | All NSE-listed | Adapter written, **not verified live** (blocked in this sandbox) |
| NSE archives (`nsearchives.nseindia.com`) | `EQUITY_L.csv` securities master, daily bhavcopy (official EOD OHLCV) | Yes | Free | One file per day, so history means many downloads | All NSE equities | Adapter written, **not verified live** |
| NSE XBRL results / integrated filings | Machine-readable quarterly and annual financials | Yes | Free | Taxonomy parsing still to do | All NSE-listed | Planned (next milestone) |
| BSE API (`api.bseindia.com/BseIndiaAPI/...`) | Announcements with PDF links, results, scrip master | Yes | Free | Undocumented, needs a Referer/UA, liable to change | All BSE-listed (wider than NSE) | Adapter written, **not verified live** |
| BSE bhavcopy | Official EOD prices | Yes | Free | Format changed in 2024 (UDiFF) | All BSE equities | Planned |
| SEBI (`sebi.gov.in`) | Orders, SAST/PIT, regulations | Yes | Free | HTML/PDF only, no API | Regulatory actions | Manual input |
| Company IR pages / annual reports | Annual reports, auditor reports, RPT notes, concalls | Yes (company) | Free | PDFs. Extraction needs review | Per company | Manual input via local files; PDF parsing planned |
| MCA21 | Company master, charges, filings | Yes | Paid per document | No public bulk API | All companies | Manual |
| Nifty Indices / BSE indices | Index levels (benchmark) | Yes | Free download; licensed feeds paid | Manual CSV | NSE/BSE indices | Local CSV benchmark |
| RBI DBIE / CCIL | G-sec yields (risk-free rate for DCF) | Yes | Free | Manual download | Rates | Manual assumption in config |
| NSE Data & Analytics / BSE licensed feeds | Licensed EOD/fundamental/corporate-action feeds | Yes (licensed) | Paid, institutional | Contract required | Full | Provider slot available |
| CMIE Prowess, ACE Equity, Capitaline | Standardised fundamentals and history | No (vendor) | Paid, institutional | Licence | Deep, long history | Provider slot available |
| LSEG/Refinitiv, Bloomberg, FactSet, S&P Capital IQ | Everything | No (vendor) | Expensive | Licence | Full | Provider slot available |
| EODHD, Twelve Data, FMP, Alpha Vantage | Global APIs with NSE/BSE tickers | No | Free tier + paid | Indian fundamentals coverage inconsistent; check per symbol | Partial | Provider slot available |
| Broker APIs (Kite Connect, Upstox, SmartAPI, Dhan) | Historical OHLCV, holdings | No (broker) | Varies, some free with an account | **Need trading-account credentials, which this project forbids** | Full for prices | Excluded by policy. Import holdings from the broker's CSV export instead |
| Screener.in, Tijori, Trendlyne, Tickertape | Standardised fundamentals, exports | No | Free/paid tiers | Scraping is not permitted; manual export for personal use only | Broad | Manual export → local files (marked unofficial) |
| Yahoo Finance `.NS` / `.BO` chart endpoint | Daily OHLCV | **No** | Free | Unofficial, no SLA, can lag or mis-adjust for corporate actions | Most listed stocks | Adapter written (unofficial fallback, prices only), **not verified live** |
| Publisher RSS (ET Markets, Business Standard, Mint, Moneycontrol, Reuters) | News | No | Free | ToS; headlines are leads, not facts | Broad | Generic RSS adapter with a domain allowlist |
| MCP connectors | Any of the above | Depends | Depends | Configure later | — | `Provider` interface is the integration point |

## 5. What needs credentials, infrastructure or manual input

| Need | Why | Where |
| --- | --- | --- |
| Network access to NSE/BSE/Yahoo hosts | This cloud sandbox's network policy blocks them (HTTP 403 at the proxy) | Environment network settings, or run locally |
| Paid vendor API keys | Only for vendor providers you choose to enable | Env vars named in `settings.toml` (`api_key_env`) |
| Scheduled runs (daily news, quarterly re-analysis) | No scheduler is bundled | cron / Task Scheduler / Claude scheduled tasks calling the CLI |
| Annual-report content (auditor opinion, RPTs, contingent liabilities, CARO) | No reliable free API | `governance.json` per company, filled from the annual report with page references |
| Risk-free rate, equity risk premium, terminal growth | These are judgement calls | `[valuation]` in `settings.toml`, shown as assumptions in every report |
| Sector classification and peer set | No authoritative free mapping | `company.json` (`sector`, `industry`, `peers`) |
| Corporate actions (bonus/split) for holdings reconciliation | Exchange data not wired in yet | The reconciliation report flags a quantity mismatch for you to resolve |
