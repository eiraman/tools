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

[Unreleased]: https://github.com/eiraman/tools/compare/v0.2.0...main
[0.2.0]: https://github.com/eiraman/tools/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/eiraman/tools/releases/tag/v0.1.0
