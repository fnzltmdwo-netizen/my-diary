from __future__ import annotations

import base64
import hashlib
from pathlib import Path

BASE = Path(__file__).resolve().parent
PARTS = BASE / "_upload_parts"


def assemble(glob_pattern: str, output_name: str, expected_sha256: str | None = None) -> None:
    files = sorted(PARTS.glob(glob_pattern))
    if not files:
        raise RuntimeError(f"missing frontend parts: {glob_pattern}")
    data = b"".join(base64.b64decode(p.read_text(encoding="utf-8").strip()) for p in files)
    if expected_sha256:
        got = hashlib.sha256(data).hexdigest()
        if got != expected_sha256:
            raise RuntimeError(f"frontend hash mismatch for {output_name}: {got}")
    (BASE / output_name).write_bytes(data)


assemble("index.html.*.b64", "index.html", "e27b5e207c2c721cfeb32148c9669243f9d9417bd9bc6bfe13374e8adaed2cd6")
assemble("style_current.*.b64", "styles.css")

from server import app  # noqa: E402,F401
