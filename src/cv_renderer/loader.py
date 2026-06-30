import os
from pathlib import Path

import yaml

from cv_renderer.models import CVData, Profile

_ROOT = Path(__file__).parent.parent.parent
_USER_DATA = (
    Path(os.environ["CV_DATA_DIR"]) if "CV_DATA_DIR" in os.environ else _ROOT / "user-data"
)


def _user_data_root() -> Path:
    if not _USER_DATA.exists():
        raise FileNotFoundError(
            f"CV data directory not found: {_USER_DATA}\n"
            "Either set CV_DATA_DIR env var or create user-data/ from the examples:\n"
            "  uv run python render.py init\n"
            "  cp profiles/general.example.yaml user-data/profiles/general.yaml\n"
            "Then fill in your own information."
        )
    return _USER_DATA


def load_cv(lang: str = "en") -> CVData:
    path = _user_data_root() / "data" / f"base_{lang}.yaml"
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return CVData.model_validate(raw)


def load_labels(lang: str = "en") -> dict[str, str]:
    user_path = _USER_DATA / "data" / "labels" / f"{lang}.yaml"
    fallback = _ROOT / "examples" / "data" / "labels" / f"{lang}.yaml"
    path = user_path if user_path.exists() else fallback
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_profile(name: str) -> Profile:
    path = _user_data_root() / "profiles" / f"{name}.yaml"
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return Profile.model_validate(raw)
