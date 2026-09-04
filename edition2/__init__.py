"""AicodeX Edition 2 — multi-model orchestration with an optional secrets vault.

Edition 2 layers a configurable roster of specialized model roles on top of the
AicodeX overlay core. Each role is bound to a model and a mission, can be
enabled or disabled independently, and is sequenced by the CHAiMERA
ConductorX orchestration system into a coherent "symphony" of work.

The module is intentionally dependency-free (standard library only) so it can
be exercised anywhere, including in CI, without extra installation.
"""

__version__ = "2.0.0"

__all__ = ["__version__"]
