---
name: fortune-research-memory
description: >-
  Research memory module. SQLite store of every analysis: company identity, structured metrics with
  formulas and source IDs, the source list (URL, publisher, official, published, period, retrieved), findings,
  assumptions, invalidation conditions and state, data issues, seen announcements, portfolio import snapshots,
  imported research notes and a global source log of every retrieval. Append-only, so earlier conclusions are
  preserved for comparison. Use when the user asks "what did we conclude last time", "history of X", "show the
  source log", or "compare with the previous report".
---

# fortune-research-memory

Run from the repository root:

```bash
cd fortune-securities
python3 -m fortune_research history SAMPLEMFG                     # every saved analysis
python3 -m fortune_research show SAMPLEMFG --section comparison   # diff stored with the latest analysis
python3 -m fortune_research changes SAMPLEMFG --no-refresh         # re-compare the two latest saved records
python3 -m fortune_research sources --limit 30                     # retrieval log (URL, status, cache hit, sha256)
```

- Database: `[general] database` (default `data/research.db`, git-ignored). The sample uses `data/sample/research.db`.
- Tables: companies, analyses (full JSON record), metrics, sources, findings, assumptions, conditions, state,
  data_issues, announcements_seen, source_log, portfolio_imports, portfolio_reports, research_notes.
- Records are never edited or deleted by these tools. If the user wants old records removed, confirm first. It is
  a destructive action on their research history.
- Historical research notes are imported from `[portfolio] research_note_files` and shown in company reports.

## Rules that apply to every Fortune skill

- **Never fabricate a number.** Quote only values printed by the tool or read from a cited source. If a value is
  `null` / `n/a`, say it is unavailable and name the missing input.
- **Cite.** Every figure you repeat carries its source reference (URL, period, publication date) from the record.
- **Say when data is stale, unofficial or synthetic.** Repeat the report's data-quality warnings; never drop them.
- **No orders, no trading credentials.** This system does research only. If asked to buy/sell, explain that it
  cannot place orders and offer the research instead.
- **Credentials** live in environment variables named in `config/settings.toml` (`*_env` keys), never in chat or files.
- Not investment advice: present evidence, assumptions and uncertainty, not instructions to trade.
