<!--
SPDX-FileCopyrightText: 2026 Paolo Ungari and contributors
SPDX-License-Identifier: Apache-2.0
-->

# Changelog

All notable changes to the Eiraman tools are documented in this file. The format is based on
[Keep a Changelog 1.1](https://keepachangelog.com/en/1.1.0/), and the tools follow
[Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html) (see
[community/VERSIONING.md](https://github.com/eiraman/community/blob/main/VERSIONING.md)). All tools in this
repository share one version, exposed as `__version__` and by `--version`.

## [Unreleased]

## [0.3.2] - 2026-11-26

Scope: Change Request CR-010 of the method project. Corrections from the independent re-review of 0.3.0 and
0.3.1 (REV-CONS-C). Version bump: PATCH, fixes that restore the behaviour the entry 0.3.0 declared.

### Fixed

- `attiva_profilo.py`: `fallback_indicativo` given as `1` or `0` was accepted and read as "not indicative",
  although the entry 0.3.0 said that a value that is not true or false is refused; it is now refused. Also
  refused, with a message that names the field: `compiti` of `fallback_eccezione` that is not a text, and a
  `fallback` that is not a level of the map (it ended in an unexplained error).
- Tests: the invalid values above are covered; the cases without the exception check that no exception row is
  written, and the case of a map without the new fields checks the last row of the table against a fixed text.
- `README.md`: the baseline holds the 48 standard profiles of the pinned registry (it said 40).

### Notes on 0.3.0, recorded here

- The generated catalogue does not carry the mark `"provata": false` of the configurations not yet tested
  (Guide §7.1, "Catalogue"): the mark is in the map and in its explanation only.
- RFC 0003, "Impact", names three changes under Tools. The role label in the run records and the Manager View
  (governance share, progress with its denominator) are carried out in the registry, in `controllore/`
  (role-profiles 0.6.0), where the Manager View generator lives; no tool of this repository reads run
  records. The traceability check is not in this repository: the point stays open for the guide repository.

## [0.3.1] - 2026-11-26

Scope: Change Request CR-010 of the method project (Wave CONS-01). Version bump: PATCH, tests and CI only; no
tool changes its behaviour.

### Changed

- The registry tests follow role-profiles 0.6.0: `tests/baseline_registro.txt` lists the 48 standard profiles
  of that release, the 47 of 0.4.1 plus `analisi-funzionale/scrum-master-ai` (registry 0.5.0), and the test
  expects 48. The templates in `_modello/` stay outside the baseline. Registry 0.6.0 uses the fallback fields
  of the Digital Seniority map that tools 0.3.0 introduced.
- CI: `PROFILES_REF` in `tests.yml` pins role-profiles 0.6.0
  (`8eb5fa852faeac6ea91219b85beb30b4f512c31b`, a local candidate, not yet tagged). **Order of publication:**
  role-profiles 0.6.0 must be published before this release, and tools 0.3.0 before role-profiles 0.6.0.
- `attiva_profilo.py`, `valida_profilo.py` and `release_diff.py` change only their version number.

## [0.3.0] - 2026-11-26

Scope: Change Request CR-010 of the method project (Wave CONS-01), which carries out the tools part of CR-009
after Guide 1.0.0-rc.3 (RFC 0003, item 10; decision D4 of the Human Manager on the fallback level). Version
bump: MINOR, the generator reads two new optional fields of the Digital Seniority map; nothing changes for a
map without them.

With a map that has neither field, the generated text is byte for byte the one of 0.2.3, so role-profiles
v0.4.1 and the unpublished registry candidates 0.5.0 and 0.5.1 validate as before. The registry tests still
pin role-profiles v0.4.1 and its 47-profile baseline; they follow the next registry release in a later PATCH.
`valida_profilo.py` and `release_diff.py` change only their version number.

Known limit: the generated catalogue states the fallback level and its exception only. The other rules of
the Guide §7.1 on tasks outside the catalogue are not in the generated text: the AI Coordinator records the
task, proposes adding it to the catalogue and reports the share of such tasks in the cycle review
("Fallback"), and raises the level at the first failure for lack of capability ("Promotion and reduction").
They are in the AI Coordinator profile and in the explanation of the map.

### Added

- `attiva_profilo.py`, generated catalogue (section 10 of `PROFILO.md`): two optional fields of
  `_seniority/seniority.json`.
  - `fallback_indicativo: true`: the fallback level is an indicative value that the mandate of the project
    sets. The sentence and the row of the table say so.
  - `fallback_eccezione: {"livello": "SDn", "compiti": "..."}`: tasks outside the catalogue of the named kinds
    start at the level of the exception. The table gains a second fallback row and the sentence names the
    exception. When the fallback is indicative, the exception is marked as indicative too (RFC 0003, item 10:
    value and exception are both Guidance).
  - A map with an invalid value is refused with a message that names the field, and no profile is written:
    `fallback_indicativo` that is not true or false; `fallback_eccezione` without `livello` or `compiti`, with
    a level that is not in the map, or with a level not higher than `fallback`. The validator then reports
    that section 10 cannot be compared.
- `README.md`: the two fields are documented.
- Tests: five cases on the generated catalogue (map without the new fields; indicative fallback with the
  exception; indicative fallback alone; fixed fallback with the exception; invalid maps refused). 33 tests.

## [0.2.3] - 2026-11-26

Scope: Change Requests CR-004, CR-005 and CR-006 of the method project (Wave REL-07).

### Changed

- The registry tests follow role-profiles 0.4.1: `tests/baseline_registro.txt` lists the 47 standard
  profiles of that release, the 43 of 0.3.0 plus `governo/revisore-architettura-applicativa-dati`,
  `governo/revisore-architettura-cloud`, `governo/revisore-legale-compliance` and
  `governo/revisore-test-qualita`, and the test expects 47. The templates in `_modello/` stay outside the
  baseline.
- CI: `PROFILES_REF` in `tests.yml` pins role-profiles v0.4.1
  (`a49e54b579025bff9afbe32b90c6a75771d4c6ee`).

### Fixed

- CI, `compliance.yml`: the local-path check removes http(s) URLs from the matched lines and matches
  again, so a path segment inside a URL is no longer flagged. The block is the one of `role-profiles`
  v0.4.1, keeping this repository's exclusions of `valida_profilo.py` and `tests/` (CR-005, CR-006).

## [0.2.2] - 2026-11-26

### Changed

- The registry tests follow role-profiles 0.3.0: `tests/baseline_registro.txt` lists the 43 standard
  profiles of that release, the 41 of 0.2.0 plus `governo/revisore-privacy` and
  `governo/revisore-sicurezza`, and the test expects 43. The templates in `_modello/` stay outside the
  baseline.
- CI: `PROFILES_REF` in `tests.yml` pins role-profiles v0.3.0
  (`adeedb4c940c637f93d46a9b58d22839e6dfee7a`).

## [0.2.1] - 2026-11-26

### Changed

- The registry tests follow role-profiles 0.2.0: `tests/baseline_registro.txt` lists the 41 standard
  profiles of that release, the 40 earlier ones plus `governo/revisore-ai`, and the test expects 41. The
  templates in `_modello/` stay outside the baseline, as in the role-profiles CI.
- CI: `PROFILES_REF` in `tests.yml` pins role-profiles v0.2.0
  (`77ca4d0e80ac4c0fef441ae39ea141b117590eca`).

## [0.2.0] - 2026-11-26

### Added

- `release_diff.py`: report of the differences between two Git refs for the independent scope review of a
  release (files added, removed and renamed; lines per modified file; Markdown headings removed or
  renamed; RFC 2119 key word counts; JSON keys removed; removed lines). With tests.
- `__version__` and `--version` in `valida_profilo.py`, `attiva_profilo.py` and `release_diff.py`, and a
  test that keeps them equal to the latest release in this changelog.
- This changelog, and the CI workflow `changelog.yml`.

## [0.1.0] - 2026-11-25

First public release, published as commit `558ddb2` of `github.com/eiraman/tools` during the restricted
launch of 25 November 2026. It was not tagged; the version number was assigned afterwards
(VERSIONING.md). The tag `v0.1.0` will be applied retroactively to that commit. The role-profiles CI pins this commit as `TOOLS_REF`.

### Added

- `valida_profilo.py`, the Role Profile validator: the two files, required sections and fields, status,
  qualification suite, the task catalogue against section 10, and forbidden content.
- `attiva_profilo.py`: writes section 10 (task catalogue) of `PROFILO.md` and the activation file of a
  profile at a Digital Seniority level for Claude Code, Codex or GitHub Copilot.
- Unit tests, with a baseline of the expected output for the 40 published profiles.
- CI: unit tests against a pinned `role-profiles` commit, compliance checks (DCO and AI declaration,
  REUSE, secrets and deny-list).

### Changed

- Before publication, the organisation-specific forbidden terms moved from the code to a local file
  excluded from Git (`.eiraman-deny.local`, or the path in `EIRAMAN_DENY_FILE`); the code keeps only
  generic patterns (local paths, credentials, private keys).
- The validator accepts the English statuses `draft`, `qualified`, `maintained` and `suspended` beside
  the Italian ones.
- Licence: Apache-2.0. Earlier copies of the scripts, distributed in the eiraman.tech kit under MIT, keep
  that licence.

[Unreleased]: https://github.com/eiraman/tools/compare/v0.3.2...main
[0.3.2]: https://github.com/eiraman/tools/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/eiraman/tools/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/eiraman/tools/compare/v0.2.3...v0.3.0
[0.2.3]: https://github.com/eiraman/tools/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/eiraman/tools/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/eiraman/tools/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/eiraman/tools/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/eiraman/tools/releases/tag/v0.1.0
