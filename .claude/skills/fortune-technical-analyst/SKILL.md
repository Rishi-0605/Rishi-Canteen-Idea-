---
name: fortune-technical-analyst
description: >-
  Technical analyst module. Calculates indicators from daily price and volume: SMA 20/50/200, EMA,
  RSI (Wilder 14), MACD (12/26/9), swing-pivot support and resistance levels, 52-week range, average traded value,
  annualised volatility, max drawdown, 1m/6m/1y returns and beta vs the benchmark. Needs a minimum number of bars
  per indicator and reports insufficient history. Use when the user asks about the chart, trend, RSI, MACD,
  support, resistance, moving averages or volatility of an NSE/BSE stock.
---

# fortune-technical-analyst

Run from the repository root:

```bash
cd fortune-securities
python3 -m fortune_research analyse SAMPLEMFG
python3 -m fortune_research show SAMPLEMFG --section technical
```

- Prices come from the configured `prices` providers. Prefer official exchange data (NSE bhavcopy). If prices came from
  Yahoo (`official: false`), say so. Unknown corporate-action adjustment is flagged, and an unadjusted split or bonus
  distorts every indicator.
- Settings: `[technical]` (windows, RSI period, MACD, pivot window, minimum bars).
- Describe indicators as descriptions of past prices ("price is above its 200-day average"), not forecasts or signals to trade.
- Stale prices (older than `[staleness] prices` days) are reported in the data-quality section. Repeat that warning.

## Rules that apply to every Fortune skill

- **Never fabricate a number.** Quote only values printed by the tool or read from a cited source. If a value is
  `null` / `n/a`, say it is unavailable and name the missing input.
- **Cite.** Every figure you repeat carries its source reference (URL, period, publication date) from the record.
- **Say when data is stale, unofficial or synthetic.** Repeat the report's data-quality warnings; never drop them.
- **No orders, no trading credentials.** This system does research only. If asked to buy/sell, explain that it
  cannot place orders and offer the research instead.
- **Credentials** live in environment variables named in `config/settings.toml` (`*_env` keys), never in chat or files.
- Not investment advice: present evidence, assumptions and uncertainty, not instructions to trade.
