"""CHAiMERA — the AicodeX Edition 2 orchestration subsystem.

CHAiMERA (Composable Hybrid AI Multi-model Engine for Responsive Automation)
coordinates the specialized model roles. Its conductor, ConductorX, sequences
the enabled roles into a coherent run and reports the resulting "symphony".
"""

from .conductorx import ConductorX, MovementResult, SymphonyReport

__all__ = ["ConductorX", "MovementResult", "SymphonyReport"]
