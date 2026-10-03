# Contributing

## Report a wrong brief

The most useful report is a brief that says something the code doesn't support. Open an issue with:
- the commit or PR link (public repo, or a small repro)
- the `.mermaidiff/<mode>.md` it produced
- the line that is wrong, and why

## Change the rules

Rules live in `skill/format.md` and `skill/SKILL.md`. Before opening a PR that changes them:
1. run the eval in `eval/RUN.md` with your change
2. check the results against `eval/expected.md`
3. include the before and after scores in the PR

A rule change that adds a false positive on any eval case won't be merged.

## Add an eval case

Pick a public commit with a clear behavior change, add it to `eval/cases.md`, and write its must-have and must-not lines in `eval/expected.md`.
