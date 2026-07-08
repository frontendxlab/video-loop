from __future__ import annotations

import json
from pathlib import Path


class Captions:
    def generate_caption_json(self, segments: list[dict], output_path: Path) -> str:
        output_path.write_text(json.dumps(segments, indent=2))
        return str(output_path)
