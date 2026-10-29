"""Settings loader. Defaults come from config/settings.example.toml; an optional
config/settings.toml (or a file passed explicitly) overrides them.

Credentials are never read from files: a provider names an environment
variable (`api_key_env`) and `secret()` reads it at call time.
"""

from __future__ import annotations

import copy
import os
import tomllib
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULTS_FILE = PROJECT_ROOT / "config" / "settings.example.toml"
USER_FILE = PROJECT_ROOT / "config" / "settings.toml"
SAMPLE_FILE = PROJECT_ROOT / "sample_data" / "settings.sample.toml"


class ConfigError(Exception):
    pass


def _merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def _find_secrets(node: Any, path: str = "") -> list:
    """Keys that look like inline credentials. Settings must name env vars instead."""
    bad = []
    if isinstance(node, dict):
        for k, v in node.items():
            p = "%s.%s" % (path, k) if path else k
            low = k.lower()
            if any(w in low for w in ("password", "secret", "token", "api_key")) and not low.endswith("_env"):
                if v not in (None, ""):
                    bad.append(p)
            bad.extend(_find_secrets(v, p))
    return bad


class Settings:
    def __init__(self, data: dict, root: Path = PROJECT_ROOT, origin: str = ""):
        bad = _find_secrets(data)
        if bad:
            raise ConfigError("credentials must not be stored in settings files; use *_env names: "
                              + ", ".join(bad))
        self.data = data
        self.root = root
        self.origin = origin

    @classmethod
    def load(cls, path: Optional[os.PathLike] = None, sample: bool = False,
             overrides: Optional[dict] = None) -> "Settings":
        with open(DEFAULTS_FILE, "rb") as fh:
            data = tomllib.load(fh)
        origin = [str(DEFAULTS_FILE.name)]
        chosen = Path(path) if path else (SAMPLE_FILE if sample else (USER_FILE if USER_FILE.exists() else None))
        if chosen:
            if not chosen.exists():
                raise ConfigError("settings file not found: %s" % chosen)
            with open(chosen, "rb") as fh:
                data = _merge(data, tomllib.load(fh))
            origin.append(str(chosen))
        if overrides:
            data = _merge(data, overrides)
        return cls(data, origin=" + ".join(origin))

    def get(self, dotted: str, default: Any = None) -> Any:
        node: Any = self.data
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node

    def path(self, dotted: str, default: Optional[str] = None) -> Path:
        value = self.get(dotted, default)
        if value is None:
            raise ConfigError("missing setting %s" % dotted)
        p = Path(value)
        return p if p.is_absolute() else (self.root / p)

    def paths(self, dotted: str) -> list:
        out = []
        for v in self.get(dotted, []) or []:
            p = Path(v)
            out.append(p if p.is_absolute() else self.root / p)
        return out

    @property
    def synthetic(self) -> bool:
        return bool(self.get("general.synthetic", False))


def secret(env_name: Optional[str]) -> Optional[str]:
    """Read a credential from the environment. Returns None if unset; never logs it."""
    if not env_name:
        return None
    value = os.environ.get(env_name)
    return value or None
