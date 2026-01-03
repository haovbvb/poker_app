"""Texas Hold'em backend modules.

This package provides a production-oriented API skeleton:
- Table/lobby lifecycle (REST)
- WebSocket event stream (snapshot + incremental events)

Game-rule completeness (hand evaluation, side pots, betting rules) is intentionally
kept behind an engine interface so it can be iterated safely.
"""

from .manager import poker_manager

__all__ = ["poker_manager"]
