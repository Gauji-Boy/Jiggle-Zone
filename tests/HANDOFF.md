# Jiggle handoff

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

`run_tests.ps1` copies the source and bundled assets into each installed extension before running
the Blender suites on every installed version; it runs the name audit and its self-test once with
Python. Logs land in `artifacts\<stamp>\` with `summary.txt`.

`make_review_packet.ps1` writes `scratch\reviews\<label>\`:

- `change.diff` — the whole diff, binaries excluded
- `files.txt` — changed files with add/remove counts
- `api.diff` — only changed `def` / `class` lines
- `zip-sha.txt` — sha256 of every entry in the ZIP
- `summary.txt` — git revision, `git status --short`, hashes, test verdicts, packet problems

It exits non-zero, and says why in `summary.txt`, when:

- the working tree is dirty (override with `-AllowDirty`, which is recorded);
- `-To` does not match the working tree, so the ZIP would not be described by the diff;
- the ZIP's contents differ from the source tree, or its `__init__.py` is not the working file;
- the committed blob and the working file differ beyond CRLF/LF.

That last check exists because the repository stores LF and checks out CRLF on Windows, so the
blob hash and the working-file hash are never equal even for identical content. `summary.txt`
reports both and the collapsed comparison, so a reviewer can confirm the ZIP matches the commit.

`tests\repack_zip.py` rebuilds the ZIP and fails if any entry has a backslash, contains
`__pycache__`, or if the packaged `__init__.py` differs from the source.

## Runtime QA (handoff text)

The repeatable runtime checks live in `tests\runtime\`:

| Script                            | Needs                    | Checks                                            |
| --------------------------------- | ------------------------ | ------------------------------------------------- |
| `test_viewport_qa.py`             | `poc_cage_xpbd_kasumi`   | rewind drift on the evaluated mesh, finite frames, followers, cage modifier |
| `test_secondary_scene.py`         | any scene                | registration, operator availability, scene props   |
| `test_clean_install_zip.py`       | the built ZIP            | install, byte parity, version agreement, operators |
| `test_legacy_names.py`            | source tree only         | 2.x `Giggle_*` modifiers and groups are still discovered |
| `test_cage_rebuild_preserves_clothing.py` | installed add-on + `poc_cage_xpbd_kasumi` | a garment's clothing Surface Deform survives cage generation and rebuild, cage discovery ignores bare clothing names |
| `test_legacy_attach.py`           | installed add-on + `poc_cage_xpbd_kasumi` | re-attaching clothing leaves one bound Surface Deform, shape and deformation unchanged |
| `test_wiggy_versions.py`          | source tree only         | `Wiggy 0.1` and `Wiggy 0.2.0` both work through presets, bake detection, cage lookup and the Socket_2 attribute path |
| `test_back_face_filter.py`        | source tree only         | `Mark`/`Clear Back Faces` write an exact per-face mask through the real `Collider`, never touch the mesh, stay in front of `Collider`, read the live Edit Mode selection, and mute a stale mask in `depsgraph_update_pre` - before the evaluation that would use it - after any topology change including same-count swaps and corner changes, failing closed when the topology record is missing or the check cannot run, finding the filter by node group even after a rename, keeping the guard inactive in clean scenes, while surviving save, undo, sharing and linked data |

`test_wiggy_versions.py` imports the add-on from source and registers it itself, so it runs headless
with `--factory-startup` and needs no installed profile:

```
blender -b --factory-startup --python-exit-code 1 --python tests/runtime/test_wiggy_versions.py
```

The source-level audit that stops hardcoded Wiggy group names creeping back is plain Python:

```
python tests/test_wiggy_name_audit.py            # audit jiggle_zone/
python tests/test_wiggy_name_audit.py --selftest # prove it still detects a regression
```

`test_cage_rebuild_preserves_clothing.py` and `test_legacy_attach.py` drive `bpy.ops.jiggle.*`, so
the add-on must be installed and enabled in the profile that runs them: they need the installed
copy, not the source file. Run them without `--factory-startup`, which skips the user preferences
that enable the extension:

```
blender -b poc_cage_xpbd_kasumi.blend --python-exit-code 1 \
    --python tests/runtime/test_cage_rebuild_preserves_clothing.py
blender -b poc_cage_xpbd_kasumi.blend --python-exit-code 1 \
    --python tests/runtime/test_legacy_attach.py
```

Installing the add-on also means the profile needs the assets the code asks for, including
`Wiggy_0.2.0.blend`; a profile synced from an older ZIP fails `add_zone` with
`Could not load node tree 'Wiggy 0.2.0' from assets`.

`run_tests.ps1` runs every suite in the table on each installed Blender version, plus the name
audit and its `--selftest` once (they need Python, not Blender). Before each version's suite it
copies the source, the changelog and `jiggle_zone\assets\*.blend` into that profile, so a missing
asset fails the run instead of hiding behind a stale install. Nothing in `tests\runtime\` needs to
be invoked by hand. Verified on 5.2.2 LTS and 5.3.0 Beta.

They exit non-zero on failure. A QA report is only meaningful if the script can fail — the earlier
viewport script caught every exception and printed `PASS`, and measured `obj.data` (which no
modifier can move), so it reported zero drift no matter what happened.

> You are testing an update to Jiggle Physics. Your job is runtime verification, not redesign.
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
source, then verify the ZIP: its `jiggle_zone/__init__.py` entry must hash the same as
`jiggle_zone/__init__.py` in the tree.

Version numbers must agree in three places: `jiggle_zone/blender_manifest.toml`, `bl_info` in
`jiggle_zone/__init__.py`, and the top `##` heading in `jiggle_zone/CHANGELOG.md`.

## Known limits in the test suite

- `bpy.data.is_dirty` is always `False` in a background session, so the dirty-backup path is
  driven by `create_project_backup(dirty=True)` rather than by a real unsaved edit.
- A bake that fails mid-write cannot be forced from Python; only the "no pre-delete" and
  "failed on a broken modifier" paths are covered.
- Everything here is headless. Viewport feel, playback smoothness and clothing interaction need
  runtime QA.
