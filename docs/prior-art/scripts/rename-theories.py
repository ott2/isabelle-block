#!/usr/bin/env python3
"""Rename Isabelle theories within a session directory, updating every
textual reference by *word-boundary* match.

    bin/rename-theories.py --dir t/ae OLD1=NEW1 OLD2=NEW2 ...

For each OLD=NEW whose <dir>/OLD.thy exists, `git mv` it to <dir>/NEW.thy,
then apply \\bOLD\\b -> NEW across every *.thy (excluding output/), the ROOT,
and document/*.tex under <dir>.  Word boundaries prevent prefix collisions
(EncodingWrap_Plant must not match inside EncodingWrap_PlantReset), and catch
`theory`/`imports` declarations, `@{theory Sess.OLD}` antiquotations, and
`\\<open>OLD\\<close>` prose cartouches alike (`.`, `>`, `}` are all non-word).

No NEW may contain any OLD as a substring, so the per-file replacements are
order-independent (single pass, each pair applied once).
"""
import os
import re
import subprocess
import sys


def main():
    args = sys.argv[1:]
    if len(args) < 3 or args[0] != "--dir":
        sys.exit("usage: rename-theories.py --dir DIR OLD=NEW [OLD=NEW ...]")
    d = args[1]
    pairs = [tuple(a.split("=", 1)) for a in args[2:]]

    news = [n for _, n in pairs]
    for old, _ in pairs:
        for n in news:
            if old in n and old != n:
                sys.exit(f"unsafe: OLD {old!r} is a substring of NEW {n!r}")

    # 1. git mv each existing OLD.thy -> NEW.thy
    for old, new in pairs:
        src = os.path.join(d, old + ".thy")
        dst = os.path.join(d, new + ".thy")
        if os.path.exists(src):
            subprocess.run(["git", "mv", src, dst], check=True)
            print(f"moved {src} -> {dst}")

    # 2. collect target files (re-glob after the moves)
    targets = []
    for root, _dirs, files in os.walk(d):
        if "output" in root.split(os.sep):
            continue
        for f in files:
            if f.endswith(".thy") or f == "ROOT" or f.endswith(".tex"):
                targets.append(os.path.join(root, f))

    # 3. apply word-boundary replacements
    total = 0
    for path in sorted(targets):
        with open(path) as fh:
            text = fh.read()
        orig = text
        n = 0
        for old, new in pairs:
            text, cnt = re.subn(r"\b" + re.escape(old) + r"\b", new, text)
            n += cnt
        if text != orig:
            with open(path, "w") as fh:
                fh.write(text)
            print(f"  {path}: {n} replacement(s)")
            total += n
    print(f"PASS: {total} replacement(s) across {len(targets)} files")


if __name__ == "__main__":
    main()
