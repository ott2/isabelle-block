"""The contract in CLAUDE.md, case by case: a refusal writes nothing, a dry
run writes nothing, every run ends with PASS:/FAIL: (checked on every call
by the `run` fixture), the blank-seam rule, and the addressing rules that
make a NAME safe to write through.

`test_verbs.py` shows each verb doing its job once; this module is the part
a release promises.
"""
from __future__ import annotations

import re

import pytest

from conftest import EXTRA, FIXTURE, last_line

N0 = len(FIXTURE.splitlines())

# FIXTURE with a doc block on `beta`: the preamble a NAME span must not eat.
CLIP = FIXTURE.replace('lemma beta', 'text \\<open>beta doc\\<close>\n\nlemma beta')

KEYWORDS = FIXTURE.replace("  imports Main\n",
                           '  imports Main\n  keywords "foo" :: thy_decl\n')

DUPLICATE = FIXTURE.replace('lemma beta', 'lemma alpha')


def _landing(r) -> tuple[int, int]:
    """The `-> FILE[lo..hi]` range a move/copy reports for the landed block."""
    m = re.search(r"\[(\d+)\.\.(\d+)\](?: \(dry run\))?$", last_line(r.stdout))
    assert m, r.stdout
    return int(m.group(1)), int(m.group(2))


def _assert_one_blank_around(lines: list[str], lo: int, hi: int) -> None:
    """Lines lo..hi (1-based) sit between exactly one blank line on each
    side, or against the file's edge."""
    blank = [not l.strip() for l in lines]
    assert not blank[lo - 1] and not blank[hi - 1], (lo, hi)
    if lo > 1:
        assert blank[lo - 2] and lo > 2 and not blank[lo - 3], (lo, hi)
    if hi < len(lines):
        assert blank[hi] and hi + 1 < len(lines) and not blank[hi + 1], (lo, hi)


def _max_blank_run(lines: list[str]) -> int:
    best = cur = 0
    for l in lines:
        cur = cur + 1 if not l.strip() else 0
        best = max(best, cur)
    return best


# --- the blank-seam rule ------------------------------------------------------

@pytest.mark.parametrize("region, dest", [
    ("16..17", "10"),     # upward, block with no blank of its own
    ("7..9", "16"),       # downward, block carrying its trailing blank
    ("7..8", "14"),       # into the double blank above a subsection
    ("10..11", "1"),      # to the top of the file
    ("7..8", "19"),       # just before `end`
])
def test_move_lands_between_single_blanks(thy, run, region, dest):
    p = thy()
    r = run("move", f"{p}:{region}", "before", dest)
    lines = p.read_text().splitlines()
    lo, hi = _landing(r)
    _assert_one_blank_around(lines, lo, hi)
    # healing collapses blank runs, it never creates a longer one
    assert _max_blank_run(lines) <= _max_blank_run(FIXTURE.splitlines())


def test_copy_grows_by_the_block(thy, run):
    p = thy()
    r = run("copy", f"{p}:7..9", "before", "16")
    lines = p.read_text().splitlines()
    assert len(lines) == N0 + 3
    _assert_one_blank_around(lines, *_landing(r))


def test_no_trailing_blank_moves_verbatim(thy, run):
    p = thy()
    run("move", f"{p}:7..9", "before", "16", "--no-trailing-blank")
    lines = p.read_text().splitlines(keepends=True)
    assert len(lines) == N0
    assert "".join(lines).count("\n\n\n") == FIXTURE.count("\n\n\n")


# --- move between files -------------------------------------------------------

def test_move_between_theories_by_name(thy, run):
    a, b = thy(), thy("Extra.thy", EXTRA)
    r = run("move", f"{a}:alpha", "before", f"{b}:delta")
    src, dst = a.read_text(), b.read_text()
    assert "lemma alpha" not in src and "A preamble" not in src
    assert "lemma alpha" in dst and "A preamble" in dst
    assert dst.index("A preamble") < dst.index("lemma alpha") < dst.index("lemma delta")
    _assert_one_blank_around(dst.splitlines(), *_landing(r))


def test_copy_between_theories_keeps_the_source(thy, run):
    a, b = thy(), thy("Extra.thy", EXTRA)
    run("copy", f"{a}:7..8", "before", f"{b}:5")
    assert a.read_text() == FIXTURE
    assert "lemma alpha" in b.read_text()


def test_move_into_its_own_span_refuses(thy, run, snapshot):
    p = thy()
    before = snapshot()
    r = run("move", f"{p}:7..9", "before", "8")
    assert r.returncode == 1 and snapshot() == before


def test_move_outside_the_destination_refuses(thy, run, snapshot):
    a, b = thy(), thy("Extra.thy", EXTRA)
    before = snapshot()
    r = run("move", f"{a}:7..8", "before", f"{b}:99")
    assert r.returncode == 1 and snapshot() == before


# --- addressing: what makes a NAME safe to write through ----------------------

def test_name_span_stops_above_the_next_entrys_preamble(thy, run):
    p = thy("Clip.thy", CLIP)
    out = run("emit", f"{p}:alpha").stdout
    assert "lemma alpha" in out and "beta doc" not in out


def test_delete_by_name_keeps_the_next_entrys_preamble(thy, run):
    p = thy("Clip.thy", CLIP)
    run("delete", f"{p}:alpha")
    txt = p.read_text()
    assert "lemma alpha" not in txt
    assert "beta doc" in txt and "lemma beta" in txt


def test_name_addressing_refuses_a_theory_declaring_keywords(thy, run, snapshot):
    p = thy("Kw.thy", KEYWORDS)
    before = snapshot()
    r = run("delete", f"{p}:alpha")
    assert r.returncode == 1 and "keywords" in r.stdout
    assert snapshot() == before
    # spans never touch the parser, so they still work there
    assert run("emit", f"{p}:8..9").returncode == 0


def test_a_duplicated_name_refuses(thy, run, snapshot):
    p = thy("Dup.thy", DUPLICATE)
    before = snapshot()
    r = run("delete", f"{p}:alpha")
    assert r.returncode == 1 and snapshot() == before


@pytest.mark.parametrize("region", ["7-9", "7 .. 9"])
def test_span_spellings_agree(thy, run, region):
    p = thy()
    assert run("emit", f"{p}:{region}").stdout == run("emit", f"{p}:7..9").stdout


def test_all_is_the_bare_file(thy, run):
    p = thy()
    assert (run("sub", "by simp", "by auto", f"{p}:all", "--dry-run").stdout
            == run("sub", "by simp", "by auto", p, "--dry-run").stdout)


@pytest.mark.parametrize("region", ["7..99", "9..7", "0..3", "0"])
def test_a_bad_span_refuses(thy, run, snapshot, region):
    p = thy()
    before = snapshot()
    r = run("delete", f"{p}:{region}")
    assert r.returncode == 1 and snapshot() == before


def test_a_missing_file_refuses(tmp_path, run):
    assert run("emit", tmp_path / "Nowhere.thy").returncode == 1


# --- a refusal writes nothing, across every file of the run -------------------

@pytest.mark.parametrize("verb, pat", [
    ("sub", "by simp"), ("resub", r"by simp"), ("reargs", "simp $1"),
])
def test_rewrite_over_two_files_refused_by_expect_writes_neither(
        thy, run, snapshot, verb, pat):
    a, b = thy(), thy("Extra.thy", EXTRA)
    before = snapshot()
    r = run(verb, pat, "by auto", a, b, "--expect", "1")
    assert r.returncode == 1 and snapshot() == before


def test_rewrite_naming_a_missing_file_writes_nothing(thy, run, snapshot, tmp_path):
    a = thy()
    before = snapshot()
    r = run("sub", "by simp", "by auto", a, tmp_path / "Nowhere.thy")
    assert r.returncode == 1 and snapshot() == before


def test_resub_refuses_overlapping_regions(thy, run, snapshot):
    p = thy()
    before = snapshot()
    r = run("resub", "by simp", "by auto", f"{p}:7..11", f"{p}:10..17")
    assert r.returncode == 1 and snapshot() == before


def test_resub_bad_pattern_refuses(thy, run):
    p = thy()
    r = run("resub", "(unclosed", "x", p)
    assert r.returncode == 1 and p.read_text() == FIXTURE


def test_split_refuses_overlapping_ranges_and_writes_no_part(thy, run, snapshot):
    p = thy()
    before = snapshot()
    r = run("split", p, "Part_A|Main|7..11", "Part_B|Main|10..17", "--cut")
    assert r.returncode == 1
    assert snapshot() == before


def test_split_refuses_a_range_past_the_end_and_writes_no_part(thy, run, snapshot):
    p = thy()
    before = snapshot()
    r = run("split", p, "Part_A|Main|7..11", "Part_B|Main|30..40", "--cut")
    assert r.returncode == 1
    assert snapshot() == before


def test_merge_refuses_a_source_without_begin_end(thy, run, snapshot):
    p = thy()
    thy("Broken.thy", "theory Broken imports Main\nlemma x: True by simp\n")
    before = snapshot()
    r = run("merge", p, p.parent / "Broken.thy")
    assert r.returncode == 1 and snapshot() == before


def test_an_unreadable_file_is_a_fail_not_a_traceback(tmp_path, run, snapshot):
    bad = tmp_path / "Bad.thy"
    bad.write_bytes(b"theory Bad imports Main begin\n\xff\xfe\nend\n")
    before = snapshot()
    r = run("delete", f"{bad}:2")
    assert r.returncode == 1 and snapshot() == before


# --- a dry run writes nothing -------------------------------------------------

DRY_RUNS = {
    "move": lambda p, e, n: ["move", f"{p}:alpha", "before", "gamma_tr"],
    "move-between": lambda p, e, n: ["move", f"{p}:alpha", "before", f"{e}:delta"],
    "copy": lambda p, e, n: ["copy", f"{p}:7..9", "before", "16"],
    "delete": lambda p, e, n: ["delete", f"{p}:beta"],
    "replace": lambda p, e, n: ["replace", f"{p}:7..9", n],
    "sub": lambda p, e, n: ["sub", "by simp", "by auto", p, e],
    "resub": lambda p, e, n: ["resub", r"by (\w+)", r"by (\1)", p, e],
    "reargs": lambda p, e, n: ["reargs", "simp $1", "auto $1", p],
    "split": lambda p, e, n: ["split", p, "Part_A|Main|16..17", "--cut"],
    "merge": lambda p, e, n: ["merge", p, e],
}


@pytest.mark.parametrize("case", list(DRY_RUNS))
def test_dry_run_writes_nothing(thy, run, snapshot, tmp_path, case):
    p, e = thy(), thy("Extra.thy", EXTRA)
    n = tmp_path / "new.txt"
    n.write_text('lemma replaced: "9 = (9::nat)"\n  by simp\n')
    before = snapshot()
    args = DRY_RUNS[case](p, e, n)
    if case == "reargs":
        # FIXTURE has no application of a head to an argument; give it one
        p.write_text(FIXTURE.replace("by simp", "by (simp x)", 1))
        before = snapshot()
    r = run(*args, "--dry-run")
    assert r.returncode == 0, r.stdout
    assert last_line(r.stdout).endswith("(dry run)")
    assert snapshot() == before


# --- emit keeps stdout verbatim ----------------------------------------------

def test_emit_reports_on_stderr_and_keeps_stdout_verbatim(thy, run):
    p = thy()
    r = run("emit", f"{p}:7..9")
    assert "PASS:" not in r.stdout and "PASS:" in r.stderr
