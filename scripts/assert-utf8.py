#!/usr/bin/env python3
"""Reject skill files that are not UTF-8 with BOM, or that mojibake the display name."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BOM = b"\xef\xbb\xbf"
DISPLAY_NAME = "据实落地"
MOJIBAKE_MARKERS = (
    "\ufffd",
    "\u9521\u65a4\u62f7",
    "\u70eb\u70eb\u70eb",
    DISPLAY_NAME.encode("utf-8").decode("latin-1"),
)

SKIP_DIR_NAMES = {".git"}
BOM_SUFFIXES = {".md", ".json", ".txt", ".yml", ".yaml"}
UTF8_NOBOM_SUFFIXES = {".py"}
EDITORCONFIG_NAME = ".editorconfig"


def iter_text_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if path.name == EDITORCONFIG_NAME or path.suffix.lower() in BOM_SUFFIXES | UTF8_NOBOM_SUFFIXES:
            files.append(path)
    return sorted(files)


def decode_or_report(path: Path, raw: bytes) -> str:
    want_bom = path.name == EDITORCONFIG_NAME or path.suffix.lower() in BOM_SUFFIXES
    if want_bom:
        if not raw.startswith(BOM):
            raise SystemExit(f"{path.relative_to(ROOT)}: missing UTF-8 BOM")
        body = raw[len(BOM) :]
    else:
        if raw.startswith(BOM):
            raise SystemExit(
                f"{path.relative_to(ROOT)}: Python/script must be UTF-8 without BOM"
            )
        body = raw
    try:
        return body.decode("utf-8")
    except UnicodeDecodeError as exc:
        try:
            preview = body.decode("gb18030")[:80]
        except UnicodeDecodeError:
            preview = body[:40].hex()
        raise SystemExit(
            f"{path.relative_to(ROOT)}: not UTF-8 ({exc}). "
            f"Possible ANSI/GBK. preview={preview!r}"
        ) from exc


def main() -> int:
    files = iter_text_files()
    if not files:
        raise SystemExit("no text files found")
    skill = None
    for path in files:
        text = decode_or_report(path, path.read_bytes())
        if path.name == "SKILL.md":
            skill = text
        for marker in MOJIBAKE_MARKERS:
            if marker in text:
                raise SystemExit(
                    f"{path.relative_to(ROOT)}: mojibake marker {marker!r}"
                )
    if skill is None:
        raise SystemExit("SKILL.md missing")
    if f"# {DISPLAY_NAME}" not in skill.splitlines()[0:20] and f"# {DISPLAY_NAME}" not in skill:
        raise SystemExit(
            f"SKILL.md must contain the UTF-8 heading '# {DISPLAY_NAME}'"
        )
    if "name: grounded-dev-loop" not in skill:
        raise SystemExit("SKILL.md must keep ASCII id name: grounded-dev-loop")
    print(f"ok: {len(files)} files, UTF-8 (BOM on md/json), {DISPLAY_NAME!r} intact")
    return 0


if __name__ == "__main__":
    sys.exit(main())
