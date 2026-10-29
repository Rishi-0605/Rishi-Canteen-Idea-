---
name: fortune-risk-analyst
description: >-
  Risk analyst module. Identifies downside scenarios (bear: EPS cut x peer 25th-percentile P/E;
  base and bull from the valuation range; repeat of the last year's worst drawdown), liquidity risk (average
  traded value, days to exit a position at a set participation), valuation risk (premium to peers, price above
  fair range), balance-sheet weakness (debt/equity, interest cover, current ratio, net debt/EBITDA), earnings
  decline and volatility. Writes explicit thesis-invalidation conditions that the next analysis re-tests. Use
  when the user asks "what could go wrong", "downside", "risks", "how liquid", or "when is the thesis wrong".
---

# fortune-risk-analyst

Run from the repository root:

```bash
cd fortune-securities
python3 -m fortune_research analyse SAMPLEMFG --position-value-cr 2.5   # liquidity for a planned size
python3 -m fortune_research show SAMPLEMFG --section risk
```

- Overall level (low / moderate / elevated / high) counts risk and forensic findings by severity.
- Invalidation conditions are generated from current values (for example "promoter pledge rises above 10%",
  "quarterly PAT declines YoY", "price closes below support X") and stored. "What has changed?" marks each one
  TRIGGERED, holds or unknown. Always report triggered conditions first.
- Scenario parameters: `[risk] bear_eps_decline`, `bear_multiple_percentile`, `adv_participation`.
- Scenarios are arithmetic on stated inputs, not forecasts.

## Rules that apply to every Fortune skill

- **Never fabricate a number.** Quote only values printed by the tool or read from a cited source. If a value is
  `null` / `n/a`, say it is unavailable and name the missing input.
- **Cite.** Every figure you repeat carries its source reference (URL, period, publication date) from the record.
- **Say when data is stale, unofficial or synthetic.** Repeat the report's data-quality warnings; never drop them.
- **No orders, no trading credentials.** This system does research only. If asked to buy/sell, explain that it
  cannot place orders and offer the research instead.
- **Credentials** live in environment variables named in `config/settings.toml` (`*_env` keys), never in chat or files.
- Not investment advice: present evidence, assumptions and uncertainty, not instructions to trade.
