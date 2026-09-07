"""Hit detection, approach ring shrinking math, and timing accuracy judgments."""

import math
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
import pygame
from pygame.math import Vector2

from core.events import GameEvent, event_bus
from core.settings import (
    HIT_CIRCLE_RADIUS,
    APPROACH_RING_MAX_R,
    TIMING_SWAK_MS,
    TIMING_PUWEDE_MS,
    TIMING_DAPLIS_MS,
    POINTS_SWAK,
    POINTS_PUWEDE,
    POINTS_DAPLIS,
    POINTS_BAGSAK,
    COLOR_RETRO_CYAN,
    COLOR_SUNSHINE,
    COLOR_RETRO_MAGENTA,
    COLOR_CHALK,
)


class TargetState(Enum):
    """Lifecycle states of a HitTarget."""
    ACTIVE = auto()
    HIT = auto()
    EXPIRED = auto()


class HitTarget:
    """
    Rhythm hit target with an inner clickable circular zone and an outer shrinking approach ring.
    Color transitions smoothly: Cyan (early) -> Yellow (mid) -> Magenta/Red (at arrival).
    """

    def __init__(
        self,
        cx: float,
        cy: float,
        t_arrive: float,
        t_duration: float = 900.0,
        r_hit: float = HIT_CIRCLE_RADIUS,
        r_max: float = APPROACH_RING_MAX_R,
    ) -> None:
        self.cx: float = cx
        self.cy: float = cy
        self.t_arrive: float = t_arrive
        self.t_duration: float = max(100.0, t_duration)
        self.t_spawn: float = t_arrive - self.t_duration
        self.r_hit: float = r_hit
        self.r_max: float = r_max
        self.state: TargetState = TargetState.ACTIVE

    @property
    def is_active(self) -> bool:
        return self.state == TargetState.ACTIVE

    def get_current_ring_radius(self, current_time_ms: float) -> float:
        """
        Calculates current radius of the outer approach ring:
        Shrinks linearly from r_max to r_hit over t_duration.
        """
        if current_time_ms >= self.t_arrive:
            return self.r_hit

        remaining_ms = self.t_arrive - current_time_ms
        factor = max(0.0, min(1.0, remaining_ms / self.t_duration))
        return self.r_hit + ((self.r_max - self.r_hit) * factor)

    def get_ring_color(self, current_time_ms: float) -> Tuple[int, int, int]:
        """
        Interpolates color: Cyan (start, factor=1.0) -> Yellow (mid, factor=0.5) -> Magenta (factor=0.0).
        """
        if current_time_ms >= self.t_arrive:
            return COLOR_RETRO_MAGENTA

        factor = max(0.0, min(1.0, (self.t_arrive - current_time_ms) / self.t_duration))

        if factor >= 0.5:
            # Interpolate between Yellow (0.5) and Cyan (1.0)
            u = (factor - 0.5) / 0.5
            r = int((1.0 - u) * COLOR_SUNSHINE[0] + u * COLOR_RETRO_CYAN[0])
            g = int((1.0 - u) * COLOR_SUNSHINE[1] + u * COLOR_RETRO_CYAN[1])
            b = int((1.0 - u) * COLOR_SUNSHINE[2] + u * COLOR_RETRO_CYAN[2])
        else:
            # Interpolate between Magenta (0.0) and Yellow (0.5)
            u = factor / 0.5
            r = int((1.0 - u) * COLOR_RETRO_MAGENTA[0] + u * COLOR_SUNSHINE[0])
            g = int((1.0 - u) * COLOR_RETRO_MAGENTA[1] + u * COLOR_SUNSHINE[1])
            b = int((1.0 - u) * COLOR_RETRO_MAGENTA[2] + u * COLOR_SUNSHINE[2])

        return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))

    def draw(self, surface: pygame.Surface, current_time_ms: float) -> None:
        """Renders inner clickable circle and outer shrinking approach ring."""
        if not self.is_active:
            return

        cx, cy = int(self.cx), int(self.cy)
        ring_color = self.get_ring_color(current_time_ms)
        ring_r = int(self.get_current_ring_radius(current_time_ms))
        hit_r = int(self.r_hit)

        # 1. Inner Clickable Disc (Translucent card fill)
        disc_size = (hit_r * 2) + 4
        disc_surf = pygame.Surface((disc_size, disc_size), pygame.SRCALPHA)
        center_offset = (disc_size // 2, disc_size // 2)

        # Translucent body
        pygame.draw.circle(disc_surf, (*ring_color, 75), center_offset, hit_r)
        # Inner target boundary
        pygame.draw.circle(disc_surf, COLOR_CHALK, center_offset, hit_r, width=3)
        # Center bullseye dot
        pygame.draw.circle(disc_surf, (255, 255, 255), center_offset, 4)

        surface.blit(disc_surf, (cx - center_offset[0], cy - center_offset[1]))

        # 2. Outer Shrinking Approach Ring (Osu!-style)
        if ring_r > hit_r:
            pygame.draw.circle(surface, ring_color, (cx, cy), ring_r, width=3)


class HitSystem:
    """
    Manages active hit targets, executes Euclidean spatial hit detection,
    computes timing accuracy deltas, and dispatches hit judgment events.
    """

    def __init__(self) -> None:
        self.active_targets: List[HitTarget] = []

    def spawn_target(
        self,
        cx: float,
        cy: float,
        t_arrive: float,
        t_duration: float = 900.0,
        r_hit: float = HIT_CIRCLE_RADIUS,
    ) -> HitTarget:
        """Spawns a new HitTarget and queues it in the active targets list."""
        target = HitTarget(cx, cy, t_arrive, t_duration, r_hit)
        self.active_targets.append(target)
        # Keep sorted by arrival time
        self.active_targets.sort(key=lambda t: t.t_arrive)
        return target

    def check_hit(self, click_pos: Vector2, current_time_ms: float) -> Optional[Dict[str, object]]:
        """
        Evaluates a click against all active targets sorted by arrival time.
        Uses Euclidean distance for hit-circle bounds and millisecond delta for judgment.
        """
        for target in self.active_targets:
            if not target.is_active:
                continue

            # Euclidean spatial collision
            dx = click_pos.x - target.cx
            dy = click_pos.y - target.cy
            dist_sq = (dx * dx) + (dy * dy)

            if dist_sq <= (target.r_hit * target.r_hit):
                # Target clicked! Calculate timing error
                signed_delta_ms = current_time_ms - target.t_arrive
                abs_delta_ms = abs(signed_delta_ms)

                if abs_delta_ms <= TIMING_SWAK_MS:
                    judgment = "Swak!"
                    points = POINTS_SWAK
                elif abs_delta_ms <= TIMING_PUWEDE_MS:
                    judgment = "Puwede"
                    points = POINTS_PUWEDE
                elif abs_delta_ms <= TIMING_DAPLIS_MS:
                    judgment = "Daplis"
                    points = POINTS_DAPLIS
                else:
                    judgment = "Bagsak!"
                    points = POINTS_BAGSAK

                target.state = TargetState.HIT
                was_miss = (judgment == "Bagsak!")

                payload = {
                    "judgment": judgment,
                    "points": points,
                    "timing_delta_ms": signed_delta_ms,
                    "position": (target.cx, target.cy),
                    "target": target,
                    "was_miss": was_miss,
                }

                event_bus.publish(GameEvent.HIT_RESULT, **payload)
                return payload

        return None

    def update(self, current_time_ms: float) -> List[Dict[str, object]]:
        """
        Checks for expired targets that exceeded the maximum late timing window.
        Dispatches Bagsak! (miss) events for unhit expired targets.
        """
        expired_events: List[Dict[str, object]] = []

        for target in self.active_targets:
            if target.is_active and (current_time_ms - target.t_arrive) > TIMING_DAPLIS_MS:
                target.state = TargetState.EXPIRED

                payload = {
                    "judgment": "Bagsak!",
                    "points": POINTS_BAGSAK,
                    "timing_delta_ms": current_time_ms - target.t_arrive,
                    "position": (target.cx, target.cy),
                    "target": target,
                    "was_miss": True,
                }
                expired_events.append(payload)

                event_bus.publish(GameEvent.HIT_RESULT, **payload)
                event_bus.publish(GameEvent.SIPA_LANDED, position=(target.cx, target.cy), was_miss=True)

        # Prune inactive targets
        self.active_targets = [t for t in self.active_targets if t.is_active]
        return expired_events

    def draw(self, surface: pygame.Surface, current_time_ms: float) -> None:
        """Renders all currently active targets."""
        for target in self.active_targets:
            target.draw(surface, current_time_ms)

    def clear(self) -> None:
        """Clears all active targets."""
        self.active_targets.clear()
