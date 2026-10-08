# Eval score · 2026-10-08 · shorter briefs, ⚠️ may break

Same 10 cases, briefs in `eval/results-short/`. Scored by a separate agent against `expected.md` and the new `format.md` limits, every ⚠️ and non-trivial claim checked in the repos.

| id | found | false + | format | chars |
|---|---|---|---|---|
| F1 | ✅ | 0 | ✅ | 1481 |
| F2 | ✅ | 0 | ✅ | 904 |
| F3 | ✅ | 0 | ✅ | 127 |
| G1 | ✅ | 0 | ✅ | 1026 |
| G2 | ✅ | 0 | ❌ proof bullet 3 fact is 9 words (max 6) | 1329 |
| G3 | ✅ | 0 | ✅ | 136 |
| E1 | ✅ | 0 | ✅ | 1098 |
| E2 | ✅ | 0 | ✅ | 1786 |
| E3 | ✅ | 0 | ✅ | 116 |
| L1 | ✅ | 0 | ✅ | 238 |

Found 10/10 · false positives 0 · format 9/10 (last: 10/10 · 0 · 9/10)

Total chars 8241 (last: 13684, −40%).

Notes:
- No ⚠️ may-break lines in any brief. The only ⚠️ is L1's correct message mismatch.
- G2 puts RunFd in the Run participant. True (RunFd calls RunListener, `gin.go:651`) and the proof says so, so not counted as a false positive.
- G1 doesn't say custom handlers are unaffected in words. "Default" in the summary plus naming only Recovery · RecoveryWithWriter covers it.
- All `Not checked:` lines are ≤12 words, max 1 ❓ per brief, max 5 proof bullets everywhere.
