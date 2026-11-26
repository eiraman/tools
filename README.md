<!-- SPDX-License-Identifier: Apache-2.0 -->
# Eiraman tools

Command-line tools for Eiraman Role Profiles. Python 3, standard library only.

- `valida_profilo.py` checks a Role Profile folder: the two files (`PROFILO.md`, `profilo.json`), required sections and fields, the status, the qualification suite, the task catalogue, and forbidden content.
- `attiva_profilo.py` writes section 10 (task catalogue) of `PROFILO.md` and produces the activation file of a profile at a Digital Seniority level.
- `release_diff.py` reports the differences between two Git refs of any repository, for the independent scope review of a release ([community/RELEASING.md](https://github.com/eiraman/community/blob/main/RELEASING.md)).

All tools share one version (`__version__`, printed by `--version`); changes are in [CHANGELOG.md](CHANGELOG.md).

## Layout

Both tools expect to sit in `<registry>/_strumenti/`, next to `<registry>/_seniority/seniority.json`.

## Usage

```sh
python3 _strumenti/valida_profilo.py <profile-folder> [<profile-folder> ...]   # exit code 1 if any profile fails
python3 _strumenti/attiva_profilo.py --scrivi-catalogo <profile-folder>
python3 _strumenti/attiva_profilo.py <profile-folder> SD3 --strumento claude --out <folder>
```

The generated catalogue ends with the fallback for tasks outside the catalogue, read from
`_seniority/seniority.json`: `fallback` is the level; the optional `fallback_indicativo: true` says that the
level is an indicative value the mandate of the project sets; the optional
`fallback_eccezione: {"livello": "SDn", "compiti": "..."}` names the tasks that start at a higher level.
Without the two optional fields the text is the one of the versions before 0.3.0.

Accepted statuses: `draft`, `qualified`, `maintained`, `suspended`, and the Italian `bozza non qualificata`, `qualificato`. The status is read only from the profile's status line (`Stato: …` or `Status: …`) and from the `stato` field of `profilo.json`. Section names are in Italian.

## Release diff

```sh
python3 release_diff.py <repo> <old-ref> <new-ref> [--json] [--max-lines N]
python3 release_diff.py ../guide v1.0.0-rc.1 HEAD          # text report
python3 release_diff.py ../guide v1.0.0-rc.1 HEAD --json   # the same report as JSON
```

`release_diff.py` does not need the registry layout: it reads any Git repository. Between `<old-ref>` (the
previous release tag) and `<new-ref>` (the release candidate) it reports:

| Section | Content |
|---|---|
| Files added, removed, renamed | Renames and copies as Git detects them (`-M`), with the similarity |
| Files modified | Lines added and removed per modified file (`binary` for binary files) |
| Markdown headings removed or renamed | ATX headings outside fenced code; a heading replaced in place by another is reported as renamed; headings of deleted Markdown files are removed |
| RFC 2119 key words | For each changed Markdown file, the counts of MUST, MUST NOT, SHOULD, SHOULD NOT and MAY (capitals only) before and after, marked `CHANGED` when they differ |
| JSON keys removed | For each changed `.json` file, such as `profilo.json`, the key paths that disappear; list items are folded into `[]`, for example `catalogo[].note` |
| Removed non-blank lines | Every removed line as `old-path:line: text`, capped by `--max-lines` (default 200); the total is always given |

The report is information for the reviewer, not a gate: whenever it is produced the exit code is 0, even
if it lists removals. The exit code is 2 only when no report can be produced (not a Git repository, unknown
ref). The scope reviewer maps every item to a changelog entry or an approved decision (RELEASING.md, step 5).

## Forbidden terms

The validator always rejects local paths, likely credentials and private keys. Terms specific to your context, such as organisation or internal tool names, go in a local file named `.eiraman-deny.local`: one regular expression per line, lines starting with `#` are comments. Never commit it; it is listed in `.gitignore`.

The validator reads every such file it finds:

1. the path in the `EIRAMAN_DENY_FILE` environment variable;
2. `.eiraman-deny.local` in the current directory;
3. `.eiraman-deny.local` in the tool's folder or its parents, up to the repository root.

If none exists, only the generic patterns apply.

## Tests

```sh
cd tests && python3 -m unittest -v
```

`test_release_diff.py` builds throwaway Git repositories and needs `git`; `test_versions.py` checks that the tools share one version, equal to the latest release in `CHANGELOG.md`. The registry tests need the Role Profile registry: by default a checkout of the `role-profiles` repository next to this one (`../role-profiles`); set `EIRAMAN_REGISTRY` to use another path. Without a registry they are skipped. `tests/baseline_registro.txt` holds the expected output for the 48 standard profiles of the pinned registry.

## Licence

Apache-2.0, see [LICENSE.md](LICENSE.md). Copyright (c) 2026 Paolo Ungari and contributors.
