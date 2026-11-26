# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Paolo Ungari and contributors
"""Tests for valida_profilo.py (standard library only).

Run from this folder:  python3 -m unittest -v
The registry tests need the Role Profile registry. The default is a checkout of the
role-profiles repository next to the tools repository (../role-profiles from the tools folder);
set EIRAMAN_REGISTRY to use another path."""
import json, os, re, shutil, subprocess, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
REGISTRY = os.path.abspath(os.environ.get("EIRAMAN_REGISTRY")
                           or os.path.join(TOOLS, "..", "role-profiles"))
BASELINE = os.path.join(HERE, "baseline_registro.txt")
HAS_REGISTRY = os.path.isdir(os.path.join(REGISTRY, "_seniority"))
FAKE_TERM = "ZetaCorpInternalTool"


def baseline_dirs():
    return [l.split(None, 1)[1].strip() for l in read(BASELINE).splitlines() if l.startswith("OK ")]


class Sandbox:
    """A throwaway registry: tools in _strumenti, _seniority linked from the real registry, no deny file."""

    def __init__(self):
        self.root = tempfile.mkdtemp(prefix="eiraman-test-")
        self.reg = os.path.join(self.root, "reg")
        os.makedirs(os.path.join(self.reg, "_strumenti"))
        os.makedirs(os.path.join(self.reg, ".git"))  # stops the upward search for a deny file
        for f in ("valida_profilo.py", "attiva_profilo.py"):
            shutil.copy(os.path.join(TOOLS, f), os.path.join(self.reg, "_strumenti", f))
        os.symlink(os.path.join(REGISTRY, "_seniority"), os.path.join(self.reg, "_seniority"))

    def copy_profile(self, rel):
        dst = os.path.join(self.reg, "p", os.path.basename(rel))
        shutil.copytree(os.path.join(REGISTRY, rel), dst)
        return dst

    def run(self, dirs, deny_file=None, cwd=None):
        env = {k: v for k, v in os.environ.items() if k != "EIRAMAN_DENY_FILE"}
        if deny_file: env["EIRAMAN_DENY_FILE"] = deny_file
        r = subprocess.run([sys.executable, os.path.join(self.reg, "_strumenti", "valida_profilo.py")] + dirs,
                           cwd=cwd or self.root, env=env, capture_output=True, text=True)
        return r.returncode, r.stdout

    def close(self):
        shutil.rmtree(self.root, ignore_errors=True)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def edit(path, fn):
    write(path, fn(read(path)))


class UnitTests(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, TOOLS)
        import valida_profilo
        self.v = valida_profilo

    def test_english_states_recognised(self):
        for s in ("draft", "qualified", "maintained", "suspended"):
            self.assertTrue(self.v.stato_presente(f"Status: {s}."), s)

    def test_italian_states_still_recognised(self):
        self.assertTrue(self.v.stato_presente("Stato: bozza non qualificata"))
        self.assertTrue(self.v.stato_presente("Stato: qualificato"))
        self.assertFalse(self.v.stato_presente("Stato: undecided"))

    def test_state_only_from_status_line(self):
        # A state word elsewhere in the text does not count as the profile's status.
        self.assertFalse(self.v.stato_presente("The draft profile is not yet qualified by a reviewer."))
        self.assertFalse(self.v.stato_presente("Il task è qualificato solo dopo la revisione."))
        self.assertFalse(self.v.stato_presente("Stato: da qualificare"))
        self.assertTrue(self.v.stato_presente("Versione 0.1.0 · Stato: **bozza non qualificata**"))
        self.assertTrue(self.v.stato_presente("Status: **maintained**"))

    def test_deny_file_comments_and_blanks_ignored(self):
        with tempfile.NamedTemporaryFile("w", suffix=".local", delete=False, encoding="utf-8") as f:
            f.write("# comment\n\n\\bAlpha\\b\n  # indented comment\nBeta\n")
        try:
            self.assertEqual([r for r, _ in self.v.load_deny([f.name])], ["\\bAlpha\\b", "Beta"])
        finally:
            os.unlink(f.name)

    def test_generic_patterns_in_code(self):
        labels = {w for _, w in self.v.VIETATI_GENERICI}
        self.assertEqual(labels, {"percorso locale", "possibile credenziale", "chiave privata"})


@unittest.skipUnless(HAS_REGISTRY, f"registry not found at {REGISTRY}")
class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.sb = Sandbox()
        self.prof = baseline_dirs()[0]

    def tearDown(self):
        self.sb.close()

    def test_all_profiles_match_baseline(self):
        dirs = baseline_dirs()
        self.assertEqual(len(dirs), 47)
        code, out = self.sb.run(dirs, deny_file=os.environ.get("EIRAMAN_DENY_FILE"), cwd=REGISTRY)
        self.assertEqual(code, 0, out)
        self.assertEqual(out, read(BASELINE))

    def test_term_from_deny_file_is_rejected(self):
        d = self.sb.copy_profile(self.prof)
        edit(os.path.join(d, "PROFILO.md"), lambda t: t + f"\nUsed with {FAKE_TERM} in production.\n")
        code, out = self.sb.run([d])
        self.assertEqual(code, 0, out)  # without the deny file the term is unknown
        deny = os.path.join(self.sb.root, "deny.txt")
        write(deny, f"# test terms\n\\b{FAKE_TERM}\\b\n")
        code, out = self.sb.run([d], deny_file=deny)
        self.assertEqual(code, 1, out)
        self.assertIn("riferimento a cliente", out)

    def test_deny_file_found_in_current_directory(self):
        d = self.sb.copy_profile(self.prof)
        edit(os.path.join(d, "PROFILO.md"), lambda t: t + f"\nUsed with {FAKE_TERM}.\n")
        cwd = os.path.join(self.sb.root, "work")
        os.makedirs(cwd)
        write(os.path.join(cwd, ".eiraman-deny.local"), FAKE_TERM + "\n")
        code, out = self.sb.run([d], cwd=cwd)
        self.assertEqual(code, 1, out)

    def test_generic_patterns_without_deny_file(self):
        cases = {"possibile credenziale": "\npassword = s3cr3tvalue99\n",
                 "percorso locale": "\nSee /Users/someone/notes.\n",
                 "chiave privata": "\n-----BEGIN RSA PRIVATE KEY\n"}
        for label, extra in cases.items():
            with self.subTest(label=label):
                d = self.sb.copy_profile(self.prof)
                edit(os.path.join(d, "PROFILO.md"), lambda t: t + extra)
                code, out = self.sb.run([d])
                self.assertEqual(code, 1, out)
                self.assertIn(label, out)
                shutil.rmtree(d)

    def test_english_states_accepted(self):
        for s in ("draft", "qualified", "maintained", "suspended"):
            with self.subTest(state=s):
                d = self.sb.copy_profile(self.prof)
                md = os.path.join(d, "PROFILO.md")
                edit(md, lambda t: re.sub(r"bozza non qualificata|qualificato", s, t))
                t = read(md)
                self.assertNotIn("bozza non qualificata", t)
                self.assertNotIn("qualificato", t)
                js = os.path.join(d, "profilo.json")
                p = json.loads(read(js)); p["stato"] = s
                write(js, json.dumps(p, ensure_ascii=False, indent=2))
                code, out = self.sb.run([d])
                self.assertEqual(code, 0, out)
                shutil.rmtree(d)

    def test_state_word_outside_status_line_not_enough(self):
        d = self.sb.copy_profile(self.prof)
        md = os.path.join(d, "PROFILO.md")
        edit(md, lambda t: re.sub(r"Stato: \*\*bozza non qualificata\*\*", "Stato: **tbd**", t)
             + "\nA draft note: this profile is not qualified.\n")
        code, out = self.sb.run([d])
        self.assertEqual(code, 1, out)
        self.assertIn("stato mancante", out)

    def test_invalid_json_state_rejected(self):
        d = self.sb.copy_profile(self.prof)
        js = os.path.join(d, "profilo.json")
        p = json.loads(read(js)); p["stato"] = "approved"
        write(js, json.dumps(p, ensure_ascii=False, indent=2))
        code, out = self.sb.run([d])
        self.assertEqual(code, 1, out)
        self.assertIn("non ammesso", out)

    def test_missing_state_rejected(self):
        d = self.sb.copy_profile(self.prof)
        edit(os.path.join(d, "PROFILO.md"),
             lambda t: re.sub(r"bozza non qualificata|qualificato|\b(draft|qualified|maintained|suspended)\b", "tbd", t))
        code, out = self.sb.run([d])
        self.assertEqual(code, 1, out)
        self.assertIn("stato mancante", out)


@unittest.skipUnless(HAS_REGISTRY, f"registry not found at {REGISTRY}")
class FallbackTests(unittest.TestCase):
    """The generated catalogue follows the fallback fields of the Digital Seniority map."""

    def setUp(self):
        self.sb = Sandbox()
        os.unlink(os.path.join(self.sb.reg, "_seniority"))
        shutil.copytree(os.path.join(REGISTRY, "_seniority"), os.path.join(self.sb.reg, "_seniority"))
        self.map = os.path.join(self.sb.reg, "_seniority", "seniority.json")
        self.dst = self.sb.copy_profile(baseline_dirs()[0])

    def tearDown(self):
        self.sb.close()

    def run_generator(self, **fields):
        m = json.loads(read(self.map))
        for k in ("fallback_indicativo", "fallback_eccezione"): m.pop(k, None)
        m.update(fields)
        write(self.map, json.dumps(m, ensure_ascii=False))
        return subprocess.run([sys.executable, os.path.join(self.sb.reg, "_strumenti", "attiva_profilo.py"),
                               "--scrivi-catalogo", self.dst], capture_output=True, text=True)

    def generate(self, **fields):
        r = self.run_generator(**fields)
        self.assertEqual(r.returncode, 0, r.stderr)
        sec = read(os.path.join(self.dst, "PROFILO.md")).split("<!-- catalogo:inizio -->")[1]
        self.assertEqual(self.sb.run([self.dst])[0], 0)
        return sec

    def test_map_without_new_fields_keeps_the_previous_text(self):
        sec = self.generate(fallback="SD4")
        self.assertIn("Un task fuori catalogo si esegue a **SD4**. Configurazioni dalla mappa", sec)
        self.assertIn("| — | Qualsiasi task fuori catalogo | — | SD4 Lead (ripiego) |", sec)
        self.assertEqual(sec.count("fuori catalogo"), 2)

    def test_indicative_fallback_with_exception(self):
        sec = self.generate(fallback="SD3", fallback_indicativo=True,
                            fallback_eccezione={"livello": "SD4", "compiti": "architettura, sicurezza"})
        self.assertIn("al livello di ripiego fissato nel mandato (valore indicativo **SD3**); i task fuori catalogo "
                      "che per natura sono di livello Lead (architettura, sicurezza) partono da **SD4**, "
                      "valore indicativo anch'esso. ", sec)
        self.assertIn("| — | Task fuori catalogo, salvo l'eccezione della riga seguente | — | "
                      "SD3 Senior (ripiego indicativo, lo fissa il mandato) | `sonnet` · `high` |", sec)
        self.assertIn("| — | Task fuori catalogo che per natura è di livello Lead: architettura, sicurezza | — | "
                      "SD4 Lead (ripiego indicativo, eccezione) | `opus` · `high` |", sec)
        self.assertNotIn("Qualsiasi task fuori catalogo", sec)

    def test_fixed_fallback_with_exception(self):
        sec = self.generate(fallback="SD3", fallback_eccezione={"livello": "SD4", "compiti": "sicurezza"})
        self.assertIn("Un task fuori catalogo si esegue a **SD3**; i task fuori catalogo che per natura sono di "
                      "livello Lead (sicurezza) partono da **SD4**. Configurazioni", sec)
        self.assertIn("| SD3 Senior (ripiego) |", sec)
        self.assertIn("| SD4 Lead (ripiego, eccezione) |", sec)

    def test_malformed_map_is_refused_with_a_message(self):
        before = read(os.path.join(self.dst, "PROFILO.md"))
        for bad in ({"fallback_eccezione": {"livello": "SD4"}},
                    {"fallback_eccezione": {"livello": "SD9", "compiti": "x"}},
                    {"fallback_eccezione": {"livello": "SD2", "compiti": "x"}},
                    {"fallback_eccezione": "SD4"},
                    {"fallback_indicativo": "si"}):
            r = self.run_generator(fallback="SD3", **bad)
            self.assertNotEqual(r.returncode, 0, bad)
            self.assertIn("seniority.json:", r.stderr, bad)
            self.assertEqual(read(os.path.join(self.dst, "PROFILO.md")), before, bad)

    def test_indicative_fallback_without_exception(self):
        sec = self.generate(fallback="SD3", fallback_indicativo=True)
        self.assertIn("(valore indicativo **SD3**). Configurazioni", sec)
        self.assertIn("| — | Qualsiasi task fuori catalogo | — | SD3 Senior (ripiego indicativo, lo fissa il mandato) |", sec)


if __name__ == "__main__":
    unittest.main()
