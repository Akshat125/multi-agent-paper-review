#!/usr/bin/env python3
"""Execute eval analysis notebooks headlessly and regenerate figures."""
import json
import sys
import traceback
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent


class _Display:
    @staticmethod
    def __call__(*args, **kwargs):
        pass


def run_notebook(path: Path) -> tuple[bool, str]:
    with open(path) as f:
        nb = json.load(f)
    g = {
        "__name__": "__main__",
        "display": _Display(),
        "plt": plt,
    }
    for i, cell in enumerate(nb["cells"]):
        if cell["cell_type"] != "code":
            continue
        src = "".join(cell["source"])
        if not src.strip():
            continue
        try:
            exec(compile(src, f"{path.name}:cell{i}", "exec"), g)
        except Exception:
            return False, f"cell {i} failed:\n{traceback.format_exc()}"
    plt.close("all")
    return True, "ok"


def main():
    notebooks = sorted(ROOT.glob("*.ipynb"))
    notebooks = [p for p in notebooks if not p.name.startswith("_")]
    failed = []
    for nb in notebooks:
        ok, msg = run_notebook(nb)
        status = "OK" if ok else "FAIL"
        print(f"{status}: {nb.name}")
        if not ok:
            print(msg)
            failed.append(nb.name)
    if failed:
        sys.exit(1)
    print(f"\nAll {len(notebooks)} notebooks executed successfully.")


if __name__ == "__main__":
    main()
