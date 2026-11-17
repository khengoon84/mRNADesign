"""mRNADesign: orchestration over pinned upstream tools.

Nothing in this package implements a scientific algorithm. Every design, folding,
prediction or constraint step is delegated to a pinned upstream tool behind an
adapter (`DECISIONS.md` D-001); this package owns configuration, validation,
provenance, reporting and the run ledger.
"""

__version__ = "0.1.0.dev0"
