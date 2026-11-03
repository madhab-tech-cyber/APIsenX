"""Fail if any text source/config file starts with a UTF-8 BOM.

A BOM in pyproject.toml makes Python's tomllib raise
"TOMLDecodeError: Invalid statement (at line 1, column 1)", which kills
pytest before collection and breaks other strict parsers. Editors on
Windows add BOMs silently, so this guard runs in CI.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUFFIXES = {
    ".py", ".toml", ".txt", ".yml", ".yaml", ".json", ".md", ".cfg", ".ini",
    ".ts", ".tsx", ".js", ".jsx", ".css", ".html",
}
SKIP_DIRS = {".git", "node_modules", "__pycache__"}
BOM = b"\xef\xbb\xbf"


def offenders():
    bad = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path.suffix not in SUFFIXES:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        with path.open("rb") as handle:
            if handle.read(3) == BOM:
                bad.append(path.relative_to(ROOT))
    return bad


def main():
    bad = offenders()
    if bad:
        print("UTF-8 BOM found at the start of these files:")
        for path in bad:
            print(f"  {path}")
        print("Rewrite each file without the BOM (UTF-8, no signature).")
        return 1
    print("No BOM found in tracked text files.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
