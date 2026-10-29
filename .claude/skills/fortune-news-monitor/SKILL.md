---
name: fortune-news-monitor
description: >-
  News monitor module. Collects exchange announcements (NSE/BSE, SEBI LODR categories such as
  financial results, pledge/SAST, auditor or KMP resignation, credit rating, M&A, litigation, regulatory
  action) and credible publisher news from an allowlist, classifies materiality, de-duplicates, marks what is new
  since the last analysis and turns governance disclosures into forensic findings. Use when the user asks "any
  news on X", "new announcements", "what did the company disclose", or "did anything material happen".
---

# fortune-news-monitor

Run from the repository root:

```bash
cd fortune-securities
python3 -m fortune_research analyse SAMPLEMFG                 # fetches and classifies
python3 -m fortune_research show SAMPLEMFG --section news
```

- Exchange filings are primary evidence. Publisher headlines are tagged `news` / `lead`: they are leads to verify.
  Never present them as fact.
- Materiality `high`: results, pledge, auditor or KMP change, default, insolvency, regulatory action. Lead with these.
- `new: true` means the item was not in any earlier saved analysis of this company.
- The keyword rules are in `fortune_research/analysis/news.py` (`RULES`). If an item is misclassified, say so and
  suggest the rule change. Do not reclassify it silently.
- Publisher RSS feeds only run when listed under `[providers.rss] feeds` and inside `allowed_domains`.
- Scheduled monitoring needs external scheduling (cron, or a Claude scheduled task that runs `ask "What has changed?"`).

## Rules that apply to every Fortune skill

- **Never fabricate a number.** Quote only values printed by the tool or read from a cited source. If a value is
  `null` / `n/a`, say it is unavailable and name the missing input.
- **Cite.** Every figure you repeat carries its source reference (URL, period, publication date) from the record.
- **Say when data is stale, unofficial or synthetic.** Repeat the report's data-quality warnings; never drop them.
- **No orders, no trading credentials.** This system does research only. If asked to buy/sell, explain that it
  cannot place orders and offer the research instead.
- **Credentials** live in environment variables named in `config/settings.toml` (`*_env` keys), never in chat or files.
- Not investment advice: present evidence, assumptions and uncertainty, not instructions to trade.
