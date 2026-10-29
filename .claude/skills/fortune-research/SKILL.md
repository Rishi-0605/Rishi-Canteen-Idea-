---
name: fortune-research
description: >-
  Orchestrator for the FORTUNE SECURITIES Indian equity research agent (NSE/BSE). Handles the three
  top-level requests: "Analyse [company name, NSE symbol, BSE scrip code or ISIN]", "Analyse my portfolio" and
  "What has changed?". Resolves and verifies the company, pulls financials, announcements, shareholding,
  governance and prices through the provider layer, runs the financial, forensic, valuation, technical, risk and
  portfolio-fit modules, writes a cited Markdown report plus an Excel export, saves the record in SQLite and
  compares it with the previous analysis. Use when the user names an Indian listed company to research, asks
  about their portfolio, or asks what changed since the last report.
---

# fortune-research

The entry point. The other `fortune-*` skills are the individual modules; this one runs them in order.

Run from the repository root:

```bash
cd fortune-securities
python3 -m fortune_research ask "Analyse Sample Manufacturing"   # company
python3 -m fortune_research ask "Analyse my portfolio"
python3 -m fortune_research ask "What has changed?"               # latest company, re-analysed and compared
python3 -m fortune_research ask "What has changed for SAMPLEMFG?"
```

Add `--sample` to use the synthetic test data (separate database under `data/sample/`). Add `--as-of YYYY-MM-DD`
to reproduce an analysis as of a date (disclosures published later are excluded). `--json` prints the full record.

## Steps for "Analyse X"

1. Run `ask "Analyse X"`. If it exits with code 2 the name was ambiguous or unknown: show the candidates it
   printed and ask the user which one. Never pick one yourself.
2. Read the Markdown report it wrote (path printed). Summarise in this order: identity checks and warnings, the
   summary table, key flags, valuation range with its method spread and assumptions, risk scenarios and
   invalidation conditions, portfolio fit, and the changes section if there was a previous analysis.
3. Copy the data-quality section's errors and stale datasets into your answer. If confidence is "low", lead with that.
4. Give both file paths (Markdown and Excel).

## Steps for "Analyse my portfolio"

Run `ask "Analyse my portfolio"`. Report the totals, account-level figures (masked IDs), concentration and
sector limits breached, unpriced positions and every reconciliation issue. Positions that do not reconcile are
for the user to resolve; never "fix" a quantity yourself.

## Steps for "What has changed?"

Run `ask "What has changed?"`. Lead with triggered invalidation conditions, then new flags, then material metric
moves, new periods and new announcements. Use `changes SYMBOL --no-refresh` to compare the two saved analyses
without fetching anything.

## Rules that apply to every Fortune skill

- **Never fabricate a number.** Quote only values printed by the tool or read from a cited source. If a value is
  `null` / `n/a`, say it is unavailable and name the missing input.
- **Cite.** Every figure you repeat carries its source reference (URL, period, publication date) from the record.
- **Say when data is stale, unofficial or synthetic.** Repeat the report's data-quality warnings; never drop them.
- **No orders, no trading credentials.** This system does research only. If asked to buy/sell, explain that it
  cannot place orders and offer the research instead.
- **Credentials** live in environment variables named in `config/settings.toml` (`*_env` keys), never in chat or files.
- Not investment advice: present evidence, assumptions and uncertainty, not instructions to trade.
