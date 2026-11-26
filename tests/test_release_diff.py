# SPDX-FileCopyrightText: 2026 Paolo Ungari and contributors
# SPDX-License-Identifier: Apache-2.0
"""Tests for release_diff.py (standard library only). Each test builds a throwaway Git repository.

Run from this folder:  python3 -m unittest -v"""
import json, os, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOL = os.path.join(os.path.dirname(HERE), "release_diff.py")
sys.path.insert(0, os.path.dirname(HERE))
import release_diff as rd  # noqa: E402

HAS_GIT = shutil.which("git") is not None

OLD_MD = """# Title

## Rules

The agent MUST record the cost. It MUST NOT publish. It SHOULD ask.
The team MAY skip it.

## Old section

Text that goes away.

```
# not a heading
```
"""

NEW_MD = """# Title

## Rules

The agent MUST record the cost. It SHOULD ask. It SHOULD NOT guess.

## New section

Text that goes away.
"""

OLD_JSON = {"id": "p", "versione": "0.1.0", "catalogo": [{"id": "T01", "note": ""}], "fasi": ["a"]}
NEW_JSON = {"id": "p", "versione": "0.2.0", "catalogo": [{"id": "T01"}]}


@unittest.skipUnless(HAS_GIT, "git is not installed")
class ReleaseDiffTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.repo = tempfile.mkdtemp(prefix="eiraman-rd-")
        self = cls
        self.git("init", "-q")
        self.write("GUIDE.md", OLD_MD)
        self.write("profilo.json", json.dumps(OLD_JSON, indent=2))
        self.write("gone.txt", "alpha\n\nbeta\n")
        self.write("keep.txt", "one\n-- a line that looks like a diff header\nthree\n")
        self.write("move-me.txt", "".join(f"line {i}\n" for i in range(20)))
        self.commit("old")
        self.git("tag", "v0.1.0")
        self.write("GUIDE.md", NEW_MD)
        self.write("profilo.json", json.dumps(NEW_JSON, indent=2))
        os.remove(os.path.join(self.repo, "gone.txt"))
        self.write("keep.txt", "one\nthree\nfour\n")
        os.rename(os.path.join(self.repo, "move-me.txt"), os.path.join(self.repo, "moved.txt"))
        self.write("NEW.md", "# Added\n")
        self.commit("new")
        cls.r = rd.report(cls.repo, "v0.1.0", "HEAD")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.repo, ignore_errors=True)

    @classmethod
    def git(self, *args):
        subprocess.run(["git", "-C", self.repo, "-c", "user.name=Test", "-c", "user.email=test@example.org",
                        "-c", "commit.gpgsign=false", "-c", "core.hooksPath=" + os.devnull, "-c", "tag.gpgsign=false", "-c", "init.defaultBranch=main"]
                       + list(args), check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @classmethod
    def write(self, name, text):
        with open(os.path.join(self.repo, name), "w", encoding="utf-8") as f:
            f.write(text)

    @classmethod
    def commit(self, msg):
        self.git("add", "-A")
        self.git("commit", "-q", "-m", msg)

    def test_files(self):
        self.assertEqual(self.r["added"], ["NEW.md"])
        self.assertEqual(self.r["removed"], ["gone.txt"])
        self.assertEqual([(x["from"], x["to"]) for x in self.r["renamed"]], [("move-me.txt", "moved.txt")])
        mod = {x["path"]: (x["lines_added"], x["lines_removed"]) for x in self.r["modified"]}
        self.assertEqual(mod["keep.txt"], (1, 1))
        self.assertIn("GUIDE.md", mod)
        self.assertIn("profilo.json", mod)

    def test_headings(self):
        self.assertEqual(self.r["headings_renamed"],
                         [{"path": "GUIDE.md", "from": "## Old section", "to": "## New section"}])
        self.assertEqual(self.r["headings_removed"], [])  # the fenced "# not a heading" is ignored

    def test_rfc2119_counts(self):
        g = next(x for x in self.r["rfc2119"] if x["path"] == "GUIDE.md")
        self.assertEqual(g["before"], {"MUST NOT": 1, "MUST": 1, "SHOULD NOT": 0, "SHOULD": 1, "MAY": 1})
        self.assertEqual(g["after"], {"MUST NOT": 0, "MUST": 1, "SHOULD NOT": 1, "SHOULD": 1, "MAY": 0})
        self.assertTrue(g["changed"])

    def test_json_keys(self):
        keys = [x["key"] for x in self.r["json_keys_removed"] if x["path"] == "profilo.json"]
        self.assertEqual(keys, ["catalogo[].note", "fasi"])

    def test_removed_lines(self):
        lines = {(x["path"], x["line"], x["text"]) for x in self.r["removed_lines"]["lines"]}
        self.assertIn(("gone.txt", 1, "alpha"), lines)
        self.assertIn(("gone.txt", 3, "beta"), lines)
        self.assertIn(("keep.txt", 2, "-- a line that looks like a diff header"), lines)
        self.assertIn(("GUIDE.md", 8, "## Old section"), lines)
        self.assertFalse(any(x[0] == "gone.txt" and x[1] == 2 for x in lines), "blank lines are not listed")
        self.assertFalse(any(x[0] in ("move-me.txt", "moved.txt") for x in lines), "a pure rename removes no line")

    def test_cap(self):
        r = rd.report(self.repo, "v0.1.0", "HEAD", max_lines=2)
        self.assertEqual(r["removed_lines"]["shown"], 2)
        self.assertGreater(r["removed_lines"]["total"], 2)

    def test_cli_json_and_exit_code(self):
        p = subprocess.run([sys.executable, "-I", TOOL, self.repo, "v0.1.0", "HEAD", "--json"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(json.loads(p.stdout)["removed"], ["gone.txt"])

    def test_cli_text_and_same_ref(self):
        p = subprocess.run([sys.executable, "-I", TOOL, self.repo, "HEAD", "HEAD"], stdout=subprocess.PIPE)
        self.assertEqual(p.returncode, 0)
        self.assertIn(b"Removed non-blank lines (total 0, shown 0)", p.stdout)

    def test_unknown_ref(self):
        p = subprocess.run([sys.executable, "-I", TOOL, self.repo, "v9.9.9", "HEAD"],
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.assertEqual(p.returncode, 2)
        self.assertIn(b"cannot produce the report", p.stderr)

    def test_version(self):
        p = subprocess.run([sys.executable, "-I", TOOL, "--version"], stdout=subprocess.PIPE)
        self.assertEqual(p.stdout.decode().strip(), "release_diff.py " + rd.__version__)


class UnitTest(unittest.TestCase):
    def test_heading_parse(self):
        self.assertEqual(rd.headings("## A ##\n#NoSpace\n   ### B\n"), [(2, "A"), (3, "B")])

    def test_keywords_case(self):
        self.assertEqual(rd.keyword_counts("must may MUST\nNOT")["MUST NOT"], 1)
        self.assertEqual(rd.keyword_counts("must may")["MAY"], 0)


if __name__ == "__main__":
    unittest.main()
