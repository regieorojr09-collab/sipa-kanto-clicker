"""Score tracking, combo multipliers, and accuracy calculations for Sipa: Kanto Clicker."""

from typing import Dict
from core.events import GameEvent, event_bus
from core.settings import (
    POINTS_SWAK,
    POINTS_PUWEDE,
    POINTS_DAPLIS,
    POINTS_BAGSAK,
)


class ScoreKeeper:
    """
    Tracks player score, combo multipliers, and rhythm accuracy statistics.
    Subscribes automatically to GameEvent.HIT_RESULT.
    """

    def __init__(self, difficulty_mult: float = 1.0) -> None:
        self.difficulty_mult: float = difficulty_mult
        self.score: int = 0
        self.current_combo: int = 0
        self.max_combo: int = 0
        self.total_notes: int = 0

        self.counts: Dict[str, int] = {
            "Swak!": 0,
            "Puwede": 0,
            "Daplis": 0,
            "Bagsak!": 0,
        }

        # Subscribe to hit results
        event_bus.subscribe(GameEvent.HIT_RESULT, self._on_hit_result)

    def _on_hit_result(self, judgment: str, points: int = 0, was_miss: bool = False, **kwargs) -> None:
        """Processes hit results dispatched from HitSystem."""
        self.total_notes += 1

        if judgment in self.counts:
            self.counts[judgment] += 1
        else:
            self.counts[judgment] = 1

        if was_miss or judgment == "Bagsak!":
            self.current_combo = 0
        else:
            self.current_combo += 1
            if self.current_combo > self.max_combo:
                self.max_combo = self.current_combo

            # Blueprint formula: BasePoints * (1 + min(Combo, 100) / 25) * DifficultyMult
            combo_factor = 1.0 + (min(self.current_combo, 100) / 25.0)
            earned_points = int(points * combo_factor * self.difficulty_mult)
            self.score += earned_points

    @property
    def accuracy(self) -> float:
        """
        Computes standard rhythm accuracy percentage (0.0 to 100.0%).
        Formula: (300*N_swak + 100*N_puwede + 50*N_daplis) / (300 * TotalNotes) * 100%
        """
        if self.total_notes == 0:
            return 100.0

        weighted_points = (
            (POINTS_SWAK * self.counts.get("Swak!", 0))
            + (POINTS_PUWEDE * self.counts.get("Puwede", 0))
            + (POINTS_DAPLIS * self.counts.get("Daplis", 0))
        )
        max_possible_points = POINTS_SWAK * self.total_notes
        return (weighted_points / max_possible_points) * 100.0

    def get_stats(self) -> Dict[str, object]:
        """Returns snapshot of current scoring stats."""
        return {
            "score": self.score,
            "current_combo": self.current_combo,
            "max_combo": self.max_combo,
            "total_notes": self.total_notes,
            "accuracy": self.accuracy,
            "counts": dict(self.counts),
        }

    def reset(self) -> None:
        """Resets all metrics to clean round start values."""
        self.score = 0
        self.current_combo = 0
        self.max_combo = 0
        self.total_notes = 0
        for key in self.counts:
            self.counts[key] = 0

    def destroy(self) -> None:
        """Unsubscribes from the event bus."""
        event_bus.unsubscribe(GameEvent.HIT_RESULT, self._on_hit_result)
