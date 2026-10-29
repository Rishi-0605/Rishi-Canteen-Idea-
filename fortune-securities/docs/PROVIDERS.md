# Data providers: audit, status, limits

Last live check: **2026-10-29**, `health --symbol BEL` with every network provider enabled.
Result: **every network provider was DOWN**. The build environment's network policy refuses
connections to `nseindia.com`, `nsearchives.nseindia.com`, `bseindia.com`, `api.bseindia.com`,
`query1/query2.finance.yahoo.com`, `news.google.com` and company websites (proxy answers 403 to
CONNECT). So **no live retrieval has been verified yet**. Everything marked "not verified live"
below is code plus parser tests on hand-written format fixtures, nothing more.

## 1. Audit: where synthetic data enters, and what is switched off

### Synthetic data (by design, for testing)

| Function / file | What it does |
| --- | --- |
| `config.Settings.load(sample=True)` → `sample_data/settings.sample.toml` | points the local provider at `sample_data/`, sets `general.synthetic = true`, a separate DB (`data/sample/`) and demo valuation assumptions |
| `cli.main --sample`, `scripts/demo_sample.py`, `tests/helpers.Workspace` | the only callers of the sample settings |
| `sample_data/generate.py`, `sample_data/stages.py` (`build`, `apply`) | write the fictional dataset and its stage-2 update |
| `providers/local_files.LocalFilesProvider` | reads whatever is in the configured roots; a row is synthetic when `master.csv` / `company.json` say so |

Synthetic records carry `synthetic: true` through `Source`, `Security`, the analysis record and every
report banner. **No code path substitutes sample data when a live source fails:** with the default
settings the local provider reads `data/manual/` (your files), never `sample_data/`.

### Connectors switched off

`config/settings.example.toml` sets `enabled = false` for `nse`, `bse`, `yahoo`, `ir` and `rss`;
`providers/registry.Registry.__init__` builds a network provider only when it is enabled.

## 2. Status of every function

| Provider | Function | Source | Official | Status |
| --- | --- | --- | --- | --- |
| local | all capabilities | your files in `data/manual/` (layout: DATA_FORMATS.md) | per row | **Operational** (tested; the working path today) |
| local | `documents` | PDFs you download into `companies/<SYM>/documents/` | per manifest | **Operational**: text, page numbers, units, line-item locator |
| nse | `securities_master` | `nsearchives.nseindia.com/content/equities/EQUITY_L.csv` | yes | Not verified live |
| nse | `prices` | daily CM bhavcopy, UDiFF (`BhavCopy_NSE_CM_0_0_0_<date>_F_0000.csv.zip`) | yes | Not verified live |
| nse | `financials` | results index `api/corporates-financial-results` → XBRL instance → `providers/xbrl.py` | yes | Not verified live; XBRL element map (`config/xbrl_map.toml`) not yet confirmed on a real filing |
| nse | `announcements` | `api/corporate-announcements` | yes | Not verified live |
| nse | `corporate_actions` | `api/corporates-corporateActions` (subject text parsed to split/bonus factors) | yes | Not verified live |
| nse | `shareholding` | `api/corporate-share-holdings-master` (promoter / public totals) | yes | Not verified live; **no pledge, FII or DII** in this endpoint |
| bse | `securities_master` | `api.bseindia.com/.../ListofScripData` | yes | Not verified live |
| bse | `announcements` | `api.bseindia.com/.../AnnSubCategoryGetData` | yes | Not verified live |
| yahoo | `prices`, `benchmark`, `corporate_actions` | `query2.finance.yahoo.com/v8/finance/chart` (+ `events=split`) | **no** | Not verified live; unofficial fallback only |
| ir | `documents` | company IR pages listed in `company.json` → PDFs | yes (company) | Not verified live |
| rss | `news` | feeds you list (e.g. Google News search RSS), publisher allowlist | no | Not verified live |

### Not implemented

- Shareholding-pattern XBRL (pledge %, FII/DII split), SAST Reg. 31 pledge-disclosure parsing.
- BSE financial results and BSE corporate actions (NSE covers them for dual-listed companies).
- Pre-July-2024 NSE bhavcopy format (older history needs the legacy `cm<DDMONYYYY>bhav.csv.zip` files).
- OCR for scanned PDFs (they are reported as "no extractable text").
- Automatic use of PDF figures in calculations: by design they are review-only evidence.
- MCA21, SEBI orders and paid vendor APIs: the `Provider` interface accepts them; none is written.

## 3. Turning a provider on

1. Allow the provider's hosts in your network (cloud environment settings, or run locally).
2. Review the source's terms (below), then set `enabled = true` under `[providers.<name>]` in `config/settings.toml`.
3. Run `python -m fortune_research health --symbol BEL --capture data/fixtures/live` and read every line:
   a provider is usable only when its rows say **OPERATIONAL**, or **PARTIAL** with the unsuitable uses understood.
4. Check `financials` diagnostics: `unmapped` lists XBRL elements the map does not know. Add them to `config/xbrl_map.toml`.
5. Copy captured responses from `data/fixtures/live/` into `tests/fixtures/live/` (if their terms allow it) and add tests on them.
6. Run `verify` (README) before relying on any figure.

## 4. Rate limits, licensing, gaps

| Source | Access and terms | Rate limit used here | Known gaps |
| --- | --- | --- | --- |
| NSE website / API | Public pages, undocumented JSON; needs a browser session (cookies from the home page). NSE's terms restrict automated and commercial use; licensed data is sold by NSE Data & Analytics. Personal research use at low volume is the intended use here. Review the terms yourself. | 1.5 s between requests per host; cached 12 h | Endpoints and field names change without notice; bot protection may return HTML (reported as a failed retrieval); bhavcopy prices are unadjusted |
| NSE archives (bhavcopy, EQUITY_L) | Public files | 1.5 s; cached | one file per trading day; UDiFF only from July 2024 |
| BSE API | Public, undocumented; needs a Referer header | 1.5 s; cached | field names change; scrip master lacks NSE symbols |
| Yahoo Finance chart | Unofficial, no SLA, Yahoo terms apply; **not an exchange source** | 1 s; cached | can lag or mis-adjust; reports bonus issues as splits |
| Company IR websites | Company's own publications; site terms apply | HTTP cache | layouts vary; scanned PDFs need OCR; many sites block bots |
| Google News RSS / publisher RSS | Google and publisher terms apply; headlines are commentary, not company statements | cached | items link through news.google.com; full text not fetched |
| Credentials | None of the providers above needs a key. Paid vendors would: name the env var with `api_key_env`; keys are never stored in files (the loader refuses them). | | |
