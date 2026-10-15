"""Every verb on a fixture, and what each must preserve.

Ported case for case from `bin/block.py --selftest` in NDTHT (29 cases).
Properties, not golden bytes: the blank-seam healing is deliberately
adjustable and a golden file would make every future tweak look like a
regression.  What must not drift is the accounting -- a move preserves the
line count, a copy grows it by the block, a delete shrinks it -- and that
the refusals refuse, writing nothing.
"""
from __future__ import annotations

import pytest

from conftest import EXTRA, FIXTURE, REARGS
from isabelle_block.cli import USAGE, VERBS

N0 = len(FIXTURE.splitlines())


# --- move / copy / delete / emit / replace ---------------------------------

def test_move_preserves_line_count_and_relocates(thy, run):
    p = thy()
    run("move", f"{p}:7..9", "before", "16")
    lines = p.read_text().splitlines()
    assert len(lines) == N0
    assert (lines.index('lemma alpha: "1 = (1::nat)"')
            > lines.index('lemma beta: "2 = (2::nat)"'))


def test_copy_keeps_the_original(thy, run):
    p = thy()
    run("copy", f"{p}:7..9", "before", "16")
    assert p.read_text().count("lemma alpha") == 2


def test_delete_removes_the_block(thy, run):
    p = thy()
    run("delete", f"{p}:7..9")
    assert "lemma alpha" not in p.read_text()


def test_emit_is_verbatim(thy, run):
    p = thy()
    out = run("emit", f"{p}:7..9").stdout
    assert out == "".join(p.read_text().splitlines(keepends=True)[6:9])


def test_replace_swaps_the_block(thy, run, tmp_path):
    p = thy()
    nb = tmp_path / "new.txt"
    nb.write_text('lemma replaced: "9 = (9::nat)"\n  by simp\n')
    run("replace", f"{p}:7..9", nb)
    txt = p.read_text()
    assert "lemma replaced" in txt and "lemma alpha" not in txt


# --- sub ----------------------------------------------------------------------

def test_sub_is_span_confined(thy, run):
    p = thy()
    run("sub", "alpha", "alpha_2", f"{p}:7..9")
    assert p.read_text().count("alpha_2") == 1


def test_sub_replacement_is_literal(thy, run):
    p = thy()
    run("sub", "by simp", "by (simp add: \\<lambda>x. x)", p)
    assert "\\<lambda>" in p.read_text()


def test_sub_refuses_zero_matches(thy, run):
    p = thy()
    before = p.read_text()
    r = run("sub", "no_such_token", "x", p)
    assert r.returncode == 1 and p.read_text() == before


def test_sub_applies_every_region_of_one_file(thy, run):
    # Buffering per target instead of per file let the last write discard the
    # rest, while every target still reported its own match count -- a false
    # PASS, which is the failure mode worth a case.
    p = thy()
    run("sub", "by simp", "by auto", f"{p}:8", f"{p}:17")
    txt = p.read_text()
    assert txt.count("by auto") == 2 and txt.count("by simp") == 1


# --- resub --------------------------------------------------------------------

def test_resub_joins_lines_span_confined_bottom_up(thy, run):
    p = thy()
    run("resub", r"lemma (\w+): (.*)\n  by simp", r"lemma \1: \2 by simp",
        f"{p}:7..9", f"{p}:16..18")
    txt = p.read_text()
    assert 'lemma alpha: "1 = (1::nat)" by simp' in txt
    assert 'lemma gamma_tr: "3 = (3::nat)" by simp' in txt
    assert 'lemma beta: "2 = (2::nat)"\n  by simp' in txt


def test_resub_keeps_a_non_letter_escape(thy, run):
    p = thy()
    run("resub", "by simp", r"by (simp add: \<lambda>x. x)", p)
    assert "\\<lambda>" in p.read_text()


def test_resub_refuses_zero_matches(thy, run):
    p = thy()
    before = p.read_text()
    r = run("resub", "no_such_token", "x", p)
    assert r.returncode == 1 and p.read_text() == before


# --- --except / --expect --------------------------------------------------------

def test_except_leaves_the_named_entry_out(thy, run):
    p = thy()
    run("sub", "by simp", "by auto", p, "--except", "beta")
    txt = p.read_text()
    assert txt.count("by auto") == 2
    assert 'lemma beta: "2 = (2::nat)"\n  by simp' in txt


def test_except_refuses_a_name_in_no_target(thy, run):
    p = thy()
    before = p.read_text()
    r = run("sub", "by simp", "by auto", p, "--except", "no_such_entry")
    assert r.returncode == 1 and p.read_text() == before


def test_expect_refuses_a_wrong_count_then_passes_the_right_one(thy, run):
    p = thy()
    before = p.read_text()
    r = run("sub", "by simp", "by auto", p, "--expect", "2")
    assert r.returncode == 1 and p.read_text() == before
    r = run("sub", "by simp", "by auto", p, "--expect", "3")
    assert r.returncode == 0 and p.read_text().count("by auto") == 3


# --- reargs -------------------------------------------------------------------

def test_reargs_refuses_a_partial_application(thy, run):
    p = thy("Rearg.thy", REARGS)
    before = p.read_text()
    r = run("reargs", "f $1 $2", "G $1", p)
    assert r.returncode == 1 and p.read_text() == before
    assert "Rearg.thy:16:" in r.stdout + r.stderr


def test_reargs_rewrites_bracket_aware_nested_first(thy, run):
    p = thy("Rearg.thy", REARGS)
    r = run("reargs", "f $1 $2", "G $1", p,
            "--except", "f", "--except", "three", "--expect", "4")
    txt = p.read_text()
    assert r.returncode == 0, r.stdout + r.stderr
    assert 'lemma one: "G (g (h 1)) = g (h 1)"' in txt
    assert 'lemma two: "G (G x) = G x"' in txt
    # prose, bare mentions, prefixes and exclusions are left alone
    assert "\\<open>f\\<close> is f x y" in txt and "f_def" in txt
    assert '"f a b = a"' in txt and "f u)" in txt


# --- split / merge ------------------------------------------------------------

def test_split_writes_and_cuts(thy, run):
    p = thy()
    run("split", p, "Part_A|Main|16..17", "--cut")
    part = p.parent / "Part_A.thy"
    assert part.is_file() and "gamma_tr" in part.read_text()
    assert "gamma_tr" not in p.read_text()


def test_merge_splices_the_body(thy, run):
    p = thy()
    e = thy("Extra.thy", EXTRA)
    run("merge", p, e)
    txt = p.read_text()
    assert "lemma delta" in txt and txt.count("theory ") == 1
    assert txt.rstrip().endswith("end")


# --- name addressing ----------------------------------------------------------

def test_name_addressing_resolves_an_entry(thy, run):
    p = thy()
    r = run("emit", f"{p}:beta")
    assert "lemma beta" in r.stdout and "lemma gamma_tr" not in r.stdout


def test_resolved_span_carries_the_preamble_unless_asked(thy, run):
    p = thy()
    assert "A preamble for the first lemma" in run("emit", f"{p}:alpha").stdout
    r = run("emit", f"{p}:alpha", "--no-preamble")
    assert "A preamble" not in r.stdout and "lemma alpha" in r.stdout


def test_unknown_name_refuses(thy, run):
    p = thy()
    assert run("delete", f"{p}:no_such_entry").returncode == 1


# --- modifiers and CLI --------------------------------------------------------

def test_dry_run_writes_nothing(thy, run):
    p = thy()
    before = p.read_text()
    r = run("delete", f"{p}:7..9", "--dry-run")
    assert p.read_text() == before and "dry run" in r.stdout


@pytest.mark.parametrize("verb", list(VERBS))
def test_every_verb_answers_help(run, verb):
    # The regression is the old behaviour, where "--help" was read as the
    # verb's first positional and refused for the argument count.
    r = run(verb, "--help")
    assert r.returncode == 0
    assert r.stdout.startswith(f"usage: {USAGE[verb]}")
    assert "FAIL:" not in r.stdout


def test_version(run):
    r = run("--version")
    assert r.returncode == 0 and r.stdout.startswith("isabelle-block ")
