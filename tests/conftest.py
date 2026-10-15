"""Fixtures for the verb tests.

The tests run the tool as a subprocess (`python -m isabelle_block`), as the
old in-file `--selftest` did: every verb ends in `SystemExit`, and what is
under test is the exit status, the PASS:/FAIL: line and the bytes on disk.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

FIXTURE = """\
theory Fixture
  imports Main
begin

text \\<open>A preamble for the first lemma.\\<close>

lemma alpha: "1 = (1::nat)"
  by simp

lemma beta: "2 = (2::nat)"
  by simp


subsection \\<open>A heading\\<close>

lemma gamma_tr: "3 = (3::nat)"
  by simp

end
"""

REARGS = """\
theory Rearg
  imports Main
begin

definition f :: "nat \\<Rightarrow> nat \\<Rightarrow> nat" where "f a b = a"

text \\<open>In prose \\<open>f\\<close> is f x y, and stays so.\\<close>

lemma one: "f (g (h 1)) 2 = g (h 1)"
  by (simp add: f_def)

lemma two: "f (f x y)
    [z] = f x y"
  unfolding f_def by simp

lemma three: "(\\<lambda>u. f u) = id"
  oops

end
"""

EXTRA = """\
theory Extra
  imports Fixture
begin

lemma delta: "4 = (4::nat)"
  by simp

end
"""


def run_block(*args) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-m", "isabelle_block", *map(str, args)],
                          capture_output=True, text=True)


@pytest.fixture
def run():
    return run_block


@pytest.fixture
def thy(tmp_path):
    """``thy(name="Fixture.thy", body=FIXTURE)`` writes a theory, returns its path."""
    def make(name: str = "Fixture.thy", body: str = FIXTURE) -> Path:
        p = tmp_path / name
        p.write_text(body)
        return p
    return make
