# tests/test__load_all_features.py
import os
from pathlib import Path
from pytest_bdd import scenarios

FEATURE_ROOT = Path("features")
only = os.getenv("FEATURE")  # e.g. "api/authentication/auth_api.feature" or "api/authentication"

def is_valid_feature(p: Path) -> bool:
    text = p.read_text(encoding="utf-8", errors="strict")
    lines = [ln.strip().lower() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]
    return any(ln.startswith("feature:") for ln in lines) and any(
        ln.startswith(("scenario:", "scenario outline:")) for ln in lines
    )

targets = [FEATURE_ROOT / only] if only else [FEATURE_ROOT]
for t in targets:
    files = [t] if t.is_file() else t.rglob("*.feature")
    for f in files:
        if is_valid_feature(f):
            scenarios(str(f.relative_to(FEATURE_ROOT)))
        else:
            print(f"[bdd] ⏭️ skipping invalid/empty feature: {f.relative_to(FEATURE_ROOT)}")
