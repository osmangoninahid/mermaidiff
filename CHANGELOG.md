# Changelog

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
