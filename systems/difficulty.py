"""Difficulty controller, dynamic Pikon Meter, and Taya modifier manager for Sipa: Kanto Clicker."""

from enum import Enum
from typing import Dict, Optional, Set
import pygame

from core.events import GameEvent, event_bus
from core.settings import (
    POINTS_SWAK,
    POINTS_PUWEDE,
    POINTS_DAPLIS,
    POINTS_BAGSAK,
)


class DifficultyLevel(Enum):
    """Preset difficulty configurations with score multipliers and base parameters."""
    MADALI = ("Madali", 1.0, 5.0, 0.8)      # Easy: 1.0x score, AR 5, slower pikon gain
    SAKTO = ("Sakto", 1.5, 6.0, 1.0)        # Normal: 1.5x score, AR 6, standard pikon
    MAHIRAP = ("Mahirap", 2.5, 7.5, 1.3)    # Hard: 2.5x score, AR 7.5, fast pikon
    PIKON = ("Pikon Mode", 4.0, 9.0, 1.6)   # Extreme: 4.0x score, AR 9, aggressive modifiers

    def __init__(self, display_name: str, score_mult: float, base_ar: float, pikon_rate: float) -> None:
        self.display_name: str = display_name
        self.score_mult: float = score_mult
        self.base_ar: float = base_ar
        self.pikon_rate: float = pikon_rate


class DifficultyController:
    """
    Manages the Pikon Meter (annoyance gauge) and escalates game modifiers.
    Pikon Meter builds with player success, decays when idle, and drops on miss.
    Crossing thresholds unlocks modifiers (Hangin wind drift, Bilis rapid approach, Dalawa double target).
    """

    THRESHOLDS = [30, 50, 65, 80, 95]

    def __init__(self, level: DifficultyLevel = DifficultyLevel.SAKTO) -> None:
        self.level: DifficultyLevel = level
        self.pikon_meter: float = 0.0  # Range: 0.0 to 100.0%
        self.idle_timer: float = 0.0
        self.triggered_thresholds: Set[int] = set()

        # Active gameplay modifiers
        self.wind_force: float = 0.0          # Lateral acceleration (px/s^2)
        self.approach_rate_mult: float = 1.0  # Duration factor for approach rings (e.g. 0.8 = 20% faster)
        self.double_target: bool = False      # Spawns secondary quick targets
        self.chaos_offset: bool = False       # Random spatial position jitter

        # Subscribe to hit results
        event_bus.subscribe(GameEvent.HIT_RESULT, self._on_hit_result)
        event_bus.subscribe(GameEvent.SIPA_LANDED, self._on_sipa_landed)

    def _on_hit_result(self, judgment: str, was_miss: bool = False, **kwargs) -> None:
        """Adjusts Pikon Meter based on player precision."""
        self.idle_timer = 0.0

        if was_miss or judgment == "Bagsak!":
            # Player dropped the sipa: Taya calms down / mocks
            self.pikon_meter = max(0.0, self.pikon_meter - 15.0)
            self._rearm_thresholds()
        else:
            # Player scored: Taya's annoyance builds up
            base_gain = 5.0 if judgment == "Swak!" else (3.0 if judgment == "Puwede" else 1.0)
            # High combo multiplier on pikon build
            combo = kwargs.get("combo", 0)
            combo_mult = 1.5 if combo >= 10 else 1.0

            gain = base_gain * combo_mult * self.level.pikon_rate
            self.pikon_meter = min(100.0, self.pikon_meter + gain)
            self._check_threshold_crossings()

        self._update_modifiers()

    def _on_sipa_landed(self, was_miss: bool = False, **kwargs) -> None:
        """Ground landing reset on miss."""
        if was_miss:
            self.idle_timer = 0.0
            self.pikon_meter = max(0.0, self.pikon_meter - 15.0)
            self._rearm_thresholds()
            self._update_modifiers()

    def _check_threshold_crossings(self) -> None:
        """Publishes GameEvent.PIKON_THRESHOLD when crossing defined annoyance levels."""
        for t in self.THRESHOLDS:
            if self.pikon_meter >= t and t not in self.triggered_thresholds:
                self.triggered_thresholds.add(t)
                modifier_name = self._get_modifier_name(t)
                event_bus.publish(GameEvent.PIKON_THRESHOLD, level=t, modifier=modifier_name)

    def _rearm_thresholds(self) -> None:
        """Re-arms threshold triggers if pikon falls comfortably below them."""
        self.triggered_thresholds = {t for t in self.triggered_thresholds if self.pikon_meter >= (t - 6)}

    def _get_modifier_name(self, threshold: int) -> str:
        if threshold == 30:
            return "Hangin"
        elif threshold == 50:
            return "Bilis"
        elif threshold == 65:
            return "Dalawa"
        elif threshold == 80:
            return "Pikon Rage"
        else:
            return "Loko-Loko"

    def _update_modifiers(self) -> None:
        """Recalculates active gameplay modifiers based on current Pikon level and difficulty."""
        # 1. Wind Force (Hangin modifier at >= 30%)
        if self.pikon_meter >= 30.0 or self.level in (DifficultyLevel.MAHIRAP, DifficultyLevel.PIKON):
            # Scale wind with pikon intensity (between 80 to 180 px/s^2)
            intensity = (self.pikon_meter / 100.0)
            direction = 1.0 if (int(self.pikon_meter) % 2 == 0) else -1.0
            self.wind_force = direction * (80.0 + (100.0 * intensity))
        else:
            self.wind_force = 0.0

        # 2. Approach Rate Speed-Up (Bilis modifier at >= 50%)
        if self.pikon_meter >= 80.0 or self.level == DifficultyLevel.PIKON:
            self.approach_rate_mult = 0.70  # 30% faster ring duration
        elif self.pikon_meter >= 50.0 or self.level == DifficultyLevel.MAHIRAP:
            self.approach_rate_mult = 0.80  # 20% faster ring duration
        else:
            self.approach_rate_mult = 1.0

        # 3. Double Target Sequential Kicks (Dalawa modifier at >= 65%)
        self.double_target = (self.pikon_meter >= 65.0) or (self.level == DifficultyLevel.PIKON)

        # 4. Chaos Jitter (Loko-Loko at >= 95%)
        self.chaos_offset = (self.pikon_meter >= 95.0)

    def update(self, dt: float) -> None:
        """Passively decays Pikon Meter when player has been idle for > 3 seconds."""
        self.idle_timer += dt
        if self.idle_timer > 3.0:
            if self.pikon_meter > 0.0:
                # Decays at -2.0% per second
                self.pikon_meter = max(0.0, self.pikon_meter - (2.0 * dt))
                self._rearm_thresholds()
                self._update_modifiers()

    def get_stats(self) -> Dict[str, object]:
        """Returns snapshot of current difficulty and pikon metrics."""
        return {
            "level": self.level.display_name,
            "score_mult": self.level.score_mult,
            "pikon_meter": self.pikon_meter,
            "wind_force": self.wind_force,
            "approach_rate_mult": self.approach_rate_mult,
            "double_target": self.double_target,
        }

    def reset(self) -> None:
        """Resets pikon meter and modifiers for a new round."""
        self.pikon_meter = 0.0
        self.idle_timer = 0.0
        self.triggered_thresholds.clear()
        self.wind_force = 0.0
        self.approach_rate_mult = 1.0
        self.double_target = False
        self.chaos_offset = False

    def destroy(self) -> None:
        """Unsubscribes from the event bus."""
        event_bus.unsubscribe(GameEvent.HIT_RESULT, self._on_hit_result)
        event_bus.unsubscribe(GameEvent.SIPA_LANDED, self._on_sipa_landed)
