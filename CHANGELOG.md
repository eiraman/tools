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

## [0.3.0] - 2026-11-26

Scope: Change Request CR-010 of the method project (Wave CONS-01), which carries out the tools part of CR-009
after Guide 1.0.0-rc.3 (RFC 0003, item 10; decision D4 of the Human Manager on the fallback level). Version
bump: MINOR, the generator reads two new optional fields of the Digital Seniority map; nothing changes for a
map without them.

### Added

- `attiva_profilo.py`, generated catalogue (section 10 of `PROFILO.md`): two optional fields of
  `_seniority/seniority.json`.
  - `fallback_indicativo: true`: the fallback level is an indicative value that the mandate of the project
    sets. The sentence and the row of the table say so.
  - `fallback_eccezione: {"livello": "SDn", "compiti": "..."}`: tasks outside the catalogue of the named kinds
    start at the level of the exception. The table gains a second fallback row and the sentence names the
    exception.
- Tests: three cases on the generated catalogue (map without the new fields, indicative fallback with the
  exception, indicative fallback alone). 31 tests.

### Unchanged

- With a map that has neither field, the generated text is byte for byte the one of 0.2.3, so the registry
  releases up to role-profiles 0.5.1 validate as before. The registry tests still pin role-profiles v0.4.1
  and its 47-profile baseline; they follow the next registry release in a later PATCH.
- `valida_profilo.py` and `release_diff.py` change only their version number.

### Known limits

- The generated sentence does not say that a task outside the catalogue is promoted at the first failure for
  lack of capability (Guide §7.1, "Promotion and reduction"): that rule is in the AI Coordinator profile and
  in the explanation of the map, not in the generated catalogue.

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

[Unreleased]: https://github.com/eiraman/tools/compare/v0.3.0...main
[0.3.0]: https://github.com/eiraman/tools/compare/v0.2.3...v0.3.0
[0.2.3]: https://github.com/eiraman/tools/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/eiraman/tools/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/eiraman/tools/compare/v0.2.0...v0.2.1
[0.2.0]: https://github.com/eiraman/tools/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/eiraman/tools/releases/tag/v0.1.0
