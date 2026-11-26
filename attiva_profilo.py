#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Paolo Ungari and contributors
"""Seniority Digitale dei Role Profile Eiraman.

Scrive la sezione 10 (catalogo) di PROFILO.md:
    python3 attiva_profilo.py --scrivi-catalogo <cartella> [<cartella> ...]
Produce il file di attivazione di un profilo a un livello:
    python3 attiva_profilo.py <cartella> <SD1..SD5> --strumento claude|codex|copilot [--out <cartella>]
Senza --out stampa il contenuto. La mappa livello -> configurazione è _seniority/seniority.json.

Ripiego dei task fuori catalogo. Il campo `fallback` della mappa è il livello di ripiego. Se la mappa dichiara
anche `fallback_indicativo: true`, il livello è un valore indicativo e lo fissa il mandato del progetto; se
dichiara `fallback_eccezione` ({"livello": "SDn", "compiti": "..."}), i task fuori catalogo di quel tipo partono
dal livello dell'eccezione, che è indicativo anch'esso quando lo è il ripiego. Il livello dell'eccezione deve
essere più alto del ripiego. Senza questi due campi il testo generato è quello delle versioni precedenti."""
import json, os, re, sys

__version__ = "0.3.1"
if __name__ == "__main__" and sys.argv[1:] == ["--version"]:  # before the Seniority map is read
    print(f"attiva_profilo.py {__version__}"); sys.exit(0)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SEN = json.load(open(os.path.join(BASE, "_seniority", "seniority.json"), encoding="utf-8"))
LIV = {l["id"]: l for l in SEN["livelli"]}
START, END = "<!-- catalogo:inizio -->", "<!-- catalogo:fine -->"

class MappaNonValida(ValueError):
    """La mappa della Seniority Digitale ha un campo di ripiego non valido."""

def cfg(lv):
    l = LIV[lv]
    return (f"`{l['claude']['model']}` · `{l['claude']['effort']}`",
            f"`{l['codex']['model']}` · `{l['codex']['model_reasoning_effort']}`",
            l["copilot"]["model"])

def cell(x):
    return str(x or "").replace("|", "\\|").replace("\n", " ")

def tabella(p):
    righe = ["| ID | Task | Deliverable | Livello | Claude Code (model · effort) | Codex (model · reasoning) | GitHub Copilot (model) |",
             "|---|---|---|---|---|---|---|"]
    for t in p["catalogo"]:
        c = cfg(t["seniority"])
        righe.append(f"| {cell(t['id'])} | {cell(t['task'])} | {cell(t.get('deliverable'))} | {t['seniority']} {LIV[t['seniority']]['nome']} | {c[0]} | {c[1]} | {c[2]} |")
    fb = SEN["fallback"]; c = cfg(fb)
    ind, ecc = SEN.get("fallback_indicativo"), SEN.get("fallback_eccezione")
    if ind not in (None, True, False):
        raise MappaNonValida("seniority.json: `fallback_indicativo` deve essere true o false")
    ind = ind is True
    if ecc is not None:
        if not isinstance(ecc, dict) or ecc.get("livello") not in LIV or not str(ecc.get("compiti") or "").strip():
            raise MappaNonValida("seniority.json: `fallback_eccezione` richiede `livello` (un livello della mappa) e `compiti` (testo)")
        ids = [l["id"] for l in SEN["livelli"]]
        if ids.index(ecc["livello"]) <= ids.index(fb):
            raise MappaNonValida("seniority.json: il livello di `fallback_eccezione` deve essere più alto di `fallback`")
    if not ind and not ecc:  # mappa senza i campi nuovi: testo delle versioni precedenti
        righe.append(f"| — | Qualsiasi task fuori catalogo | — | {fb} {LIV[fb]['nome']} (ripiego) | {c[0]} | {c[1]} | {c[2]} |")
        frase = f"Un task fuori catalogo si esegue a **{fb}**. "
    else:
        nota = "ripiego indicativo, lo fissa il mandato" if ind else "ripiego"
        frase = (f"Un task fuori catalogo si esegue al livello di ripiego fissato nel mandato (valore indicativo **{fb}**)"
                 if ind else f"Un task fuori catalogo si esegue a **{fb}**")
        if ecc:
            fe = ecc["livello"]; ce = cfg(fe); comp = cell(ecc["compiti"])
            righe.append(f"| — | Task fuori catalogo, salvo l'eccezione della riga seguente | — | {fb} {LIV[fb]['nome']} ({nota}) | {c[0]} | {c[1]} | {c[2]} |")
            nota_e = "ripiego indicativo, eccezione" if ind else "ripiego, eccezione"
            righe.append(f"| — | Task fuori catalogo che per natura è di livello {LIV[fe]['nome']}: {comp} | — | {fe} {LIV[fe]['nome']} ({nota_e}) | {ce[0]} | {ce[1]} | {ce[2]} |")
            frase += (f"; i task fuori catalogo che per natura sono di livello {LIV[fe]['nome']} ({comp}) partono da **{fe}**"
                      + (", valore indicativo anch'esso" if ind else ""))
        else:
            righe.append(f"| — | Qualsiasi task fuori catalogo | — | {fb} {LIV[fb]['nome']} ({nota}) | {c[0]} | {c[1]} | {c[2]} |")
        frase += ". "
    s = p.get("seniority", {})
    testa = (f"Livello tipico del ruolo: da **{s.get('minima','?')}** a **{s.get('massima','?')}**. "
             f"Il Coordinatore AI attiva l'agente con la configurazione della riga; nella squadra l'agente lavora al livello più alto "
             f"tra quelli dei suoi task nel Work Package. {frase}"
             f"Configurazioni dalla mappa `_seniority/seniority.json` (versione {SEN['versione']}), da riverificare a ogni cambio di modello.")
    return testa + "\n\n" + "\n".join(righe)

def scrivi_catalogo(d):
    p = json.load(open(os.path.join(d, "profilo.json"), encoding="utf-8"))
    md = os.path.join(d, "PROFILO.md"); t = open(md, encoding="utf-8").read()
    blocco = f"{START}\n{tabella(p)}\n{END}"
    if START in t and END in t:
        t = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: blocco, t, flags=re.S)
    else:
        t = t.rstrip("\n") + f"\n\n## 10. Catalogo dei task e Seniority Digitale\n{blocco}\n"
    open(md, "w", encoding="utf-8").write(t)

def istruzioni(d):
    parti = []
    fam = os.path.join(os.path.dirname(os.path.normpath(d)), "FAMIGLIA.md")
    if os.path.isfile(fam): parti.append(open(fam, encoding="utf-8").read())
    parti.append(open(os.path.join(d, "PROFILO.md"), encoding="utf-8").read())
    return "\n\n---\n\n".join(parti)

def attiva(d, lv, strumento):
    p = json.load(open(os.path.join(d, "profilo.json"), encoding="utf-8")); l = LIV[lv]
    desc = p["descrizione_breve"].replace('"', "'")
    if strumento == "claude":
        return (f"{p['id']}.md", f'---\nname: {p["id"]}\ndescription: "{desc}"\nmodel: {l["claude"]["model"]}\neffort: {l["claude"]["effort"]}\n---\n\n'
                f"<!-- Eiraman · Seniority Digitale {lv} {l['nome']} -->\n\n" + istruzioni(d))
    if strumento == "codex":
        return (f"{p['id']}-{lv.lower()}.config.toml",
                f'# Eiraman · {p["nome"]} · Seniority Digitale {lv} {l["nome"]}\n# Salva come ~/.codex/{p["id"]}-{lv.lower()}.config.toml e avvia con: codex --profile {p["id"]}-{lv.lower()}\n'
                f'# Le istruzioni di ruolo (FAMIGLIA.md e PROFILO.md) vanno in AGENTS.md della cartella di lavoro.\n'
                f'model = "{l["codex"]["model"]}"\nmodel_reasoning_effort = "{l["codex"]["model_reasoning_effort"]}"\n')
    if strumento == "copilot":
        return (f"{p['id']}.agent.md", f'---\nname: {p["id"]}\ndescription: "{desc}"\nmodel: {l["copilot"]["model"]}\n---\n\n'
                f"<!-- Eiraman · Seniority Digitale {lv} {l['nome']}. Nome del modello: da verificare nella documentazione di Copilot. -->\n\n" + istruzioni(d))
    sys.exit("strumento: claude, codex o copilot")

def main(a):
    if a and a[0] == "--scrivi-catalogo":
        for d in a[1:]:
            try: scrivi_catalogo(d)
            except MappaNonValida as ex: sys.exit(str(ex))
            print("catalogo scritto:", d)
        return
    if len(a) < 4 or a[2] != "--strumento" or a[1] not in LIV:
        sys.exit(__doc__)
    if a[1] == "SD5" and "--motivo" not in a:
        sys.exit("SD5 si usa per eccezione: indica --motivo \"...\" e registralo nel registro del progetto (spec §4 bis).")
    p_ = json.load(open(os.path.join(a[0], "profilo.json"), encoding="utf-8"))
    if a[1] not in [u.get("livello") for u in p_.get("unit_cost", [])]:
        print(f"Attenzione: il profilo non ha uno Unit Cost per {a[1]}; registra il costo come «sconosciuto».", file=sys.stderr)
    nome, testo = attiva(a[0], a[1], a[3])
    if "--out" in a:
        out = a[a.index("--out") + 1]; os.makedirs(out, exist_ok=True)
        open(os.path.join(out, nome), "w", encoding="utf-8").write(testo); print(os.path.join(out, nome))
    else:
        print(testo)

if __name__ == "__main__":
    main(sys.argv[1:])
