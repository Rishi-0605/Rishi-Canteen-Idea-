# Data formats

## Portfolio files (`data/portfolio/`, git-ignored)

Broker exports are accepted as they are. Headers are matched through `config/column_maps.toml`, and preamble
rows above the header are skipped.

**Holdings** (CSV/XLSX): `account`, `symbol` (NSE symbol, or BSE code; `.NS`/`.BO` and `-EQ` are stripped),
`isin` (recommended), `exchange`, `quantity`, `avg_cost`, `name`.
If there is no account column, every row is assigned to the file name (and a warning is raised).

**Transactions** (CSV/XLSX): `date`, `account`, `symbol`, `isin`, `exchange`, `side` (BUY/SELL, B/S),
`quantity`, `price`, `charges`, `trade_id`.

**Research notes** (CSV/XLSX): `date`, `symbol`, `author`, `title`, `note`, `stance`, `source_url`.

## Manual / exported market data (`data/manual/`, the local provider)

Every row names its source. Rows without a `source_url` are rejected and reported.

```
data/manual/
  master.csv                      securities master
  benchmarks/NIFTY50.csv          date, close[, open, high, low, volume]
  benchmarks/NIFTY50.source.json  {"url", "title", "publisher", "official", "retrieved_at", "adjusted"}
  companies/<NSE symbol or BSE code>/
    company.json        identity, sector, industry, face_value, peers, description
    financials.csv      one row per line item per period (long format)
    prices.csv          date, open, high, low, close, volume
    prices.source.json  source metadata for prices.csv
    announcements.csv   exchange disclosures
    news.csv            publisher headlines (treated as leads)
    shareholding.csv    quarterly shareholding pattern
    governance.json     annual-report governance facts, with page references
```

### master.csv

`name, isin, nse_symbol, bse_code, series, synthetic, source_url, publisher, official, retrieved_at`.
The NSE `EQUITY_L.csv` file can be converted to this layout, and once the NSE provider is enabled it is read directly.

### company.json

```json
{"name": "Example Industries Limited", "isin": "INE...", "nse_symbol": "EXAMPLE", "bse_code": "5xxxxx",
 "sector": "Capital Goods", "industry": "Industrial Machinery", "face_value": 10,
 "peers": ["PEER1", "PEER2", "PEER3"], "description": "One line on the business."}
```

### financials.csv

| column | meaning |
| --- | --- |
| `period_end` | YYYY-MM-DD (fiscal year ends 31 March; quarters 30 Jun / 30 Sep / 31 Dec / 31 Mar) |
| `period_type` | `FY`, `Q` or `POINT` |
| `basis` | `consolidated` or `standalone` (kept apart; consolidated preferred) |
| `line_item` | canonical name, listed below |
| `value`, `unit` | `INR crore`, `INR lakh`, `INR million`, `INR`; `INR per share` for EPS; `shares` / `crore shares` for share count |
| `source_url`, `source_title`, `publisher`, `official` | the filing you copied it from, and whether that is an official source |
| `published` | date the filing was published (analyses dated earlier will not see it) |
| `retrieved_at` | when you took the number (ISO timestamp) |

Line items:
P&L `revenue` (revenue from operations), `other_income`, `operating_expenses` (total expenses excluding finance
costs and D&A), `cost_of_goods_sold`, `depreciation`, `finance_costs`, `pbt`, `tax_expense`, `pat`,
`pat_attributable`, `eps_diluted`.
Balance sheet `equity_share_capital`, `other_equity`, `total_equity`, `borrowings_noncurrent`, `borrowings_current`,
`lease_liabilities`, `cash_and_equivalents`, `current_investments`, `trade_receivables`, `inventories`,
`trade_payables`, `current_assets`, `current_liabilities`, `total_assets`, `total_liabilities`,
`contingent_liabilities`.
Cash flow `cfo`, `capex` (purchase of PPE; sign is normalised to an outflow), `dividends_paid`.
Other `shares_outstanding`.

Leave a line item out rather than entering 0 when the filing does not give it. A missing value shows as n/a,
but a 0 would be used in the arithmetic.

### shareholding.csv

`quarter_end, promoter_pct, promoter_pledged_pct (% of the promoter holding), fii_pct, dii_pct, public_pct,
source_url, source_title, publisher, official, published, retrieved_at`.

### announcements.csv / news.csv

announcements: `date, exchange, category, subject, source_url, publisher, official, published, retrieved_at`
(the category may be left blank and is classified automatically).
news: `date, publisher, headline, source_url, official, published, retrieved_at`.

### governance.json

```json
{"fiscal_years": {"FY26": {
  "auditor": "...", "audit_opinion": "unmodified | qualified | adverse | disclaimer",
  "qualification_text": null, "emphasis_of_matter": null,
  "auditor_changed": false, "auditor_resigned": false, "auditor_resignation_reason": null,
  "caro_adverse_remarks": [], "rpt_total_cr": 140, "rpt_note": "...",
  "other_events": [{"severity": "medium", "text": "..."}],
  "source": {"url": "...", "title": "Annual report FY26", "publisher": "...", "official": true,
             "published": "2026-08-01", "page": "118-125", "retrieved_at": "..."}}}}
```
