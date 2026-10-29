---
name: fortune-valuation-analyst
description: >-
  Valuation analyst module. Values an Indian listed company with market multiples (P/E TTM, P/B,
  EV/EBITDA, EV/Sales, FCF and dividend yield), peer comparables (25th/median/75th percentile implied values),
  a two-stage FCFF DCF with a WACC x terminal-growth sensitivity grid, and sector methods (justified P/B vs ROE
  for banks/NBFCs/insurers, where EV and DCF methods are skipped). Prints every assumption. Use when the user
  asks "is it cheap", "what is it worth", "fair value", "compare valuation with peers" or "run a DCF".
---

# fortune-valuation-analyst

Run from the repository root:

```bash
cd fortune-securities
python3 -m fortune_research analyse SAMPLEMFG
python3 -m fortune_research show SAMPLEMFG --section valuation
```

## Configuration (`[valuation]` in config/settings.toml)

`risk_free_rate` (10Y G-sec yield as a decimal, with `risk_free_rate_as_of` and `risk_free_rate_source`) and
`equity_risk_premium` are **unset by default**, and the DCF and cost-of-equity methods do not run until the user
sets them. Do not supply values yourself. Ask the user, or point them to RBI DBIE / CCIL for the yield.
`terminal_growth`, `forecast_years` and `min_peers` have defaults that are printed as assumptions.

## Reading the output

- Fair-value range = median across methods of the low, mid and high values, so one outlier method cannot stretch
  it. `method_spread` shows the lowest and highest method midpoints. Always mention a wide spread.
- DCF: report the terminal-value share of EV. Above about 70%, the value rests on terminal assumptions.
- Peers come from `peers` in the company profile. Fewer than `min_peers` with a usable multiple means peer comps are skipped.
- These are model estimates under stated assumptions, not price targets or recommendations.

## Rules that apply to every Fortune skill

- **Never fabricate a number.** Quote only values printed by the tool or read from a cited source. If a value is
  `null` / `n/a`, say it is unavailable and name the missing input.
- **Cite.** Every figure you repeat carries its source reference (URL, period, publication date) from the record.
- **Say when data is stale, unofficial or synthetic.** Repeat the report's data-quality warnings; never drop them.
- **No orders, no trading credentials.** This system does research only. If asked to buy/sell, explain that it
  cannot place orders and offer the research instead.
- **Credentials** live in environment variables named in `config/settings.toml` (`*_env` keys), never in chat or files.
- Not investment advice: present evidence, assumptions and uncertainty, not instructions to trade.
