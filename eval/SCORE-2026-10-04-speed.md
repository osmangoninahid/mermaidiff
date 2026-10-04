# Eval score · 2026-10-04 · speed change (collector script), Opus

Same 10 cases as `SCORE-2026-10-04.md`, run with `/mermaidiff <sha>` after adding `scripts/collect.py`. Scored by a separate agent against `expected.md`, every 🔴 and non-trivial claim checked in the repos.

| id | found | false + | format | chars |
|---|---|---|---|---|
| F1 | ✅ | 0 | ✅ | 2379 |
| F2 | ✅ | 0 | ✅ ⚠️ Checked line 26 words | 1556 |
| F3 | ✅ | 0 | ✅ | 157 |
| G1 | ✅ | 0 | ✅ | 1777 |
| G2 | ✅ | 0 | ✅ | 1956 |
| G3 | ✅ | 0 | ✅ | 134 |
| E1 | ✅ | 0 | ✅ ⚠️ Checked line 27 words | 2048 |
| E2 | ✅ | 0 | ❌ Checked line 32 words (max 25) | 3301 |
| E3 | ✅ | 0 | ✅ | 124 |
| L1 | ✅ | 0 | ✅ | 252 |

Found 10/10 · false positives 0 · format 9/10 (baseline: 10/10 · 0 · 9/10).

Notes:
- Briefs are 16% longer than the baseline, mostly extra prose after the proof bullets and long Checked lines.
- E1 ⚠️: marks the UNFOLLOW payload as new, though only its call path is new. Not a false claim about behavior.
- New useful questions: F1 no tiebreaker on sort, G2 a 0 value can't turn the timeout off.

Speed, A/B on the same machine (Opus):

| case | before | after |
|---|---|---|
| GitHub PR (gin #4800) | 62 s · 11 turns · $0.44 | **27 s** · 5 turns · $0.29 |
| staged (2 files) | 34 s · 5 turns · $0.52 | 36 s · 6 turns · $0.30 |
