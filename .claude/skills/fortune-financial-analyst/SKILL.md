---
name: fortune-financial-analyst
description: >-
  Financial analyst module. Calculates revenue, EBITDA, PAT and EPS growth (YoY, QoQ, 3y/5y CAGR,
  TTM), margins, ROE, ROCE, debt/equity, net debt, interest coverage, CFO/PAT, free cash flow and working-capital
  days from Ind AS statements in INR crore, with a formula and source on every number, plus reconciliation checks
  (PBT-tax=PAT, assets=equity+liabilities, quarters sum to the year, EPS vs PAT/shares). Use when the user asks
  about growth, margins, returns, leverage, cash conversion or "show me the financials".
---

# fortune-financial-analyst

Run from the repository root:

```bash
cd fortune-securities
python3 -m fortune_research analyse SAMPLEMFG
python3 -m fortune_research show SAMPLEMFG --section financials
python3 -m fortune_research show SAMPLEMFG --section quality      # reconciliation and staleness issues
```

## Definitions (stated in every report)

EBITDA = revenue - operating expenses (else PBT + finance costs + D&A - other income). EBIT = PBT + finance costs.
ROE = PAT / average equity. ROCE = EBIT / average (equity + debt). Debt = borrowings + lease liabilities.
FCF = CFO - |capex|. Days use closing balances (inventory and payables on COGS when given, else revenue, labelled).
TTM = last four consecutive quarters, else the latest FY (labelled). Consolidated is preferred; standalone is
used only when no consolidated statements exist, and the basis is printed.

## Rules

- Compare like with like: quarterly growth is against the same quarter last year. QoQ is shown, but businesses are seasonal.
- A metric with a missing input is `null`, and its `missing` field names the input. Never estimate it.
- Repeat reconciliation warnings. A PBT/PAT gap usually means exceptional items, so read the filing's notes.
- Banks and NBFCs: margins and working-capital days do not apply. Say so rather than quoting them.

## Rules that apply to every Fortune skill

- **Never fabricate a number.** Quote only values printed by the tool or read from a cited source. If a value is
  `null` / `n/a`, say it is unavailable and name the missing input.
- **Cite.** Every figure you repeat carries its source reference (URL, period, publication date) from the record.
- **Say when data is stale, unofficial or synthetic.** Repeat the report's data-quality warnings; never drop them.
- **No orders, no trading credentials.** This system does research only. If asked to buy/sell, explain that it
  cannot place orders and offer the research instead.
- **Credentials** live in environment variables named in `config/settings.toml` (`*_env` keys), never in chat or files.
- Not investment advice: present evidence, assumptions and uncertainty, not instructions to trade.
