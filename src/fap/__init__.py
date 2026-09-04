"""Finality-aware planning: deciding under uncertainty about payment finality.

A planning policy over the FinalityBench environment (P1). The question it
answers is the one a fixed procedure cannot: when the outcome of a capture will
not be known before the ship-by deadline, what is the right thing to do, and
does that depend on the order?

The strongest policy shipped with the benchmark escalates every such case to a
human. That is safe and it is never optimal. What to do instead is a function of
the order value and the cost structure, and computing it is what this package
does.
"""

from ._p1 import ensure_p1, p1_provenance  # noqa: F401

__version__ = "1.0.0"
