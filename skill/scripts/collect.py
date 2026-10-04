#!/usr/bin/env python3
"""Collect the facts for a mermaidiff brief in one go, before the model starts.

Reads the /mermaidiff argument from argv, works out the mode, gets the diff with
git, lists the changed symbols and fields, and greps their callers and readers.
Prints markdown for SKILL.md to use, followed by format.md so the model needs no
extra read or permission for it.

It must never fail the skill: every error becomes a line in the output and the
exit code is always 0. Only the standard library is used.
"""
import hashlib
import os
import re
import shutil
import subprocess
import sys
import time

T0 = time.time()
DIFF_CAP = 80_000          # chars of diff text shown inline
HITS_PER_NAME = 8          # caller / reader lines per symbol or field
MAX_NAMES = 12             # symbols and fields to look up
NOISE = ("*.lock", "*lock.json", "*.min.js", "*.min.css", "*.map", "*.svg", "*.png",
         "*.jpg", "*.gif", "*.ico", "*.pdf", "*.snap", "go.sum", "uv.lock")
DOC_OR_TEST = re.compile(r"(\.(md|rst|txt)$|(^|/)(docs?|tests?|__tests__|spec)/|_test\.\w+$|\.(test|spec)\.\w+$|(^|/)test_[^/]+$)")
KEYWORDS = {"self", "this", "return", "class", "def", "func", "function", "const", "let", "var",
            "if", "else", "for", "while", "import", "from", "true", "false", "none", "null",
            "type", "struct", "interface", "string", "int", "bool", "float", "async", "await",
            "public", "private", "static", "export", "default", "new", "err", "error", "ctx"}

out = []


def say(line=""):
    out.append(line)


def run(args, timeout=30):
    """Run a command, return (code, text). Never raises."""
    try:
        p = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "") + (p.stderr if p.returncode else "")
    except Exception as e:  # missing tool, timeout, ...
        return 127, str(e)


def git(*args, timeout=30):
    return run(["git", *args], timeout)


def ok(*args):
    code, text = git(*args)
    return text.strip() if code == 0 else None


def origin_host_and_path():
    url = ok("remote", "get-url", "origin") or ""
    m = re.search(r"(?:@|//)([^/:]+)[:/](.+?)(?:\.git)?/?$", url)
    return (m.group(1).lower(), m.group(2).lower()) if m else ("", "")


def default_base():
    ref = ok("rev-parse", "--abbrev-ref", "origin/HEAD")
    if not ref:
        git("remote", "set-head", "origin", "-a", timeout=30)
        ref = ok("rev-parse", "--abbrev-ref", "origin/HEAD")
    for cand in ([ref] if ref else []) + ["origin/main", "origin/master", "main", "master"]:
        if cand and ok("rev-parse", "--verify", "--quiet", cand + "^{commit}"):
            return cand
    return None


def logged_in(tool):
    if not shutil.which(tool):
        return False
    code, _ = run([tool, "auth", "status"], timeout=10)
    return code == 0


# ---------------------------------------------------------------- mode

def parse(arg):
    a = arg.strip()
    first = a.split()[0] if a else ""
    m = re.search(r"github\.com/([^/]+/[^/]+)/pull/(\d+)", a)
    if m:
        return "pr", {"n": m.group(2), "repo": m.group(1).lower(), "host": "github"}
    m = re.search(r"https?://([^/]+)/(.+?)/-/merge_requests/(\d+)", a)
    if m:
        return "mr", {"n": m.group(3), "repo": m.group(2).lower(), "host": "gitlab"}
    m = re.fullmatch(r"(?:#|pr\s+)(\d+)", a, re.I)
    if m:
        return "pr", {"n": m.group(1), "host": "github"}
    m = re.fullmatch(r"(?:!|mr\s+)(\d+)", a, re.I)
    if m:
        return "mr", {"n": m.group(1), "host": "gitlab"}
    if re.fullmatch(r"\d+", a):
        host, _ = origin_host_and_path()
        return ("mr", {"n": a, "host": "gitlab"}) if "gitlab" in host else ("pr", {"n": a, "host": "github"})
    if a == "":
        return "auto", {}
    if a in ("staged", "wip"):
        return a, {}
    m = re.fullmatch(r"(?:commit\s+)?([0-9a-fA-F]{7,40})", a)
    if m:
        return "commit", {"sha": m.group(1)}
    if ".." in first and " " not in a:
        return "range", {"spec": a}
    if re.fullmatch(r"[A-Z][A-Z0-9]+-\d+", first) or "atlassian.net" in a:
        return "ticket", {}
    return "plan", {}


# ---------------------------------------------------------------- diff per mode

def diff_cmd(base, head=None):
    """git diff args with noise files excluded."""
    args = ["diff", "--no-color", "-U3", base] + ([head] if head else []) + ["--", "."]
    args += [f":(exclude,glob)**/{p}" for p in NOISE]
    return args


def get_change(mode, info):
    """Return dict: mode, base, head, label, claim, notes, read_at."""
    c = {"mode": mode, "notes": [], "claim": None, "read_at": "working tree"}
    if mode == "auto":
        if git("diff", "--cached", "--quiet")[0] == 1:
            mode = "staged"
        elif git("diff", "--quiet")[0] == 1:
            mode = "wip"
        else:
            mode = "commit"
            info = {"sha": "HEAD"}
        c["notes"].append(f"auto picked: {mode}")
        c["mode"] = mode
    if mode == "staged":
        c.update(base="--cached", head=None, label="staged changes", read_at="working tree (staged)")
    elif mode == "wip":
        c.update(base="HEAD", head=None, label="unstaged changes", read_at="working tree")
        c["wip"] = True
    elif mode == "commit":
        sha = ok("rev-parse", "--verify", "--quiet", info["sha"] + "^{commit}")
        if not sha:
            return fail(c, f"commit {info['sha']} not found in this repo")
        parent = ok("rev-parse", "--verify", "--quiet", sha + "^")
        base = parent or ok("hash-object", "-t", "tree", "/dev/null")
        c.update(base=base, head=sha, label=f"commit {sha[:10]}", read_at=sha)
        c["claim"] = ok("show", "-s", "--format=%s%n%n%b", sha)
        if ok("rev-parse", "--verify", "--quiet", sha + "^2"):
            c["notes"].append("merge commit: diff is against the first parent")
    elif mode == "range":
        spec = info["spec"]
        three = "..." in spec
        a, b = spec.split("..." if three else "..", 1)
        b = b or "HEAD"
        base = ok("merge-base", a, b) if three else ok("rev-parse", "--verify", "--quiet", a)
        head = ok("rev-parse", "--verify", "--quiet", b)
        if not base or not head:
            return fail(c, f"range {spec} not found")
        c.update(base=base, head=head, label=f"range {spec}", read_at=head)
    elif mode in ("pr", "mr"):
        return get_pr(c, mode, info)
    return c


def fail(c, why):
    c["error"] = why
    return c


def get_pr(c, mode, info):
    n = info["n"]
    host, path = origin_host_and_path()
    if info.get("repo") and path and not path.endswith(info["repo"]) and info["repo"] not in path:
        return fail(c, f"the link is for {info['repo']}, but this repo's origin is {path}. Run it inside that repo")
    ref = f"refs/mermaidiff/{mode}-{n}"
    src = f"pull/{n}/head" if mode == "pr" else f"merge-requests/{n}/head"
    code, text = git("fetch", "-q", "--no-tags", "origin", f"+{src}:{ref}", timeout=90)
    if code != 0:
        return fail(c, f"could not fetch {src} from origin ({text.strip().splitlines()[-1] if text.strip() else 'no output'}). Private repo without git login, or wrong number")
    head = ok("rev-parse", ref)
    base_branch = None
    tool = "gh" if mode == "pr" else "glab"
    if logged_in(tool):
        if mode == "pr":
            code, j = run(["gh", "pr", "view", n, "--json", "title,body,baseRefName"], timeout=20)
            if code == 0:
                import json
                d = json.loads(j)
                base_branch = d.get("baseRefName")
                c["claim"] = f"{d.get('title', '')}\n\n{d.get('body', '') or ''}".strip()
        else:
            code, j = run(["glab", "mr", "view", n, "-F", "json"], timeout=20)
            if code == 0:
                import json
                d = json.loads(j)
                base_branch = d.get("target_branch")
                c["claim"] = f"{d.get('title', '')}\n\n{d.get('description', '') or ''}".strip()
    else:
        c["notes"].append(f"No {tool} login: {'PR' if mode == 'pr' else 'MR'} title and description skipped.")
    base_ref = None
    if base_branch:
        git("fetch", "-q", "--no-tags", "origin", base_branch, timeout=60)
        if ok("rev-parse", "--verify", "--quiet", f"origin/{base_branch}"):
            base_ref = f"origin/{base_branch}"
    base_ref = base_ref or default_base()
    if not base_ref:
        return fail(c, "could not find the base branch (no origin/HEAD, main or master)")
    base = ok("merge-base", base_ref, head)
    if not base:
        return fail(c, f"no merge-base between {base_ref} and the {mode.upper()} head")
    c.update(base=base, head=head, label=f"{mode.upper()} {n} ({base_ref} → {ref})", read_at=ref)
    return c


# ---------------------------------------------------------------- names and lookups

DEF_RE = re.compile(r"^[+-]\s*(?:export\s+|public\s+|private\s+|protected\s+|static\s+|async\s+|pub\s+)*"
                    r"(?:def|class|func|function|fn|interface|struct|enum|type|message|service)\s+"
                    r"(?:\([^)]*\)\s*)?([A-Za-z_]\w*)")
CONST_FN_RE = re.compile(r"^[+-]\s*(?:export\s+)?(?:const|let|var)\s+([A-Za-z_]\w*)\s*=\s*(?:async\s*)?(?:\(|function)")
HUNK_RE = re.compile(r"^@@[^@]*@@\s*(?:.*?\b(?:def|class|func|function|fn)\s+(?:\([^)]*\)\s*)?)?([A-Za-z_]\w*)?")
FIELD_RE = re.compile(r"^[+-]\s*(?:readonly\s+)?([A-Za-z_]\w*)\??\s*:\s*[A-Za-z\[\{\"'(]")
GO_FIELD_RE = re.compile(r'^[+-]\s*([A-Z]\w*)\s+[\w.*\[\]]+\s*(?:`[^`]*json:"(\w+))?')
KEY_RE = re.compile(r"""^[+-].*?["'](\w{3,})["']\s*[:=]""")


def names_from(diff):
    syms, fields = [], []
    for line in diff.splitlines():
        if line.startswith(("+++", "---")):
            continue
        if line.startswith("@@"):
            m = HUNK_RE.match(line)
            if m and m.group(1):
                syms.append(m.group(1))
            continue
        if not line.startswith(("+", "-")):
            continue
        for rx, bucket in ((DEF_RE, syms), (CONST_FN_RE, syms)):
            m = rx.match(line)
            if m:
                bucket.append(m.group(1))
        m = GO_FIELD_RE.match(line)
        if m and (m.group(2) or m.group(1)):
            fields.append(m.group(2) or m.group(1))
        m = FIELD_RE.match(line)
        if m:
            fields.append(m.group(1))
        m = KEY_RE.match(line)
        if m:
            fields.append(m.group(1))

    def clean(xs):
        seen, res = set(), []
        for x in xs:
            if len(x) < 3 or x.lower() in KEYWORDS or x in seen or re.match(r"(Test|test_|Benchmark|Example)", x):
                continue
            seen.add(x)
            res.append(x)
        return res[:MAX_NAMES]

    syms = clean(syms)
    fields = [f for f in clean(fields) if f not in syms]
    return syms, fields


def grep(pattern, at, word=False, regex=False):
    """git grep at a commit or the working tree. Returns lines, capped."""
    args = ["grep", "-n", "-I", "--no-color"]
    if word:
        args.append("-w")
    args += ["-E" if regex else "-F", "-e", pattern]
    if at:
        args.append(at)
    args += ["--", "."] + [f":(exclude,glob)**/{p}" for p in NOISE]
    code, text = git(*args, timeout=30)
    lines = [l for l in text.splitlines() if l.strip()] if code == 0 else []
    if at:
        lines = [l[len(at) + 1:] if l.startswith(at + ":") else l for l in lines]
    more = len(lines) - HITS_PER_NAME
    return lines[:HITS_PER_NAME], max(more, 0)


# ---------------------------------------------------------------- main

def main():
    arg = " ".join(sys.argv[1:])
    arg = arg.strip()
    if not ok("rev-parse", "--is-inside-work-tree"):
        say("mermaidiff facts: not inside a git repo. Plan or ticket mode only.")
        return
    mode, info = parse(arg)
    say("## Pre-collected facts")
    say(f"- argument: `{arg or '(none)'}` → mode **{mode}**")
    if mode in ("ticket", "plan"):
        say("- no git diff for this mode. Follow SKILL.md steps 1 and 2 by hand.")
        return
    c = get_change(mode, info)
    for n in c["notes"]:
        say(f"- {n}")
    if c.get("error"):
        say(f"- **stop:** {c['error']}")
        return
    mode = c["mode"]
    base, head = c["base"], c["head"]
    stat_args = ["diff", "--stat=120"] + ([base] if base != "--cached" else ["--cached"]) + ([head] if head else [])
    if base == "--cached":
        dargs = ["diff", "--cached", "--no-color", "-U3", "--", "."] + [f":(exclude,glob)**/{p}" for p in NOISE]
    else:
        dargs = diff_cmd(base, head)
    stat = ok(*stat_args) or ""
    _, diff = git(*dargs, timeout=60)
    if not diff.strip():
        say(f"- **empty:** nothing changed in {c['label']}.")
        return
    files = ok(*(["diff", "--name-only"] + (["--cached"] if base == "--cached" else [base]) + ([head] if head else []))) or ""
    files = [f for f in files.splitlines() if f]
    key = hashlib.sha256((mode + diff).encode()).hexdigest()[:16]
    brief = os.path.join(".mermaidiff", f"{mode}.md")
    say(f"- change: {c['label']}")
    say(f"- read code at: `{c['read_at']}`" + (" (use `git show <ref>:<path>`)" if c['read_at'] not in ("working tree", "working tree (staged)") else ""))
    say(f"- brief file: `{brief}` · cache key: `{key}`")
    try:
        with open(brief, encoding="utf-8") as fh:
            if f"mermaidiff-key: {key}" in fh.readline():
                say(f"- **cache hit:** `{brief}` already briefs this exact diff. Reuse it: rerun view.py with --open, reply with its summary, and stop.")
    except OSError:
        pass
    graphs = [g for g in (".codegraph", "graphify-out/graph.json") if os.path.exists(g)]
    say(f"- code graph: {', '.join(graphs) if graphs else 'none, callers below come from git grep'}")
    if files and all(DOC_OR_TEST.search(f) for f in files):
        say("- hint: only docs or tests changed. Likely **No flow change.**")
    if c.get("claim"):
        say("\n### Claim (commit message / PR text, not proof)")
        say("```text")
        say(c["claim"][:3000])
        say("```")
    say("\n### Diff stat")
    say("```text")
    say(stat.strip()[:4000])
    say("```")
    say("\n### Diff")
    say("```diff")
    if len(diff) > DIFF_CAP:
        say(diff[:DIFF_CAP])
        say("```")
        say(f"(diff cut at {DIFF_CAP} chars of {len(diff)}. Read the rest of the files listed in the stat with `git diff` or Read.)")
    else:
        say(diff.rstrip())
        say("```")
    syms, fields = names_from(diff)
    at = None if c["read_at"].startswith("working tree") else c["read_at"]
    if syms:
        say("\n### Callers of changed symbols (git grep, word match)")
        for s in syms:
            lines, more = grep(s, at, word=True)
            if len(lines) + more > 40:
                say(f"- `{s}`: {len(lines) + more} hits, too common to list. Search it yourself if it matters.")
                continue
            say(f"- `{s}`: {len(lines) + more} hits" + (f" (first {len(lines)})" if more else ""))
            for l in lines:
                say(f"  - {l[:200]}")
    if fields:
        say("\n### Readers of changed fields (string and attribute access)")
        for f in fields:
            pat = rf"""["']{re.escape(f)}["']|\.{re.escape(f)}\b"""
            lines, more = grep(pat, at, regex=True)
            if len(lines) + more > 40:
                say(f"- `{f}`: {len(lines) + more} hits, too common to list. Search it yourself if it matters.")
                continue
            say(f"- `{f}`: {len(lines) + more} hits" + (f" (first {len(lines)})" if more else ""))
            for l in lines:
                say(f"  - {l[:200]}")
    say(f"\n_collected in {time.time() - T0:.1f}s_")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:  # never fail the skill
        say(f"- collect.py error: {e}. Collect the facts by hand (SKILL.md steps 1 and 2).")
    try:
        fmt = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "format.md")
        with open(fmt, encoding="utf-8") as fh:
            say("\n---\n## Output format (format.md)\n")
            say(fh.read())
    except OSError as e:
        say(f"- could not read format.md ({e}). Read it from the skill folder.")
    print("\n".join(out))
    sys.exit(0)
