"""Embeds every data/output/*.json into index.html's dashboard-data block.

Run: python -m src.build_dashboard
Env: OUTPUT_DATA_DIR (default data/output), DASHBOARD_HTML (default index.html).
"""

import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BLOCK_RE = re.compile(
    r'(<script id="dashboard-data" type="application/json">)(.*?)(</script>)', re.DOTALL
)


def build(data_dir: Path, html_path: Path) -> int:
    """Replaces the embedded JSON block; returns the number of files embedded."""
    files = sorted(data_dir.glob("*.json"))
    if not files:
        raise FileNotFoundError(f"No JSON files in {data_dir}; run 'python -m src.main' first")
    data = {f.stem: json.loads(f.read_text(encoding="utf-8")) for f in files}
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e")
    html = html_path.read_text(encoding="utf-8")
    new_html, count = BLOCK_RE.subn(lambda m: m.group(1) + payload + m.group(3), html, count=1)
    if count != 1:
        raise ValueError(f'<script id="dashboard-data"> block not found in {html_path}')
    html_path.write_text(new_html, encoding="utf-8")
    return len(files)


def main() -> int:
    data_dir = Path(os.environ.get("OUTPUT_DATA_DIR", str(ROOT / "data" / "output")))
    html_path = Path(os.environ.get("DASHBOARD_HTML", str(ROOT / "index.html")))
    try:
        n = build(data_dir, html_path)
    except (OSError, ValueError) as exc:  # FileNotFoundError and JSONDecodeError included
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Embedded {n} JSON files from {data_dir} into {html_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
