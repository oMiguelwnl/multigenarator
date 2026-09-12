import pytest

from multilang.services.native_cache import VersionedCache
from multilang.services.plugins import PluginRegistry


def test_cache_namespaces_versions_expiry_and_copy_isolation():
    now = [0.0]
    cache = VersionedCache(max_entries=2, ttl_seconds=5, clock=lambda: now[0])
    cache.put("ranking", "v1", "en", {"rank": [1]})
    value = cache.get("ranking", "v1", "en")
    value["rank"].append(2)
    assert cache.get("ranking", "v1", "en") == {"rank": [1]}
    assert cache.get("ranking", "v2", "en") is None
    assert cache.get("audio", "v1", "en") is None
    now[0] = 6
    assert cache.get("ranking", "v1", "en") is None


def test_plugin_registration_is_explicit_versioned_and_never_imports_paths():
    registry = PluginRegistry()
    plugin = object()
    registry.register(kind="module", name="fixture", version="1", plugin=plugin)
    assert registry.get("module", "fixture", "1") is plugin
    with pytest.raises(ValueError):
        registry.register(kind="module", name="fixture", version="1", plugin=object())
    with pytest.raises(ValueError):
        registry.get("module", "os.system", "1")
