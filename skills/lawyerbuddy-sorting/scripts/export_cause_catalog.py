#!/usr/bin/env python3
"""Export the bundled cause-of-action workbook to a portable JSON asset."""

from __future__ import annotations

import json
from pathlib import Path

from cause_catalog import XLSX_CATALOG, load_catalog


def main() -> None:
    output = XLSX_CATALOG.with_suffix(".json")
    records = load_catalog(XLSX_CATALOG)
    output.write_text(
        json.dumps(records, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"{output} ({len(records)} 条案由记录)")


if __name__ == "__main__":
    main()
