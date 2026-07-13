"""Shared helper for tests that need the REAL SPOT kernel (not a MagicMock).

Most test files in this suite install ``sys.modules['spot'] = MagicMock()`` at
import time so they can run where the conda-only SPOT library is absent. That
makes it impossible to test the SPOT-backed modules (``spotutils``,
``feedbackgenerator``, ``stepper``, and the Flask routes) for real.

``load_real(*module_names)`` restores the real ``spot`` and re-imports the
requested pure-Python modules against it, returning the freshly-loaded modules.
It returns ``None`` if SPOT is genuinely unavailable so callers can
``skipUnless`` cleanly.

CRITICAL invariant: ``spot`` is a C-extension whose automata carry a global BDD
dict. Popping ``spot`` from ``sys.modules`` and re-importing yields a *different*
module object with a *different* BDD dict, and automata from the two cannot be
combined ("left and right automata should share their bdd_dict"). We therefore
import the real ``spot`` **exactly once**, cache that single object, and only
ever *restore* it -- we never re-import it. Only the pure-Python wrapper modules
are reloaded.

Verified to coexist with the mocking test files under both ``pytest`` and
``unittest discover``, regardless of collection order.
"""

import importlib
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


def _is_mock(mod):
    return mod is not None and type(mod).__module__.startswith(("unittest", "mock"))


def _capture_real_spot():
    """Import the real ``spot`` once and return it (or ``None`` if unavailable).

    If a sibling test has already installed a MagicMock under ``sys.modules
    ['spot']``, drop it first so the import reaches the genuine extension.
    """
    existing = sys.modules.get("spot")
    if existing is not None and not _is_mock(existing):
        return existing  # a real spot is already loaded; reuse that exact object
    if _is_mock(existing):
        sys.modules.pop("spot", None)
    try:
        import spot  # the one and only real import in this process
    except Exception:
        return None
    return None if _is_mock(sys.modules.get("spot")) else sys.modules["spot"]


# Capture at module import time so this is the first (and only) real spot import.
_REAL_SPOT = _capture_real_spot()


def spot_available():
    """True if the real SPOT library is importable."""
    return _REAL_SPOT is not None


def load_real(*module_names):
    """Reload the given src modules against the cached real SPOT kernel.

    Returns a tuple of the reloaded modules in the order requested, or ``None``
    if SPOT is unavailable. Reload dependencies before dependents (e.g. pass
    ``"spotutils"`` before ``"feedbackgenerator"``) so the dependent rebinds the
    freshly reloaded dependency.
    """
    if _REAL_SPOT is None:
        return None
    # Restore the single cached real spot object (a mocking sibling may have
    # overwritten sys.modules['spot'] during collection).
    sys.modules["spot"] = _REAL_SPOT
    loaded = []
    for name in module_names:
        if name in sys.modules:
            mod = importlib.reload(sys.modules[name])
        else:
            mod = importlib.import_module(name)
        loaded.append(mod)
    return tuple(loaded)
