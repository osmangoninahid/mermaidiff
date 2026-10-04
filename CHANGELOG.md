# Changelog

## 0.1.4

- Pre-approve only the two bundled scripts (`collect.py`, `view.py`) by name, not every script in the folder.

## 0.1.3

- Faster: `scripts/collect.py` gathers the diff, callers and readers in one call (GitHub PR brief 62 s → 27 s on Opus).
- Fewer permission prompts: the collector and `view.py` are pre-approved by the skill.
- Same brief for the same diff is reused (cache key in the first line).
- Eval re-run: 10/10 found, 0 false positives (`eval/SCORE-2026-10-04-speed.md`).

## 0.1.2

- PR and MR links work without `gh` or `glab`: the head is fetched with git and diffed against the merge-base. Only the PR title and description are skipped.

## 0.1.1

- install as a Claude Code plugin: `/plugin marketplace add osmangoninahid/mermaidiff`

## 0.1.0

First public version.
- `/mermaidiff` skill for commits, staged and unstaged changes, ranges, GitHub PRs and GitLab MRs
- browser viewer with live reload and Copy for MR, no server
- stat line recounted from the diagram
- eval: 10 commits on FastAPI, gin and excalidraw, 0 false positives
