#!/usr/bin/env python3
"""Generate the whole-identifier map for the ktm rename (Andras, 2026-10-04).

MAT's core names coincided with Dalvit and Thiemann's Multitape_To_Singletape_TM
(mttm, mt_config, dir, Q_tm, ...), so an entry importing both would see two of
each.  The scheme:

  *mttm*        -> *ktm*        (MTTM -> KTM)
  mt_*          -> ktc_*        (the configuration family)
  X_tm          -> X_ktm        for the ten machine selectors, as a name component
  dir           -> move         the type, go_dir* and finite_UNIV_dir only
  Config\\<^sub>M -> KConfig
  relpow_mono   -> relpow_subset_mono   (TM_Common has a relpow_mono too)

The constructors R / L / N are NOT in this map: bare one-letter tokens are
also variables, so they are renamed separately (phase 2).

Prints "OLD NEW" lines for every identifier in the .thy files under t/ that a
rule changes, for bin/rename-thy-names.py.

Usage: bin/ktm-rename-map.py > scratch/rename-ktm.map
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SYM = (r"\\<(?:alpha|beta|gamma|delta|epsilon|sigma|tau|Gamma|Delta|Sigma"
       r"|Theta|Lambda|Pi|Phi|Psi|Omega)>")
# an identifier, allowing Isabelle letter symbols (\<Gamma>_tm) and \<^sub>
IDENT = re.compile(rf"(?:[A-Za-z]|{SYM})(?:[A-Za-z0-9_']|{SYM}|\\<\^sub>)*")
STEMS = r"(?:Q|Sigma|\\<Gamma>|bl|le|delta|s|t|r|k)"
SEL = re.compile(rf"(?:(?<=_)|^){STEMS}_tm(?=_|$)")
DIR = re.compile(r"^(?:dir$|go_dir(?=_|$))")
# only the clashing direction names: the type (and its generated facts, which
# follow it as `dir.X`), go_dir and its lemma family, finite_UNIV_dir.  Names
# like enc_dir or flip_dir, where "dir" just abbreviates direction, stay.

FIXED = {"MTTM": "KTM", "Config\\<^sub>M": "KConfig",
         "finite_UNIV_dir": "finite_UNIV_move",
         "relpow_mono": "relpow_subset_mono"}


def rename(name: str) -> str:
    if name in FIXED:
        return FIXED[name]
    new = name.replace("mttm", "ktm")
    if new.startswith("mt_"):
        new = "ktc_" + new[3:]
    new = SEL.sub(lambda m: m.group(0)[:-3] + "_ktm", new)
    new = DIR.sub(lambda m: m.group(0).replace("dir", "move"), new)
    return new


def main() -> int:
    seen: set[str] = set()
    for p in sorted((REPO / "t").glob("*/*.thy")):
        seen.update(IDENT.findall(p.read_text()))
    out = sorted((n, rename(n)) for n in seen if rename(n) != n)
    news = [b for _, b in out]
    # `ktm` (a fact label in ART) and `move` (local variables) are term names;
    # a type of the same name does not collide with them
    clash = sorted(b for b in ({b for b in news if b in seen} | {b for b in news if news.count(b) > 1}) if b not in ("ktm", "move"))
    for a, b in out:
        print(f"{a}\t{b}")
    print(f"# {len(out)} identifiers", file=sys.stderr)
    if clash:
        print("FAIL: new names already present or duplicated: " + " ".join(clash), file=sys.stderr)
        return 1
    print("PASS: no new name collides with an existing identifier", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
