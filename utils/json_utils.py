from __future__ import annotations

import json
import re
from typing import Any, Optional

JSON_BLOCK_RE = re.compile(r"\{[\s\S]*?\}", re.MULTILINE)

def extract_first_json_block(text: str) -> Optional[dict[str, Any]]:
    """Zoekt naar de eerste JSON-achtige blok in de tekst en probeert te parsen."""
    if not text:
        return None
    # Probeer eerst direct json
    try:
        return json.loads(text)
    except Exception:
        pass
    # Zoek blok
    m = JSON_BLOCK_RE.search(text)
    if not m:
        return None
    snippet = m.group(0)
    try:
        return json.loads(snippet)
    except Exception:
        return None
