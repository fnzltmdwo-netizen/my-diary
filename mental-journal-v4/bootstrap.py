from __future__ import annotations

import base64
from pathlib import Path

BASE = Path(__file__).resolve().parent
PARTS = BASE / "_upload_parts"


def assemble(glob_pattern: str, output_name: str) -> None:
    files = sorted(PARTS.glob(glob_pattern))
    if not files:
        raise RuntimeError(f"missing frontend parts: {glob_pattern}")

    # Chunks are slices of one base64 stream. Join the encoded text first,
    # then decode once so chunk boundaries can never break base64 padding.
    encoded = "".join(p.read_text(encoding="utf-8").strip() for p in files)
    try:
        data = base64.b64decode(encoded)
    except Exception as exc:
        raise RuntimeError(f"failed to rebuild {output_name}: {exc}") from exc

    if not data:
        raise RuntimeError(f"rebuilt {output_name} is empty")

    (BASE / output_name).write_bytes(data)


assemble("index.html.*.b64", "index.html")
assemble("style_current.*.b64", "styles.css")

from server import app  # noqa: E402,F401
