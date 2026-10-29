---
name: fortune-report-generator
description: >-
  Report generator module. Produces the consistent FORTUNE SECURITIES research report (Markdown
  with numbered citations: summary scorecard, identity checks, financial tables, forensic findings, valuation,
  technical picture, risk scenarios and invalidation conditions, announcements, portfolio fit, changes since the
  previous analysis, assumptions, data quality, sources) and an Excel-compatible .xlsx export (numeric cells,
  one sheet per section, a Sources sheet). Also writes the portfolio report. Use when the user asks for "the
  report", "export to Excel", "a PDF/Word version", or wants to share the research.
---

# fortune-report-generator

Run from the repository root:

```bash
cd fortune-securities
python3 -m fortune_research analyse SAMPLEMFG        # writes data/reports/<SYMBOL>_<date>_<id>.md and .xlsx
python3 -m fortune_research portfolio                # writes data/reports/portfolio_<date>.md and .xlsx
```

- Reports go to `[general] reports_dir` (git-ignored). Give the user both paths.
- Citations `[n]` refer to the numbered Sources section and the Excel `Sources` sheet. Keep them when you quote.
- Synthetic-data reports carry a banner. Never remove it or present that data as real.
- For PDF or Word, convert the Markdown with the document skills available in the session. Do not retype numbers.
- The disclaimer at the end of every report stays in any derived document.

## Rules that apply to every Fortune skill

- **Never fabricate a number.** Quote only values printed by the tool or read from a cited source. If a value is
  `null` / `n/a`, say it is unavailable and name the missing input.
- **Cite.** Every figure you repeat carries its source reference (URL, period, publication date) from the record.
- **Say when data is stale, unofficial or synthetic.** Repeat the report's data-quality warnings; never drop them.
- **No orders, no trading credentials.** This system does research only. If asked to buy/sell, explain that it
  cannot place orders and offer the research instead.
- **Credentials** live in environment variables named in `config/settings.toml` (`*_env` keys), never in chat or files.
- Not investment advice: present evidence, assumptions and uncertainty, not instructions to trade.
