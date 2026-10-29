---
name: fortune-portfolio-reader
description: >-
  Portfolio reader module. Imports holdings, transactions, quantities, average costs, account
  identifiers and historical research notes from broker CSV/XLSX exports (column aliases, preamble rows,
  multi-account), validates every row and reconciles holdings against transactions (bonus/split hints, cost
  mismatches, oversells, duplicates). Use when the user wants to load or check portfolio files, says "import my
  holdings", "check my transactions", "why doesn't my quantity match", or adds a new broker export.
---

# fortune-portfolio-reader

Run from the repository root:

```bash
cd fortune-securities
python3 -m fortune_research import-portfolio            # validate + reconcile, saves an import snapshot
python3 -m fortune_research --sample import-portfolio   # try it on the synthetic sample first
```

Files come from `[portfolio]` in `config/settings.toml`: `holdings_files`, `transaction_files`,
`research_note_files` (CSV or XLSX, several allowed). Put real files under `data/portfolio/` (git-ignored).

## Column mapping

`config/column_maps.toml` maps your broker's headers to canonical fields (account, symbol, isin, quantity,
avg_cost; date, side, price, charges, trade_id). Matching ignores case, spaces and punctuation. If the import
reports `header_not_found`, add the broker's header text as an alias. Do not rename columns in the user's file.

## What it checks

- quantity positive (fractional flagged), cost non-negative, ISIN check digit, BUY/SELL side, parseable dates
- duplicate holdings per account and repeated trade IDs
- reconciliation: transactions' net quantity and weighted-average cost (broker convention; sells do not change
  average cost) vs the holdings file: `matched`, `qty_mismatch` (with a "exactly Nx: bonus or split?" hint),
  `cost_mismatch` (>1%), `no_transactions`, `missing_holding`, `oversold`

Report every issue with its file and row. Never edit quantities or costs to make them reconcile; the user resolves
corporate actions and missing trades.

## Rules that apply to every Fortune skill

- **Never fabricate a number.** Quote only values printed by the tool or read from a cited source. If a value is
  `null` / `n/a`, say it is unavailable and name the missing input.
- **Cite.** Every figure you repeat carries its source reference (URL, period, publication date) from the record.
- **Say when data is stale, unofficial or synthetic.** Repeat the report's data-quality warnings; never drop them.
- **No orders, no trading credentials.** This system does research only. If asked to buy/sell, explain that it
  cannot place orders and offer the research instead.
- **Credentials** live in environment variables named in `config/settings.toml` (`*_env` keys), never in chat or files.
- Not investment advice: present evidence, assumptions and uncertainty, not instructions to trade.
