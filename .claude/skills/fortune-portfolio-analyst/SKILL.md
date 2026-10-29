---
name: fortune-portfolio-analyst
description: >-
  Portfolio analyst module. Evaluates an account-aware Indian equity portfolio: priced market value,
  unrealised P&L, weights per account and overall, top-1/top-5 concentration, HHI and effective positions,
  sector exposure, single-stock and sector limit breaches, money-weighted return (XIRR) against a benchmark
  replay of the same cash flows, and how a researched company fits (already held, sector overlap, return
  correlations, fundamentals vs holdings). Use for "analyse my portfolio", "how concentrated am I", "sector
  exposure", "am I beating the Nifty", or "how does X compare with what I own".
---

# fortune-portfolio-analyst

Run from the repository root:

```bash
cd fortune-securities
python3 -m fortune_research ask "Analyse my portfolio"
python3 -m fortune_research show SAMPLEMFG --section portfolio     # fit of a researched company
```

- Positions without a usable price are listed as **unpriced** and excluded from weights. They are never valued at cost.
- Account identifiers are masked in reports (`[portfolio] mask_account_ids`). Do not print full IDs in chat.
- XIRR comes from the transactions file. The benchmark XIRR replays the same dated cash flows into the benchmark
  series named by `[portfolio] benchmark` (a file `benchmarks/<NAME>.csv` with a `.source.json` beside it).
  Without transactions, the return is "not computable".
- Limits: `max_single_stock_weight`, `max_sector_weight`. Breaches are facts about the portfolio, not instructions to trade.
- Sectors come from each company's profile. "Unclassified" means no profile was given.

## Rules that apply to every Fortune skill

- **Never fabricate a number.** Quote only values printed by the tool or read from a cited source. If a value is
  `null` / `n/a`, say it is unavailable and name the missing input.
- **Cite.** Every figure you repeat carries its source reference (URL, period, publication date) from the record.
- **Say when data is stale, unofficial or synthetic.** Repeat the report's data-quality warnings; never drop them.
- **No orders, no trading credentials.** This system does research only. If asked to buy/sell, explain that it
  cannot place orders and offer the research instead.
- **Credentials** live in environment variables named in `config/settings.toml` (`*_env` keys), never in chat or files.
- Not investment advice: present evidence, assumptions and uncertainty, not instructions to trade.
