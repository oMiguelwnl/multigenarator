"""Compatibility import for :mod:`multilang.services.audio.native`.

The shared module object preserves existing monkeypatch and import behavior.
New code should use the responsibility package.
"""

import sys
from importlib import import_module

sys.modules[__name__] = import_module("multilang.services.audio.native")
