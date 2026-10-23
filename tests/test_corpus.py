"""Read-only checks against real trees [corpus-tests]: `pytest -m corpus`.

Each tree is skipped when absent.  Nothing here writes: names are resolved
in-process through `block`'s own `resolve_entry`, so the spans checked are
the spans the CLI would write through.

- NDTHT's `t/`: about 450 theories, the first consumer's tree.
- The AFP entries that declare `keywords`: where a session's keyword table
  changes what an entry's span is, and where shared lines occur.
"""
from __future__ import annotations

import io
from contextlib import redirect_stdout
from pathlib import Path

import pytest

from isabelle_block import cli

pytestmark = pytest.mark.corpus

NDTHT = Path.home() / "projects" / "ndtht" / "t"
AFP = Path.home() / "repos" / "afp" / "thys"


def _afp_keyword_theories() -> list[Path]:
    if not AFP.is_dir():
        return []
    entries = sorted({p.parent for p in AFP.glob("*/*.thy")
                      if any(l.lstrip().startswith("keywords ")
                             for l in p.read_text(errors="replace").splitlines())})
    return [p for d in entries for p in sorted(d.rglob("*.thy"))]


TREES = {
    "ndtht": lambda: sorted(NDTHT.rglob("*.thy")) if NDTHT.is_dir() else [],
    "afp-keywords": _afp_keyword_theories,
}


@pytest.mark.parametrize("tree", list(TREES))
def test_every_name_resolves_inside_its_entry_or_is_refused_for_a_reason(tree):
    files = TREES[tree]()
    if not files:
        pytest.skip(f"{tree}: tree absent")
    cli._ROOT = None
    resolved = refused = 0
    bad: list[str] = []
    for p in files:
        cli._SECTIONS.clear()
        n_lines = len(p.read_text(errors="replace").splitlines())
        entries = cli._entries(p)
        placed = [e for e in entries if e.thy_line]
        count: dict[str, int] = {}
        for e in placed:
            count[e.name] = count.get(e.name, 0) + 1
        for i, e in enumerate(placed):
            if count[e.name] != 1:
                continue
            out = io.StringIO()
            try:
                with redirect_stdout(out):
                    lo, hi = cli.resolve_entry(p, e.name)
            except SystemExit:
                refused += 1
                if not any(why in out.getvalue() for why in (
                        "shares a line", "where the next declaration starts")):
                    bad.append(f"{p}:{e.name}: refused: {out.getvalue().strip()}")
                continue
            resolved += 1
            if not (1 <= lo <= e.thy_line <= hi <= n_lines):
                bad.append(f"{p}:{e.name}: {lo}..{hi} does not hold its "
                           f"declaration line {e.thy_line} ({n_lines} lines)")
            nxt = next((n for n in placed[i + 1:] if n.thy_line > e.thy_line), None)
            if nxt is not None:
                start = nxt.preamble[0] if nxt.preamble else nxt.thy_line
                if hi >= start:
                    bad.append(f"{p}:{e.name}: {lo}..{hi} reaches {nxt.name!r}, "
                               f"which starts at {start}")
    assert resolved, f"{tree}: nothing resolved"
    assert not bad, f"{len(bad)} of {resolved + refused}:\n" + "\n".join(bad[:20])
