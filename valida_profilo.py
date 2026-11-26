#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 Paolo Ungari and contributors
"""Valida una cartella di Role Profile Eiraman: due file, sezioni e campi obbligatori, divieti.
Uso: python3 valida_profilo.py <cartella> [<cartella> ...]   Esce con 1 se un profilo non passa.
I termini vietati specifici (organizzazioni, strumenti interni) stanno nel file locale .eiraman-deny.local,
escluso da Git: un'espressione regolare per riga, righe con # ignorate. Il file si cerca nella cartella
corrente, risalendo dalla cartella dello strumento fino alla radice del repository e nel percorso indicato
dalla variabile EIRAMAN_DENY_FILE. Se manca, restano attivi i soli pattern generici."""
import json, os, re, sys

__version__ = "0.3.1"

SEZIONI = ["Identità e scopo", "Competenze di base e metodologie", "Responsabilità", "Azioni consentite",
           "Azioni vietate", "Regole di comunicazione", "Repository documentale", "Limiti dichiarati",
           "Suite di qualificazione", "Catalogo dei task e Seniority Digitale"]
CAMPI = ["id", "nome", "versione", "metodo", "stato", "piramide", "fasi", "descrizione_breve", "competenze_fonti",
         "motori", "ragionamento", "seniority", "catalogo", "mode_role", "unit_cost", "strumenti_deterministici",
         "scritture_consentite", "do_riservati", "qualificazione"]
STATI_IT = ["bozza non qualificata", "qualificato"]
STATI_EN = ["draft", "qualified", "maintained", "suspended"]
STATI = STATI_IT + STATI_EN
# Lo stato si cerca solo nella riga di stato («Stato: …» o «Status: …»), non in tutto il testo.
RIGA_STATO = re.compile(r"\b(?:stato|status)\s*:\s*\**\s*(" + "|".join(map(re.escape, STATI)) + r")\s*\**(?![\w-])",
                        re.I)
VIETATI_GENERICI = [(r"/Users/|[A-Za-z]:\\\\|OneDrive", "percorso locale"),
                    (r"\b(api[_-]?key|secret|password|token)\s*[:=]\s*\S{6,}", "possibile credenziale"),
                    (r"-----BEGIN [A-Z ]*PRIVATE KEY", "chiave privata")]
DENY_NAME = ".eiraman-deny.local"
DENY_LABEL = "riferimento a cliente, datore di lavoro o strumento interno"

def deny_files():
    """Percorsi dei file locali di termini vietati presenti, senza duplicati."""
    cand = [os.environ.get("EIRAMAN_DENY_FILE"), os.path.join(os.getcwd(), DENY_NAME)]
    d = os.path.dirname(os.path.abspath(__file__))
    while True:
        cand.append(os.path.join(d, DENY_NAME))
        if os.path.exists(os.path.join(d, ".git")) or os.path.isfile(os.path.join(d, DENY_NAME)): break
        up = os.path.dirname(d)
        if up == d: break
        d = up
    out, seen = [], set()
    for f in cand:
        if f and os.path.isfile(f) and os.path.realpath(f) not in seen:
            seen.add(os.path.realpath(f)); out.append(f)
    return out

def load_deny(paths=None):
    """Espressioni del file locale: una per riga; righe vuote e commenti con # ignorati."""
    rx = []
    for f in (deny_files() if paths is None else paths):
        with open(f, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line and not line.startswith("#"): rx.append((line, DENY_LABEL))
    return rx

def vietati():
    return VIETATI_GENERICI + load_deny()

def stato_presente(t):
    """Vero solo se una riga di stato del profilo dichiara uno stato ammesso."""
    return bool(RIGA_STATO.search(t))

def check(d):
    err = []
    md, js = os.path.join(d, "PROFILO.md"), os.path.join(d, "profilo.json")
    for f in (md, js):
        if not os.path.isfile(f): err.append(f"manca {os.path.basename(f)}")
    if err: return err
    t = open(md, encoding="utf-8").read()
    heads = re.findall(r"^##\s+\d+\.\s+(.+?)\s*$", t, re.M)
    for i, s in enumerate(SEZIONI):
        if s not in heads: err.append(f"PROFILO.md: manca la sezione «{s}»")
    if heads[:len(SEZIONI)] != SEZIONI and not err: err.append("PROFILO.md: sezioni fuori ordine")
    if not stato_presente(t): err.append("PROFILO.md: stato mancante")
    for m in re.finditer(r"^##\s+\d+\.\s+(.+?)\s*$\n(.*?)(?=^##\s|\Z)", t, re.M | re.S):
        if len(m.group(2).strip()) < 40: err.append(f"PROFILO.md: sezione «{m.group(1)}» vuota o troppo breve")
    n_casi = len(re.findall(r"^\s*(?:\d+\.|-|\|)\s*\**(?:Caso|Q)\s*\d", t.split("Suite di qualificazione")[-1].split("Catalogo dei task e Seniority Digitale")[0], re.M | re.I))
    if n_casi < 5: err.append(f"PROFILO.md: la suite ha {n_casi} casi, servono almeno 5 (righe «Caso N» o «QN»)")
    try:
        p = json.load(open(js, encoding="utf-8"))
    except Exception as ex:
        return err + [f"profilo.json non valido: {ex}"]
    for c in CAMPI:
        if c not in p or p[c] in (None, "", [], {}): err.append(f"profilo.json: campo «{c}» mancante o vuoto")
    if p.get("stato") and str(p["stato"]).strip().lower() not in STATI:
        err.append(f"profilo.json: stato «{p.get('stato')}» non ammesso")
    if p.get("id") and p["id"] != os.path.basename(os.path.normpath(d)).lower():
        err.append(f"profilo.json: id «{p.get('id')}» diverso dal nome della cartella")
    for m in p.get("motori", []):
        if m.get("tipo") == "locale" and not m.get("minimo"): err.append(f"profilo.json: motore locale «{m.get('motore')}» senza taglia minima")
    noti = {m.get("motore") for m in p.get("motori", [])}
    LIV = {"SD1", "SD2", "SD3", "SD4", "SD5"}
    ids = [c.get("id") for c in p.get("catalogo", [])]
    if len(ids) != len(set(ids)): err.append("profilo.json: ID duplicati nel catalogo")
    if len(ids) < 4: err.append(f"profilo.json: il catalogo ha {len(ids)} task, ne servono almeno 4")
    for c in p.get("catalogo", []):
        if c.get("seniority") not in LIV: err.append(f"profilo.json: task «{c.get('id')}» con livello non valido «{c.get('seniority')}»")
        if not c.get("task") or not c.get("deliverable"): err.append(f"profilo.json: task «{c.get('id')}» senza descrizione o deliverable")
    s = p.get("seniority") or {}
    if s.get("minima") not in LIV or s.get("massima") not in LIV: err.append("profilo.json: seniority minima/massima non valide")
    sez10 = t.split("Catalogo dei task e Seniority Digitale")[-1]
    m10 = re.search(r"<!-- catalogo:inizio -->\n(.*?)\n<!-- catalogo:fine -->", sez10, re.S)
    if not m10: err.append("PROFILO.md: sezione 10 senza tabella generata (eseguire attiva_profilo.py --scrivi-catalogo)")
    else:
        try:
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            import attiva_profilo
            if m10.group(1) != attiva_profilo.tabella(p):
                err.append("PROFILO.md: la sezione 10 non corrisponde al catalogo di profilo.json o alla mappa: rigenerarla con attiva_profilo.py --scrivi-catalogo")
        except Exception as ex:
            err.append(f"PROFILO.md: impossibile confrontare la sezione 10 ({ex.__class__.__name__})")
    for u in p.get("unit_cost", []):
        if u.get("motore") not in noti: err.append(f"profilo.json: Unit Cost per motore non dichiarato «{u.get('motore')}»")
    for f in p.get("competenze_fonti", []):
        if not f.get("riferimento"): err.append(f"profilo.json: fonte «{f.get('fonte')}» senza riferimento puntuale")
    regole = vietati()
    for name in (md, js):
        txt = open(name, encoding="utf-8").read()
        for rx, what in regole:
            for mm in re.finditer(rx, txt):
                err.append(f"{os.path.basename(name)}: {what}: «{mm.group(0)}»")
    return err

def main():
    if sys.argv[1:] == ["--version"]:
        print(f"valida_profilo.py {__version__}"); sys.exit(0)
    bad = 0
    for d in sys.argv[1:] or ["."]:
        e = check(d)
        print(("OK   " if not e else "NO   ") + d)
        for x in e: print("     - " + x)
        bad += bool(e)
    sys.exit(1 if bad else 0)

if __name__ == "__main__":
    main()
