import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

from cv_renderer.models import CVData, Profile

_ROOT = Path(__file__).parent.parent.parent
load_dotenv(_ROOT / ".env")
_USER_DATA = Path(os.environ["CV_DATA_DIR"]) if "CV_DATA_DIR" in os.environ else _ROOT / "user-data"


def _user_data_root() -> Path:
    if not _USER_DATA.exists():
        raise FileNotFoundError(
            f"CV data directory not found: {_USER_DATA}\n\n"
            "Option 1 — create a fresh data directory inside the repo:\n"
            "  uv run python render.py init\n"
            "  Then fill in user-data/ with your own information.\n\n"
            "Option 2 — point to an existing data directory:\n"
            "  Set CV_DATA_DIR in your .env file to the absolute path of your data folder."
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
    if not path.exists():
        raise FileNotFoundError(
            f"Profile '{name}' not found at {path}\n"
            "Run 'uv run python render.py --list' to see available profiles."
        )
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return Profile.model_validate(raw)
