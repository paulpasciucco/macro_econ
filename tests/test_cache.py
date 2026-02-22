"""Tests for ParquetCacheStore."""

import time

import pandas as pd
import pytest

from macro_econ.cache.store import ParquetCacheStore, make_key


@pytest.fixture
def cache_store(tmp_path):
    return ParquetCacheStore(cache_dir=tmp_path, ttl=10)


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {"value": [100.0, 101.5, 103.2]},
        index=pd.to_datetime(["2024-01-01", "2024-02-01", "2024-03-01"]),
    )


class TestMakeKey:
    def test_deterministic(self):
        k1 = make_key("fred", "UNRATE")
        k2 = make_key("fred", "UNRATE")
        assert k1 == k2

    def test_different_inputs(self):
        k1 = make_key("fred", "UNRATE")
        k2 = make_key("fred", "GDP")
        assert k1 != k2

    def test_length(self):
        k = make_key("fred", "UNRATE")
        assert len(k) == 16


class TestParquetCacheStore:
    def test_miss_returns_none(self, cache_store):
        assert cache_store.get("nonexistent") is None

    def test_put_and_get(self, cache_store, sample_df):
        key = make_key("fred", "TEST")
        cache_store.put(key, sample_df, source="fred", series_id="TEST")
        result = cache_store.get(key)
        assert result is not None
        pd.testing.assert_frame_equal(result, sample_df)

    def test_stale_returns_none(self, tmp_path, sample_df):
        store = ParquetCacheStore(cache_dir=tmp_path, ttl=0)
        key = make_key("fred", "TEST")
        store.put(key, sample_df)
        time.sleep(0.01)
        assert store.get(key) is None

    def test_invalidate(self, cache_store, sample_df):
        key = make_key("fred", "TEST")
        cache_store.put(key, sample_df)
        cache_store.invalidate(key)
        assert cache_store.get(key) is None

    def test_clear_all(self, cache_store, sample_df):
        for i in range(3):
            key = make_key("fred", f"TEST{i}")
            cache_store.put(key, sample_df)
        cache_store.clear_all()
        for i in range(3):
            key = make_key("fred", f"TEST{i}")
            assert cache_store.get(key) is None

    def test_list_entries(self, cache_store, sample_df):
        keys = []
        for i in range(3):
            key = make_key("fred", f"TEST{i}")
            keys.append(key)
            cache_store.put(key, sample_df, source="fred", series_id=f"TEST{i}")
        entries = cache_store.list_entries()
        assert len(entries) == 3
        entry_keys = [e[0] for e in entries]
        for k in keys:
            assert k in entry_keys
