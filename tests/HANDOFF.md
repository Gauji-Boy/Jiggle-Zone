# Giggle handoff

Three roles, one source of truth.

| Role        | Does                                                        | Never does                     |
| ----------- | ----------------------------------------------------------- | ------------------------------ |
| Developer   | Implements, writes tests, commits on `dev`, self-reviews     | Tests in the GUI, tags `main`  |
| Runtime QA  | Runs real files in 5.2.2 and 5.3.0, reports evidence         | Edits the implementation       |
| Reviewer    | Reads the diff and the logs, accepts or rejects the release   | Trusts a summary               |

## Branches

`main` is the released line only. Work happens on `dev` and is merged to `main` when the
reviewer accepts it. Tag every merge (`v2.0.1-maintenance1`, …) so any change is recoverable.

`v2.0.0-baseline` is the audited 2.0.0 source. It never moves.

## Developer

```
git checkout dev                 # never edit main
powershell -ExecutionPolicy Bypass -File tests\run_tests.ps1
powershell -ExecutionPolicy Bypass -File tests\make_review_packet.ps1 -From v2.0.0-baseline
```

`run_tests.ps1` copies the source into each installed extension first, then runs both suites on
every installed Blender. Logs land in `artifacts\<stamp>\` with `summary.txt`.

`make_review_packet.ps1` writes `scratch\reviews\<label>\`:

- `change.diff` — the whole diff, binaries excluded
- `files.txt` — changed files with add/remove counts
- `api.diff` — only changed `def` / `class` lines
- `summary.txt` — git revision, source and zip hashes, test verdicts

## Runtime QA (handoff text)

> You are testing an update to Giggle Physics. Your job is runtime verification, not redesign.
>
> 1. Read `change.diff` and understand the intended change.
> 2. Test the source on Blender 5.2.2 LTS and 5.3.0 Beta.
> 3. Use real project files. Run `tests\run_tests.ps1` for the automated suites.
> 4. Check for regressions in cage XPBD, full-mesh XPBD, clothing attachment, presets, baking,
>    Rebake All, cache invalidation and scene isolation.
> 5. Compare against the previous release (`git checkout v2.0.0-baseline`).
> 6. Do not modify the implementation. Do not report a test as passed unless you ran it.
>    Separate automated results from visual checks.
>
> Report per test: Blender version, what was done, expected, actual, PASS / FAIL / NOT TESTED,
> log or screenshot, and any regression. Say explicitly what you could not test.

## Reviewer

Read `change.diff`, `api.diff` and `summary.txt`. Re-check the claims that matter against the
source, then verify the ZIP: its `giggle_addon/__init__.py` entry must hash the same as
`giggle_addon/__init__.py` in the tree.

## Known limits in the test suite

- `bpy.data.is_dirty` is always `False` in a background session, so the dirty-backup path is
  driven by `create_project_backup(dirty=True)` rather than by a real unsaved edit.
- A bake that fails mid-write cannot be forced from Python; only the "no pre-delete" and
  "failed on a broken modifier" paths are covered.
- Everything here is headless. Viewport feel, playback smoothness and clothing interaction need
  runtime QA.
