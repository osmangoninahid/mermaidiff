# Expected answers (scorer only, never shown to the run)

Score per case: found (all must-haves) · false (any must-not or unproven warning) · size (chars of the brief) · format (stat line matches, tiers present).

## F1 · 3c1f7c4 · created_at
must: ➕ `created_at` column on user and item tables (migration, nullable) · ➕ `created_at` in `UserPublic` and `ItemPublic` (optional) · ✏️ list users and list items now order by `created_at desc` (items: both superuser and owner query) · payload diff for the 2 public models
ok if present: regenerated frontend client types (same repo)
must not: any 🔴 · claims about what a UI shows · warnings about API clients
note: NULL ordering for old rows is a fair ❓ only, never 🔴

## F2 · 9fe3a4d · 403
must: ✏️ read, update and delete item return 403 instead of 400 when the user is not the owner and not superuser · all 3 routes named
must not: any 🔴 about clients expecting 400 (outside repo)

## F3 · 458fddd
must: one line `No flow change.` (tests only)

## G1 · 4a3eb31 · recovery
must: ✏️ default recovery handler records the panic in `c.Errors` (non-error values wrapped with fmt.Errorf) before aborting with 500 · entry points: `Recovery()` / `RecoveryWithWriter` default path · custom handlers (`CustomRecovery*`) not affected
ok if present: ⚠️ message body mentions a quic-go bump the diff doesn't contain
must not: claims that custom recovery handlers changed

## G2 · d8f2d58 · ReadHeaderTimeout
must: ➕ `Engine.ReadHeaderTimeout` field, default 10s (zero or negative → 10s) · ✏️ `Run`, `RunTLS`, `RunListener` set it on their `http.Server`
must not: claims that `RunUnix`, `RunFd` or other run methods changed

## G3 · 074b669
must: one line `No flow change.` (tests only)

## E1 · 02fc9f35 · setViewport
must: ✏️ `setViewport` with a resolved target now calls `requestUnfollow` (UNFOLLOW intent via `onUserFollow` when `userToFollow` is set) · `setViewport(null)` and an unresolved target don't
must not: claims that following itself changed

## E2 · 14e1c614 · onDuplicate
must: payload diff for the `onDuplicate` signature (3rd arg `data` lookups, may return `false`) · returned duplicates are merged into the editor's own · omitted duplicates are vetoed · applies to paste/library insert, duplicate action, alt-drag
must not: more than 12 diagram steps · invented behavior not in the diff

## E3 · 5a406e51
must: one line, `No flow change.` (one locale string)

## L1 · lying commit
setup: a commit that only adds a line to README.md, message `fix(router): redirect trailing slash for POST routes`
must: `No flow change.` + a `⚠️ Message says …` line
