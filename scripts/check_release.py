"""Check source hygiene and package metadata without network or live transports."""
from pathlib import Path
import ast
import json
import re

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = ("README.md", "LICENSE", "SECURITY.md", "CONTRIBUTING.md",
            "CHANGELOG.md", "RELEASE_CHECKLIST.md", "pyproject.toml")


def main():
    for name in REQUIRED:
        if not (ROOT / name).is_file():
            raise SystemExit(f"Missing release document: {name}")
    for directory in ("pairhatch", "tests", "scripts"):
        for path in (ROOT / directory).rglob("*.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    example = json.loads((ROOT / "examples/native.template.json").read_text())
    if example.get("experimental_native_transports") is not False:
        raise SystemExit("Native example must remain disabled")
    version = re.search(r'^version = "([^"<>]+)"$',
                        (ROOT / "pyproject.toml").read_text(), re.M).group(1)
    from pairhatch import __version__
    if version != __version__:
        raise SystemExit("Package and runtime versions differ")
    print("PASS: release documents, Python syntax, disabled native example, version consistency")


if __name__ == "__main__":
    # Permit execution from an unrelated working directory without installation.
    import sys
    sys.path.insert(0, str(ROOT))
    main()
