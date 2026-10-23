# Upstream drafts

These are issue drafts for sibling packages.  None is posted until Andras has
checked it; he posts them, signed (see `.claude/memory/feedback_outward_actions.md`).

Each draft was checked against the release named in it, using a fixture under
`scratch/query-repro/` (not tracked).  The drafts quote the fixture inline.

The numbering follows `docs/background.md` §2.5.  The rule is in `tasks.md`
`[upstream-asks]`: the `query` CLI is used first, and a library API is
requested only for a demonstrated limit.

| U | Draft | State |
|---|---|---|
| U1 | public callers API | **not drafted**: conditional (the CLI is sufficient so far) |
| U2 | `query-callees-tsv.md` | drafted 2026-10-16 |
| U3 | public import closure | **not drafted**: conditional (`query graph imports -f json` so far) |
| U4 | `query-callers-antiquotations.md` | drafted 2026-10-16 |
| U5 | `query-implicit-uses.md` | drafted 2026-10-16 |
| U6 | identifier-boundary helper and keyword table | **deferred**: draft when `rename` phase 1 is built, so the request carries a concrete use |
| U7 | `query-preamble-section-intro.md` | **posted** 2026-10-23 as [isabelle-query#28](https://github.com/ott2/isabelle-query/issues/28), rechecked against 1.1.0 |
| U8 | `<toplevel>` tsv rows | **fixed in 0.9.8**: rows carry theory, session and a `TOPLEVEL` tag.  NDTHT's draft `upstream/query-callers-batch.md` is obsolete |
| U9 | bound names as call-graph nodes | **deferred**: draft when `rename` phase 3 (constructor case names) is built |
| U10 | `query-same-line-declaration.md` | **posted** 2026-10-23 as [isabelle-query#29](https://github.com/ott2/isabelle-query/issues/29).  A declaration after `by …` on one line is missed, and the previous `cut_span` holds it (one AFP site) |
