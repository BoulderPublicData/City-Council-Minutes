import os
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


def test_data_dir_override(tmp_path):
    """CCM_DATA_DIR moves every data path out of the working tree (for long runs)."""
    env = {**os.environ, "CCM_DATA_DIR": str(tmp_path / "data")}
    out = subprocess.run(
        [sys.executable, "-c",
         "from scripts import config as c; print(c.DATA); print(c.MANIFEST_CSV); print(c.CA_BUNDLE)"],
        cwd=ROOT, env=env, capture_output=True, text=True, check=True).stdout.split()
    assert out[0] == str((tmp_path / "data").resolve())
    assert out[1].startswith(out[0])
    assert out[2] == str(ROOT / "certs" / "boulder-ca-bundle.pem")  # code assets stay put


def test_extraction_runs_reference_meetings_first(tmp_path, monkeypatch):
    from scripts import datalab
    manifest = tmp_path / "manifest.csv"
    pd.DataFrame({"entry_id": [10, 20, 30, 40], "year_folder": [2000] * 4,
                  "local_path": ["x"] * 4}).to_csv(manifest, index=False)
    monkeypatch.setattr(datalab, "MANIFEST_CSV", manifest)
    monkeypatch.setattr(datalab, "gold_entry_ids", lambda: [30])
    assert datalab._targets("all", None, None)["entry_id"].tolist() == [30, 10, 20, 40]
