#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 Paolo Ungari and contributors
# SPDX-License-Identifier: Apache-2.0
"""Release diff report for Eiraman repositories (standard library only).

Usage:
    python3 release_diff.py <repo> <old-ref> <new-ref> [--json] [--max-lines N]

Compares two Git refs and reports what an independent scope reviewer has to map to a changelog
entry or to an approved decision (community/RELEASING.md, step 5):

  * files added, removed and renamed;
  * lines added and removed for each modified or renamed file;
  * Markdown headings removed or renamed;
  * per changed Markdown file, the counts of the RFC 2119 key words (MUST, MUST NOT, SHOULD,
    SHOULD NOT, MAY) before and after;
  * JSON keys removed from changed .json files (for example profilo.json);
  * removed non-blank lines, as old-path:line, capped by --max-lines (default 200).

The report is not a gate: when it is produced the exit code is 0, whatever it contains. The exit
code is 2 only when no report can be produced (not a Git repository, unknown ref)."""
import argparse, difflib, json, re, subprocess, sys

__version__ = "0.3.0"

KEYWORDS = [("MUST NOT", r"\bMUST\s+NOT\b"), ("MUST", r"\bMUST\b(?!\s+NOT\b)"),
            ("SHOULD NOT", r"\bSHOULD\s+NOT\b"), ("SHOULD", r"\bSHOULD\b(?!\s+NOT\b)"), ("MAY", r"\bMAY\b")]
HEADING = re.compile(r"^ {0,3}(#{1,6})[ \t]+(.*?)[ \t]*(?:[ \t]#+[ \t]*)?$")
FENCE = re.compile(r"^ {0,3}(```|~~~)")
HUNK = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


class GitError(Exception):
    pass


def git(repo, *args):
    """Runs git in repo with a fixed, unquoted path format and returns stdout as bytes."""
    cmd = ["git", "-C", repo, "-c", "core.quotepath=off", "--no-pager"] + list(args)
    p = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if p.returncode != 0:
        raise GitError(p.stderr.decode("utf-8", "replace").strip() or "git failed: " + " ".join(args))
    return p.stdout


def blob(repo, ref, path):
    """Text of path at ref, or None if it is missing or not UTF-8 text."""
    try:
        data = git(repo, "cat-file", "blob", f"{ref}:{path}")
    except GitError:
        return None
    if b"\0" in data:
        return None
    return data.decode("utf-8", "replace")


def name_status(repo, old, new):
    """List of (status, old_path, new_path); status is A, D, M, R, C or T."""
    parts = git(repo, "diff", "--name-status", "-M", "-z", old, new).decode("utf-8", "replace").split("\0")
    out, i = [], 0
    while i < len(parts) and parts[i]:
        st = parts[i]
        if st[0] in "RC":
            out.append((st[0], parts[i + 1], parts[i + 2], int(st[1:] or 0))); i += 3
        else:
            path = parts[i + 1]
            out.append((st[0], None if st[0] == "A" else path, None if st[0] == "D" else path, None)); i += 2
    return out


def numstat(repo, old, new):
    """{new_path or old_path: (added, removed)}; None for binary files."""
    parts = git(repo, "diff", "--numstat", "-M", "-z", old, new).decode("utf-8", "replace").split("\0")
    out, i = {}, 0
    while i < len(parts) and parts[i]:
        a, r, path = parts[i].split("\t", 2)
        if path == "":  # rename: the two paths follow
            path = parts[i + 2]; i += 3
        else:
            i += 1
        out[path] = None if a == "-" else (int(a), int(r))
    return out


def headings(text):
    """ATX headings outside fenced code, as (level, title)."""
    out, fence = [], None
    for line in (text or "").splitlines():
        m = FENCE.match(line)
        if m:
            fence = None if fence == m.group(1) else (fence or m.group(1))
            continue
        if fence:
            continue
        h = HEADING.match(line)
        if h:
            out.append((len(h.group(1)), h.group(2).strip()))
    return out


def heading_changes(old_text, new_text):
    """Removed headings and renamed ones (a heading replaced in place by another)."""
    a, b = headings(old_text), headings(new_text)
    removed, renamed = [], []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
        if op == "delete":
            removed += a[i1:i2]
        elif op == "replace":
            pairs = min(i2 - i1, j2 - j1)
            renamed += [(a[i1 + k], b[j1 + k]) for k in range(pairs)]
            removed += a[i1 + pairs:i2]
    fmt = lambda h: "#" * h[0] + " " + h[1]
    return [fmt(h) for h in removed], [(fmt(x), fmt(y)) for x, y in renamed]


def keyword_counts(text):
    text = text or ""
    return {k: len(re.findall(rx, text)) for k, rx in KEYWORDS}


def json_keys(text):
    """Set of key paths; list items are folded into '[]'."""
    def walk(o, prefix):
        if isinstance(o, dict):
            for k, v in o.items():
                p = f"{prefix}.{k}" if prefix else str(k)
                yield p
                yield from walk(v, p)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v, prefix + "[]")
    return set(walk(json.loads(text), ""))


def removed_lines(repo, old, new):
    """All removed non-blank lines as (old_path, old_line, text)."""
    raw = git(repo, "diff", "-U0", "-M", "--no-color", "--no-ext-diff", old, new).decode("utf-8", "replace")
    out, path, ln, header = [], None, 0, False
    for line in raw.split("\n"):
        if line.startswith("diff --git "):
            path, header = None, True
        elif header and line.startswith("--- "):
            p = line[4:].rstrip("\t")
            path = None if p == "/dev/null" else (p[2:] if p.startswith("a/") else p)
        elif header and not line.startswith("@@"):
            continue  # index, mode, rename and +++ lines
        elif line.startswith("@@"):
            header = False
            m = HUNK.match(line)
            ln = int(m.group(1)) if m else 0
        elif line.startswith("-") and path is not None:
            if line[1:].strip():
                out.append((path, ln, line[1:]))
            ln += 1
    return out


def report(repo, old, new, max_lines=200):
    for ref in (old, new):
        git(repo, "rev-parse", "--verify", "--quiet", ref + "^{commit}")
    changes = name_status(repo, old, new)
    stats = numstat(repo, old, new)
    r = {"tool": "release_diff", "version": __version__, "repo": repo,
         "old": {"ref": old, "commit": git(repo, "rev-parse", old + "^{commit}").decode().strip()},
         "new": {"ref": new, "commit": git(repo, "rev-parse", new + "^{commit}").decode().strip()},
         "added": [], "removed": [], "renamed": [], "modified": [],
         "headings_removed": [], "headings_renamed": [], "rfc2119": [], "json_keys_removed": [], "json_errors": [],
         "removed_lines": {"total": 0, "shown": 0, "lines": []}}
    for st, op, np, sim in changes:
        if st == "A":
            r["added"].append(np)
        elif st == "D":
            r["removed"].append(op)
        elif st in "RC":
            s = stats.get(np)
            r["renamed"].append({"from": op, "to": np, "similarity": sim, "kind": "copy" if st == "C" else "rename",
                                 "lines_added": s[0] if s else None, "lines_removed": s[1] if s else None})
        else:
            s = stats.get(np)
            r["modified"].append({"path": np, "lines_added": s[0] if s else None, "lines_removed": s[1] if s else None})
        if st == "A":
            continue
        old_text, new_text = blob(repo, old, op), (blob(repo, new, np) if np else None)
        if op.lower().endswith(".md") or (np or "").lower().endswith(".md"):
            rem, ren = heading_changes(old_text, new_text)
            r["headings_removed"] += [{"path": op, "heading": h} for h in rem]
            r["headings_renamed"] += [{"path": np or op, "from": x, "to": y} for x, y in ren]
            before, after = keyword_counts(old_text), keyword_counts(new_text)
            r["rfc2119"].append({"path": np or op, "before": before, "after": after,
                                 "changed": before != after})
        if op.lower().endswith(".json"):
            try:
                gone = json_keys(old_text or "{}") - (json_keys(new_text) if new_text is not None else set())
                r["json_keys_removed"] += [{"path": op, "key": k} for k in sorted(gone)]
            except ValueError as ex:
                r["json_errors"].append({"path": np or op, "error": str(ex)})
    lines = removed_lines(repo, old, new)
    r["removed_lines"] = {"total": len(lines), "shown": min(len(lines), max_lines),
                          "lines": [{"path": p, "line": n, "text": t} for p, n, t in lines[:max_lines]]}
    return r


def text_report(r):
    out = [f"release_diff {r['version']}: {r['repo']}",
           f"  old {r['old']['ref']} ({r['old']['commit'][:12]})  new {r['new']['ref']} ({r['new']['commit'][:12]})", ""]

    def section(title, items):
        out.append(f"{title}: {len(items)}")
        out.extend("  " + x for x in items)
        out.append("")
    section("Files added", r["added"])
    section("Files removed", r["removed"])
    section("Files renamed", [f"{x['from']} -> {x['to']} ({x['kind']}, {x['similarity']}%)" for x in r["renamed"]])
    section("Files modified (+added -removed lines)",
            [f"{x['path']}  " + ("binary" if x["lines_added"] is None else f"+{x['lines_added']} -{x['lines_removed']}")
             for x in r["modified"]])
    section("Markdown headings removed", [f"{x['path']}: {x['heading']}" for x in r["headings_removed"]])
    section("Markdown headings renamed", [f"{x['path']}: {x['from']}  =>  {x['to']}" for x in r["headings_renamed"]])
    fmt = lambda c: " ".join(f"{k}={v}" for k, v in c.items())
    section("RFC 2119 key words per changed Markdown file (before -> after)",
            [f"{x['path']}{'  CHANGED' if x['changed'] else ''}\n    before {fmt(x['before'])}\n    after  {fmt(x['after'])}"
             for x in r["rfc2119"]])
    section("JSON keys removed", [f"{x['path']}: {x['key']}" for x in r["json_keys_removed"]])
    if r["json_errors"]:
        section("JSON files not parsed", [f"{x['path']}: {x['error']}" for x in r["json_errors"]])
    rl = r["removed_lines"]
    section(f"Removed non-blank lines (total {rl['total']}, shown {rl['shown']})",
            [f"{x['path']}:{x['line']}: {x['text']}" for x in rl["lines"]])
    return "\n".join(out).rstrip() + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(prog="release_diff.py", description=__doc__.split("\n\n")[0])
    ap.add_argument("repo", help="path of the Git repository")
    ap.add_argument("old_ref", help="previous release (tag or commit)")
    ap.add_argument("new_ref", help="release candidate (tag, branch or commit)")
    ap.add_argument("--json", action="store_true", help="print the report as JSON")
    ap.add_argument("--max-lines", type=int, default=200, help="cap on the removed lines listed (default 200)")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    a = ap.parse_args(argv)
    try:
        r = report(a.repo, a.old_ref, a.new_ref, max(0, a.max_lines))
    except GitError as ex:
        print(f"release_diff: cannot produce the report: {ex}", file=sys.stderr)
        return 2
    sys.stdout.write(json.dumps(r, indent=2, ensure_ascii=False) + "\n" if a.json else text_report(r))
    return 0


if __name__ == "__main__":
    sys.exit(main())
