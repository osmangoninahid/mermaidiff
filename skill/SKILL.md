---
name: mermaidiff
description: Brief any change as a git-style Mermaid flow diff (new / changed / removed) with payload diff, impact and open questions. Use for /mermaidiff, a Jira ticket, GitLab MR or GitHub PR link, commit sha, staged or unstaged changes, branch range, plan, refactor idea, or bug walkthrough, or when the user says "brief me".
allowed-tools: Bash(python3 "${CLAUDE_SKILL_DIR}/scripts/*)
---

# mermaidiff

Gather the facts, write the brief in the exact format in `format.md` (same folder), then open it in the browser.

## 0. Collect the facts first

Your first tool call, before reading anything else: run the bundled collector with the user's argument as one quoted string (empty string if none):

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/collect.py" '<argument>'
```

It prints the mode, the diff, the claim (commit message or PR text), and the callers and readers from `git grep`, taken at the right commit, in about a second. It ends with the full text of `format.md`, so you don't need to read that file.

Use its output and don't run those git commands again:
- `**stop:**` or `**empty:**` → reply with that reason in one line and stop.
- `**cache hit:**` → do what it says and stop.
- Otherwise go to step 2, and only fetch what is still missing.

If the script can't run (no `python3`) or prints an error, collect the facts yourself with step 1 and read `format.md` in this skill's folder.

**Be fast:** when you need several files or searches, request them all in one turn (parallel tool calls), not one by one.

## 1. Parse the argument (only if the collector failed)

| Argument | Mode | Get the change with |
|---|---|---|
| (none) | auto | staged if any, else unstaged, else last commit |
| `staged` | staged | `git diff --cached` |
| `wip` | unstaged | `git diff` |
| 7–40 hex chars, or `commit <x>` | commit | `git show --stat <sha>` then `git diff <sha>^ <sha>` |
| contains `..` | range | `git diff <base>...<head>` |
| GitHub PR URL, `#123`, or `pr <x>` | pr | `gh pr view <n> --json title,body,baseRefName,headRefName,headRefOid` and `gh pr diff <n>` |
| GitLab MR URL, `!123`, or `mr <x>` | mr | `glab mr view <iid>` and `glab mr diff <iid>` |
| a bare number | pr or mr | pick by `git remote get-url origin`: github.com → `gh`, gitlab → `glab` |
| Jira key (`ABC-123`) or Atlassian URL | ticket | Read issue + comments (Jira MCP), then find the current flow in code. "After" side is `(inferred)` |
| anything else | plan | Current flow from code, "after" from the text. Mark it `(inferred)` |

If the diff is empty (nothing staged, no changes), reply with one line only: `Nothing to brief: <why>. Try /mermaidiff <sha> or stage changes.` Don't write or overwrite a brief.

For a PR or MR, read code at its head, not your local checkout. Fetch it by number, which also works for forks: GitHub `git fetch origin pull/<n>/head`, GitLab `git fetch origin merge-requests/<iid>/head`. Then read files with `git show FETCH_HEAD:<path>`. The PR/MR title and body are claims, like a commit message.

If `gh` or `glab` is missing or not logged in, still brief the PR or MR with git alone. Fetch the head as above, then:
1. Base: `git merge-base origin/HEAD FETCH_HEAD`. If `origin/HEAD` is not set, run `git remote set-head origin -a` once, or try `origin/main`, then `origin/master`.
2. Diff: `git diff <base> FETCH_HEAD`.
3. Say in one line: `No gh login: PR title and description skipped.` (or `glab`, `MR`).

Never fall back to the local diff for a PR or MR. If the fetch fails (private repo, wrong number, or the PR is from another repo than `origin`), say why in one line and stop.

If a Jira login is missing, say so in one line and brief the ticket text the user gave as a plan.

If the change is only tests, docs, comments, logs or formatting: brief is `**No flow change.** <what changed>`. Skip step 2.

## 2. Find the relatives of the change

For each changed function, class, model or field:

1. **If `.codegraph/` exists:** `codegraph callers <symbol> --json`, `codegraph callees <symbol> --json`, `codegraph impact <symbol> --depth 2 --json`
2. **Else if `graphify-out/graph.json` exists:** `graphify explain "<symbol>"`, `graphify query "<question>"`
3. **Else:** grep for the symbol name.

For changed **fields** (payload, model, DB doc), also grep for string access, since graphs miss it:
`rg -n "['\"]<field>['\"]|\.<field>\b"`

For each reader, check: **required or optional?** (`x["f"]` vs `x.get("f")`, `Optional[...]`, `omitempty`, `?.`, `??`)

Before reporting any break, prove it is reachable: walk back from the reader to an entry point and look for guards that block it (`if`, early `return`, `raise`, feature flag, type or category check, config). Blocked or unsure → drop it. Report only proven breaks (see "The first rule" in `format.md`).

Keep 1–2 hops only. You need the path the change travels, not the whole system.

**Scope is the current repo only.** Don't open sibling repos, even if they are on disk. Callers outside the repo (UI, other services, API clients) are one participant in the diagram and one line in `Not checked:`.

## 3. Write and show the brief

1. Write the brief to `.mermaidiff/<mode>.md` in the repo root with the Write tool (the folder is gitignored by convention). If the facts gave a cache key, make the first line `<!-- mermaidiff-key: <key> -->`.
2. Render it: `python3 "${CLAUDE_SKILL_DIR}/scripts/view.py" .mermaidiff/<mode>.md --open` (a plain command, no `&&` or heredoc, so it matches the pre-approved rule). It writes `.mermaidiff/<mode>.html` and opens it in the default browser. No server. Run it outside any sandbox so it can open the browser.
3. In the chat reply, print only: the summary line, 🔴 lines, ❓ lines, and the `file://` link `view.py` printed. Never print the `.md` path as a link.

## 4. Adjust and execute

- If the change came from git (commit, staged, wip, range, PR, MR), the diff is fact. The user may hide steps, but never rewrite facts to match: keep proof, payload and impact true, and add one line `Hidden by you: N steps · <what>` under the stat line. Only plan and ticket briefs can be changed freely.
- If the user edits lines ("drop step 4", "make it optional"), rewrite only those parts in the same file and run `view.py` again **without** `--open`. The open tab reloads itself.
- When approved, the approved brief is the spec. Implement exactly that.
- After implementing, run `git diff` and compare built vs approved: list ✅ matches and ⚠️ gaps (asked but not built, or built but not asked).
