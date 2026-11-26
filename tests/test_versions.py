# SPDX-FileCopyrightText: 2026 Paolo Ungari and contributors
# SPDX-License-Identifier: Apache-2.0
"""Every tool exposes the same release version through __version__ and --version (community/VERSIONING.md)."""
import os, re, subprocess, sys, unittest

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAMES = ["valida_profilo.py", "attiva_profilo.py", "release_diff.py"]


def declared(name):
    with open(os.path.join(TOOLS, name), encoding="utf-8") as f:
        return re.search(r'^__version__ = "([^"]+)"$', f.read(), re.M).group(1)


class VersionTest(unittest.TestCase):
    def test_same_version_everywhere(self):
        versions = {n: declared(n) for n in NAMES}
        self.assertEqual(len(set(versions.values())), 1, versions)
        self.assertRegex(versions[NAMES[0]], r"^\d+\.\d+\.\d+(-[0-9A-Za-z.]+)?$")

    def test_version_flag(self):
        for n in NAMES:
            p = subprocess.run([sys.executable, "-I", os.path.join(TOOLS, n), "--version"],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertEqual(p.returncode, 0, n)
            self.assertEqual(p.stdout.decode().strip(), f"{n} {declared(n)}")

    def test_changelog_matches(self):
        with open(os.path.join(TOOLS, "CHANGELOG.md"), encoding="utf-8") as f:
            released = re.findall(r"^## \[(\d[^\]]*)\]", f.read(), re.M)
        self.assertEqual(released[0], declared(NAMES[0]), "latest CHANGELOG release differs from __version__")


if __name__ == "__main__":
    unittest.main()
