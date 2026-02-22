"""Parquet-based cache store with JSON sidecar metadata."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

import pandas as pd

from macro_econ.config import CACHE_DIR, DEFAULT_CACHE_TTL


def make_key(source: str, series_id: str, **params: object) -> str:
    """Generate a cache key from source, series_id, and extra params."""
    canonical = json.dumps(
        {"source": source, "series_id": series_id, **params},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(canonical.encode()).hexdigest()[:16]


class ParquetCacheStore:
    """File-based cache using Parquet files with JSON metadata sidecars."""

    def __init__(self, cache_dir: Path | None = None, ttl: int = DEFAULT_CACHE_TTL):
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl

    def _data_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.parquet"

    def _meta_path(self, key: str) -> Path:
        return self.cache_dir / f"{key}.meta.json"

    def get(self, key: str) -> pd.DataFrame | None:
        """Return cached DataFrame or None if missing/stale."""
        data_path = self._data_path(key)
        meta_path = self._meta_path(key)

        if not data_path.exists() or not meta_path.exists():
            return None

        with open(meta_path) as f:
            meta = json.load(f)

        if time.time() - meta.get("fetched_at", 0) > self.ttl:
            return None

        return pd.read_parquet(data_path)

    def put(self, key: str, df: pd.DataFrame, **extra_meta: object) -> None:
        """Write DataFrame and metadata to cache."""
        data_path = self._data_path(key)
        meta_path = self._meta_path(key)

        df.to_parquet(data_path)

        meta = {
            "fetched_at": time.time(),
            "key": key,
            **extra_meta,
        }
        with open(meta_path, "w") as f:
            json.dump(meta, f, indent=2, default=str)

    def invalidate(self, key: str) -> None:
        """Delete cache entry."""
        self._data_path(key).unlink(missing_ok=True)
        self._meta_path(key).unlink(missing_ok=True)

    def clear_all(self) -> None:
        """Remove all cache files."""
        for path in self.cache_dir.glob("*.parquet"):
            path.unlink()
        for path in self.cache_dir.glob("*.meta.json"):
            path.unlink()

    def list_entries(self) -> list[tuple[str, dict]]:
        """Return list of (key, metadata) for all cache entries."""
        entries = []
        for meta_path in sorted(self.cache_dir.glob("*.meta.json")):
            with open(meta_path) as f:
                meta = json.load(f)
            key = meta_path.stem.replace(".meta", "")
            entries.append((key, meta))
        return entries
