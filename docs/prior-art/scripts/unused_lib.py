"""Shared helpers for the dead-code scripts (prune-rounds.py, classify-unused.py).

`query unused` counts proof-body references, so two kinds of entry look
zero-caller while being live: definitions used only in statements, and rules
used implicitly by the simplifier or the classical reasoner.  `implicit_use`
detects the second kind by reading the source rather than the call graph.
"""
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HEAD = re.compile(r"^--- (\S+) \((\w+)\) — (\S+\.thy) \[src (\d+)\.\.(\d+)")
KEYWORDS = r"(?:lemma|theorem|corollary|proposition|schematic_goal)"


def locate(session_dir, name):
    """(theory path, first line, last line) of NAME's span, or None."""
    out = subprocess.run(["query", "-R", session_dir, "show", name], capture_output=True,
                         text=True, cwd=ROOT).stdout
    for line in out.splitlines():
        m = HEAD.match(line)
        if m and m.group(1) == name:
            return Path(session_dir) / m.group(3), int(m.group(4)), int(m.group(5))
    return None


DOCS = ["CLAUDE.md", "nth-design.md", "tasks.md", "decisions.md", "afp-revisions.md",
        "ht.md"]


def mentioned(session_dir, name):
    """Where NAME is named outside its own span, or None.

    A zero-caller entry has no proof-body reference, so another occurrence in
    the session's theories is prose (a `text` block or comment explaining the
    design) or a statement use; one in the design docs or the KB is a
    citation.  Either way deleting the entry leaves a reader pointed at
    nothing, so the entry is part of the explained design, not dead code."""
    loc = locate(session_dir, name)
    word = re.compile(rf"\b{re.escape(name)}\b")
    for thy in sorted(Path(session_dir).glob("*.thy")):
        for i, line in enumerate(thy.read_text().splitlines(), 1):
            if loc and thy.resolve() == loc[0].resolve() and loc[1] <= i <= loc[2]:
                continue
            if word.search(line):
                return f"{thy.name}:{i}"
    paths = [ROOT / d for d in DOCS] + sorted((ROOT / "techniques").glob("*.md")) \
        + sorted((ROOT / "insights").glob("*.md"))
    for p in paths:
        if p.exists() and word.search(p.read_text()):
            return p.name
    return None


def implicit_use(session_dir, name):
    """A reason NAME may be used without being cited, or None.

    Reasons: an attribute on its own header (`lemma NAME [simp]:`), or a
    mention in a `declare` / `lemmas` command anywhere in the session, which
    is how a rule joins a simp set or a bundle after the fact."""
    loc = locate(session_dir, name)
    if loc:
        path, a, b = loc
        lines = path.read_text().splitlines()[a - 1:b]
        header = re.compile(rf"^\s*{KEYWORDS}\s+{re.escape(name)}\s*\[")
        if any(header.match(l) for l in lines):
            return "attribute"
    word = re.compile(rf"\b{re.escape(name)}\b")
    cmd = re.compile(r"^\s*(declare|lemmas)\b")
    for thy in Path(session_dir).glob("*.thy"):
        text = thy.read_text().splitlines()
        for i, line in enumerate(text):
            if cmd.match(line):
                # a declare/lemmas command runs until the next blank line
                j, block = i, []
                while j < len(text) and text[j].strip():
                    block.append(text[j])
                    j += 1
                if any(word.search(l) for l in block):
                    return f"{cmd.match(line).group(1)} in {thy.name}"
    return None
