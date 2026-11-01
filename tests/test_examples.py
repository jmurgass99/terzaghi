# -*- coding: utf-8 -*-
"""Cada ejemplo de ``examples/`` termina con código 0 (se ejecutan como subprocesos)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

_EXAMPLES = sorted((Path(__file__).resolve().parents[1] / "examples").glob("*.py"))


@pytest.mark.parametrize("example_path", _EXAMPLES, ids=[p.name for p in _EXAMPLES])
def test_example_runs_clean(example_path: Path, tmp_path: Path) -> None:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env["JM_EXAMPLES_OUT_DIR"] = str(tmp_path)
    result = subprocess.run(
        [sys.executable, "-X", "utf8", str(example_path)],
        capture_output=True, text=True, timeout=100, env=env,
        cwd=str(example_path.parent.parent),
    )
    assert result.returncode == 0, f"{example_path.name}\nSTDOUT: {result.stdout[-800:]}\nSTDERR: {result.stderr[-800:]}"
