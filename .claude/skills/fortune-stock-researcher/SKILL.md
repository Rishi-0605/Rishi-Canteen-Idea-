---
name: fortune-stock-researcher
description: >-
  Stock researcher module. Resolves and verifies an Indian listed company (NSE symbol, BSE scrip
  code, ISIN or name; .NS/.BO suffixes accepted), checks the ISIN check digit and that NSE and BSE codes map to
  one ISIN, then gathers annual and quarterly results, exchange disclosures, shareholding and annual-report
  governance data with full provenance. Use when the user asks "who is X", "find the ISIN", "is this the right
  company", "get the latest results for X", or before any deeper module runs.
---

# fortune-stock-researcher

Run from the repository root:

```bash
cd fortune-securities
python3 -m fortune_research resolve "Sample Manufacturing"     # identity + verification only
python3 -m fortune_research resolve 990001.BO
python3 -m fortune_research analyse SAMPLEMFG                     # full retrieval + analysis
python3 -m fortune_research show SAMPLEMFG --section identity     # providers used, data dates and ages
```

## Identity rules

- An ambiguous name returns every candidate (exit code 2). Ask the user; never choose.
- Yahoo tickers (`SYMBOL.NS`, `CODE.BO`) are derived for the unofficial price fallback only. They are not identifiers.
- A security confirmed only by a local master (not an official exchange file) carries a warning; repeat it.

## Data sources, in priority order

Configured per capability under `[providers]` in settings. Official sources come first: NSE/BSE filings and
company documents, then licensed vendors, then unofficial sources. The NSE/BSE network adapters are written but
**not verified live** and are disabled by default. Until they are enabled, data comes from the local files in
`data/manual/` (layout: `docs/DATA_FORMATS.md`). When the user gives you a filing, help them enter its numbers
into that layout with the filing's URL, publication date and period on every row.

## Rules that apply to every Fortune skill

- **Never fabricate a number.** Quote only values printed by the tool or read from a cited source. If a value is
  `null` / `n/a`, say it is unavailable and name the missing input.
- **Cite.** Every figure you repeat carries its source reference (URL, period, publication date) from the record.
- **Say when data is stale, unofficial or synthetic.** Repeat the report's data-quality warnings; never drop them.
- **No orders, no trading credentials.** This system does research only. If asked to buy/sell, explain that it
  cannot place orders and offer the research instead.
- **Credentials** live in environment variables named in `config/settings.toml` (`*_env` keys), never in chat or files.
- Not investment advice: present evidence, assumptions and uncertainty, not instructions to trade.
