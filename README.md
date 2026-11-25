<!-- SPDX-License-Identifier: Apache-2.0 -->
# Eiraman tools

Command-line tools for Eiraman Role Profiles. Python 3, standard library only.

- `valida_profilo.py` checks a Role Profile folder: the two files (`PROFILO.md`, `profilo.json`), required sections and fields, the status, the qualification suite, the task catalogue, and forbidden content.
- `attiva_profilo.py` writes section 10 (task catalogue) of `PROFILO.md` and produces the activation file of a profile at a Digital Seniority level.

## Layout

Both tools expect to sit in `<registry>/_strumenti/`, next to `<registry>/_seniority/seniority.json`.

## Usage

```sh
python3 _strumenti/valida_profilo.py <profile-folder> [<profile-folder> ...]   # exit code 1 if any profile fails
python3 _strumenti/attiva_profilo.py --scrivi-catalogo <profile-folder>
python3 _strumenti/attiva_profilo.py <profile-folder> SD3 --strumento claude --out <folder>
```

Accepted statuses: `draft`, `qualified`, `maintained`, `suspended`, and the Italian `bozza non qualificata`, `qualificato`. The status is read only from the profile's status line (`Stato: …` or `Status: …`) and from the `stato` field of `profilo.json`. Section names are in Italian.

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

The registry tests need the Role Profile registry: by default a checkout of the `role-profiles` repository next to this one (`../role-profiles`); set `EIRAMAN_REGISTRY` to use another path. Without a registry they are skipped. `tests/baseline_registro.txt` holds the expected output for the 40 published profiles.

## Licence

Apache-2.0, see [LICENSE.md](LICENSE.md). Copyright (c) 2026 Paolo Ungari and contributors.
