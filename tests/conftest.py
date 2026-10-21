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


def last_line(text: str) -> str:
    lines = text.rstrip("\n").splitlines()
    return lines[-1] if lines else ""


def check_contract(args, r: subprocess.CompletedProcess) -> None:
    """Every run ends with `PASS:` or `FAIL:`, and the exit status agrees.

    The verdict is the last line of stdout, except for a successful `emit`:
    its stdout is the block itself, verbatim, so its `PASS:` goes to stderr.
    `--help` and `--version` are questions, not runs, and are exempt."""
    args = [str(a) for a in args]
    if not args or {"-h", "--help", "-V", "--version"} & set(args):
        return
    stream = r.stderr if args[0] == "emit" and r.returncode == 0 else r.stdout
    verdict = last_line(stream)
    want = "PASS:" if r.returncode == 0 else "FAIL:"
    assert verdict.startswith(want), (
        f"exit {r.returncode} but last line {verdict!r}\n"
        f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
    assert r.returncode in (0, 1), r.returncode


@pytest.fixture
def run():
    """`run_block`, with the PASS:/FAIL: contract checked on every call."""
    def checked(*args) -> subprocess.CompletedProcess:
        r = run_block(*args)
        check_contract(args, r)
        return r
    return checked


@pytest.fixture
def snapshot(tmp_path):
    """``snapshot()`` maps every file under tmp_path to its bytes, so a test
    can assert that a refusal or a dry run left the whole directory alone,
    including files it should not have created."""
    def take() -> dict[str, bytes]:
        return {str(p.relative_to(tmp_path)): p.read_bytes()
                for p in sorted(tmp_path.rglob("*")) if p.is_file()}
    return take


@pytest.fixture
def thy(tmp_path):
    """``thy(name="Fixture.thy", body=FIXTURE)`` writes a theory, returns its path."""
    def make(name: str = "Fixture.thy", body: str = FIXTURE) -> Path:
        p = tmp_path / name
        p.write_text(body)
        return p
    return make
