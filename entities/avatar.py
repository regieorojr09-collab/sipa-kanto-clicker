"""Player avatar entity with 7-state FSM, priority gating, input buffering, and procedural animations."""

import math
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
import pygame
from pygame.math import Vector2

from core.events import GameEvent, event_bus
from core.settings import (
    GROUND_Y,
    LOGICAL_CENTER_X,
    COLOR_SUNSHINE,
    COLOR_BRICK_RED,
    COLOR_RETRO_CYAN,
    COLOR_CARD_BORDER,
)


class AvatarState(Enum):
    """Animation states for the player avatar."""
    IDLE = auto()
    PAA_KICK = auto()       # Inside-foot kick
    TUHOD_KICK = auto()     # Knee bump
    SIKO_KICK = auto()      # Elbow rebound
    MISS_STUMBLE = auto()   # Failed kick stumble
    CELEBRATE = auto()      # Fist pump / combo celebration
    HIT_RECOVER = auto()    # Post-kick recovery return to stance


# Priority definitions (higher number overrides lower number)
STATE_PRIORITY: Dict[AvatarState, int] = {
    AvatarState.IDLE: 0,
    AvatarState.HIT_RECOVER: 1,
    AvatarState.CELEBRATE: 2,
    AvatarState.PAA_KICK: 3,
    AvatarState.TUHOD_KICK: 3,
    AvatarState.SIKO_KICK: 3,
    AvatarState.MISS_STUMBLE: 4,  # Highest priority, interrupts everything
}

# State configurations: (frame_count, frame_duration_ms, is_looping)
STATE_CONFIG: Dict[AvatarState, Tuple[int, float, bool]] = {
    AvatarState.IDLE: (4, 150.0, True),
    AvatarState.PAA_KICK: (6, 50.0, False),
    AvatarState.TUHOD_KICK: (5, 55.0, False),
    AvatarState.SIKO_KICK: (5, 55.0, False),
    AvatarState.MISS_STUMBLE: (8, 60.0, False),
    AvatarState.CELEBRATE: (6, 80.0, False),
    AvatarState.HIT_RECOVER: (3, 40.0, False),
}


def _generate_procedural_avatar_frames() -> Dict[AvatarState, List[pygame.Surface]]:
    """
    Generates stylized 2D street-baller sprite frames for all 7 states on 128x128 surfaces.
    Uses layered geometric shapes (head, sando undershirt, basketball shorts, limbs, chinelas).
    """
    frames_dict: Dict[AvatarState, List[pygame.Surface]] = {}
    frame_size = 128

    # Colors
    c_skin = (215, 155, 110)
    c_hair = (30, 25, 30)
    c_sando = (245, 245, 248)
    c_shorts = COLOR_BRICK_RED
    c_stripe = COLOR_SUNSHINE
    c_chinelas = (40, 42, 52)

    for state, (num_frames, _, _) in STATE_CONFIG.items():
        frame_list: List[pygame.Surface] = []

        for f in range(num_frames):
            surf = pygame.Surface((frame_size, frame_size), pygame.SRCALPHA)
            base_x, base_y = 64, 116  # Feet rest near y=116

            # Animation offsets
            if state == AvatarState.IDLE:
                bob = int(math.sin(f * (math.pi / 2.0)) * 2.0)
                # Head
                pygame.draw.circle(surf, c_skin, (base_x, base_y - 68 + bob), 12)
                pygame.draw.circle(surf, c_hair, (base_x, base_y - 74 + bob), 12)
                # Torso / Sando
                pygame.draw.rect(surf, c_sando, (base_x - 12, base_y - 56 + bob, 24, 28), border_radius=4)
                # Shorts
                pygame.draw.rect(surf, c_shorts, (base_x - 13, base_y - 30 + bob, 26, 16), border_radius=3)
                pygame.draw.line(surf, c_stripe, (base_x + 10, base_y - 30 + bob), (base_x + 10, base_y - 14 + bob), 2)
                # Legs
                pygame.draw.line(surf, c_skin, (base_x - 7, base_y - 14 + bob), (base_x - 7, base_y), 5)
                pygame.draw.line(surf, c_skin, (base_x + 7, base_y - 14 + bob), (base_x + 7, base_y), 5)
                # Chinelas / Shoes
                pygame.draw.rect(surf, c_chinelas, (base_x - 12, base_y - 2, 11, 4), border_radius=2)
                pygame.draw.rect(surf, c_chinelas, (base_x + 3, base_y - 2, 11, 4), border_radius=2)
                # Arms resting
                pygame.draw.line(surf, c_skin, (base_x - 13, base_y - 52 + bob), (base_x - 16, base_y - 32 + bob), 4)
                pygame.draw.line(surf, c_skin, (base_x + 13, base_y - 52 + bob), (base_x + 16, base_y - 32 + bob), 4)

            elif state == AvatarState.PAA_KICK:
                # Inside-foot kick: right leg sweeps inward and foot angles up
                progress = f / max(1, num_frames - 1)
                leg_lift = math.sin(progress * math.pi) * 32.0

                # Head & Torso leaning slightly back
                pygame.draw.circle(surf, c_skin, (base_x - 6, base_y - 70), 12)
                pygame.draw.circle(surf, c_hair, (base_x - 6, base_y - 76), 12)
                pygame.draw.rect(surf, c_sando, (base_x - 16, base_y - 58, 24, 28), border_radius=4)
                pygame.draw.rect(surf, c_shorts, (base_x - 17, base_y - 32, 26, 16), border_radius=3)

                # Standing support leg (left)
                pygame.draw.line(surf, c_skin, (base_x - 10, base_y - 16), (base_x - 10, base_y), 5)
                pygame.draw.rect(surf, c_chinelas, (base_x - 15, base_y - 2, 11, 4), border_radius=2)

                # Kicking leg (sweeping inward up)
                knee_x = base_x + 6 + (progress * 8.0)
                knee_y = base_y - 20 - (leg_lift * 0.6)
                foot_x = base_x + 18 + (progress * 16.0)
                foot_y = base_y - 10 - leg_lift
                pygame.draw.line(surf, c_skin, (base_x + 4, base_y - 16), (int(knee_x), int(knee_y)), 5)
                pygame.draw.line(surf, c_skin, (int(knee_x), int(knee_y)), (int(foot_x), int(foot_y)), 5)
                pygame.draw.rect(surf, c_chinelas, (int(foot_x) - 4, int(foot_y) - 6, 12, 5), border_radius=2)

                # Outstretched arms for balance
                pygame.draw.line(surf, c_skin, (base_x - 16, base_y - 54), (base_x - 30, base_y - 40), 4)
                pygame.draw.line(surf, c_skin, (base_x + 8, base_y - 54), (base_x + 28, base_y - 48), 4)

            elif state == AvatarState.TUHOD_KICK:
                # Knee bump: right knee thrusts high up toward chest
                progress = f / max(1, num_frames - 1)
                knee_thrust = math.sin(progress * math.pi) * 36.0

                pygame.draw.circle(surf, c_skin, (base_x - 4, base_y - 68), 12)
                pygame.draw.circle(surf, c_hair, (base_x - 4, base_y - 74), 12)
                pygame.draw.rect(surf, c_sando, (base_x - 14, base_y - 56, 24, 28), border_radius=4)
                pygame.draw.rect(surf, c_shorts, (base_x - 15, base_y - 30, 26, 16), border_radius=3)

                # Left standing leg
                pygame.draw.line(surf, c_skin, (base_x - 8, base_y - 14), (base_x - 8, base_y), 5)
                pygame.draw.rect(surf, c_chinelas, (base_x - 13, base_y - 2, 11, 4), border_radius=2)

                # High knee bump
                high_knee_y = base_y - 20 - knee_thrust
                pygame.draw.line(surf, c_skin, (base_x + 6, base_y - 14), (base_x + 18, int(high_knee_y)), 6)
                pygame.draw.line(surf, c_skin, (base_x + 18, int(high_knee_y)), (base_x + 10, int(high_knee_y) + 20), 5)

                # Arms raised
                pygame.draw.line(surf, c_skin, (base_x - 14, base_y - 52), (base_x - 24, base_y - 64), 4)
                pygame.draw.line(surf, c_skin, (base_x + 10, base_y - 52), (base_x + 22, base_y - 64), 4)

            elif state == AvatarState.SIKO_KICK:
                # Elbow rebound: low crouch with elbow dropped/angled downward
                progress = f / max(1, num_frames - 1)
                elbow_drop = math.sin(progress * math.pi) * 16.0

                pygame.draw.circle(surf, c_skin, (base_x - 2, base_y - 58 + int(elbow_drop)), 12)
                pygame.draw.circle(surf, c_hair, (base_x - 2, base_y - 64 + int(elbow_drop)), 12)
                pygame.draw.rect(surf, c_sando, (base_x - 14, base_y - 46 + int(elbow_drop), 24, 28), border_radius=4)
                pygame.draw.rect(surf, c_shorts, (base_x - 15, base_y - 22, 26, 16), border_radius=3)

                # Legs bent in crouch
                pygame.draw.line(surf, c_skin, (base_x - 8, base_y - 8), (base_x - 12, base_y), 5)
                pygame.draw.line(surf, c_skin, (base_x + 8, base_y - 8), (base_x + 12, base_y), 5)
                pygame.draw.rect(surf, c_chinelas, (base_x - 16, base_y - 2, 11, 4), border_radius=2)
                pygame.draw.rect(surf, c_chinelas, (base_x + 8, base_y - 2, 11, 4), border_radius=2)

                # Angled sharp elbow strike
                elbow_x = base_x + 18
                elbow_y = base_y - 36 + int(elbow_drop * 1.4)
                pygame.draw.line(surf, c_skin, (base_x + 10, base_y - 42 + int(elbow_drop)), (int(elbow_x), int(elbow_y)), 5)
                pygame.draw.line(surf, c_skin, (int(elbow_x), int(elbow_y)), (base_x + 8, int(elbow_y) - 14), 4)

            elif state == AvatarState.MISS_STUMBLE:
                # Stumble: off-balance tilt, flailing arms
                tilt = math.sin((f / max(1, num_frames - 1)) * math.pi) * 16.0
                pygame.draw.circle(surf, c_skin, (base_x + int(tilt * 1.2), base_y - 64), 12)
                pygame.draw.circle(surf, c_hair, (base_x + int(tilt * 1.2), base_y - 70), 12)
                pygame.draw.rect(surf, c_sando, (base_x - 12 + int(tilt), base_y - 52, 24, 28), border_radius=4)
                pygame.draw.rect(surf, c_shorts, (base_x - 13 + int(tilt * 0.7), base_y - 26, 26, 16), border_radius=3)
                # Flailing arms
                pygame.draw.line(surf, c_skin, (base_x - 12, base_y - 48), (base_x - 28, base_y - 66), 4)
                pygame.draw.line(surf, c_skin, (base_x + 12, base_y - 48), (base_x + 30, base_y - 36), 4)
                # Slipping legs
                pygame.draw.line(surf, c_skin, (base_x - 6, base_y - 12), (base_x - 16, base_y), 5)
                pygame.draw.line(surf, c_skin, (base_x + 8, base_y - 12), (base_x + 20, base_y), 5)

            elif state == AvatarState.CELEBRATE:
                # Fist pump: arm thrust in air
                bob = int(math.sin(f * (math.pi / 2.0)) * 4.0)
                pygame.draw.circle(surf, c_skin, (base_x, base_y - 72 + bob), 12)
                pygame.draw.circle(surf, c_hair, (base_x, base_y - 78 + bob), 12)
                pygame.draw.rect(surf, c_sando, (base_x - 12, base_y - 60 + bob, 24, 28), border_radius=4)
                pygame.draw.rect(surf, c_shorts, (base_x - 13, base_y - 34 + bob, 26, 16), border_radius=3)
                # Legs
                pygame.draw.line(surf, c_skin, (base_x - 7, base_y - 18 + bob), (base_x - 7, base_y), 5)
                pygame.draw.line(surf, c_skin, (base_x + 7, base_y - 18 + bob), (base_x + 7, base_y), 5)
                # Raised fist
                pygame.draw.line(surf, c_skin, (base_x + 12, base_y - 56 + bob), (base_x + 18, base_y - 82 + bob), 5)
                pygame.draw.circle(surf, c_skin, (base_x + 18, base_y - 84 + bob), 5)

            else:  # HIT_RECOVER
                # Smooth landing back toward idle
                pygame.draw.circle(surf, c_skin, (base_x, base_y - 67), 12)
                pygame.draw.circle(surf, c_hair, (base_x, base_y - 73), 12)
                pygame.draw.rect(surf, c_sando, (base_x - 12, base_y - 55, 24, 28), border_radius=4)
                pygame.draw.rect(surf, c_shorts, (base_x - 13, base_y - 29, 26, 16), border_radius=3)
                pygame.draw.line(surf, c_skin, (base_x - 7, base_y - 13), (base_x - 7, base_y), 5)
                pygame.draw.line(surf, c_skin, (base_x + 7, base_y - 13), (base_x + 7, base_y), 5)

            frame_list.append(surf)

        frames_dict[state] = frame_list

    return frames_dict


class Avatar:
    """
    Player character entity driven by a priority-gated animation state machine
    with an input buffer (200ms) and dynamic tracking near the kick zone.
    """

    def __init__(self, x: float = 460.0, y: float = GROUND_Y) -> None:
        self.pos: Vector2 = Vector2(x, y)
        self.target_x: float = x
        self.facing_right: bool = True

        # State Machine
        self.current_state: AvatarState = AvatarState.IDLE
        self.frame_index: int = 0
        self.frame_timer_ms: float = 0.0

        # Input buffer: stores (AvatarState, timestamp_sec)
        self.buffered_state: Optional[AvatarState] = None
        self.buffered_time_sec: float = 0.0
        self.buffer_window_sec: float = 0.20  # 200 ms buffer window

        # Procedural sprite cache
        self.frames: Dict[AvatarState, List[pygame.Surface]] = _generate_procedural_avatar_frames()

        # Subscribe to gameplay events
        event_bus.subscribe(GameEvent.HIT_RESULT, self._on_hit_result)
        event_bus.subscribe(GameEvent.SIPA_LANDED, self._on_sipa_landed)

    @property
    def is_locked(self) -> bool:
        """Returns True if current animation cannot be interrupted by another kick."""
        return self.current_state in (
            AvatarState.PAA_KICK,
            AvatarState.TUHOD_KICK,
            AvatarState.SIKO_KICK,
            AvatarState.MISS_STUMBLE,
        )

    def request_state(self, new_state: AvatarState, current_time_sec: float = 0.0) -> bool:
        """
        Requests a state change adhering to priority gating:
        - MISS_STUMBLE (Priority 4) overrides everything immediately.
        - Kicks (Priority 3) during another kick are queued in the 200ms input buffer.
        - Idle/Recover/Celebrate transitions immediately.
        """
        new_priority = STATE_PRIORITY[new_state]
        curr_priority = STATE_PRIORITY[self.current_state]

        # Highest priority (Miss stumble) interrupts immediately
        if new_priority > curr_priority:
            self._set_state(new_state)
            self.buffered_state = None
            return True

        # If currently locked in an active kick, buffer the input
        if self.is_locked:
            if new_state in (AvatarState.PAA_KICK, AvatarState.TUHOD_KICK, AvatarState.SIKO_KICK):
                self.buffered_state = new_state
                self.buffered_time_sec = current_time_sec
                return False

        # Otherwise transition immediately
        self._set_state(new_state)
        return True

    def _set_state(self, state: AvatarState) -> None:
        """Internal immediate state transition."""
        self.current_state = state
        self.frame_index = 0
        self.frame_timer_ms = 0.0

    def _on_hit_result(self, judgment: str, was_miss: bool = False, position: tuple = (0, 0), **kwargs) -> None:
        """Triggers appropriate kick or stumble state based on hit judgment."""
        current_time_sec = pygame.time.get_ticks() / 1000.0

        if was_miss or judgment == "Bagsak!":
            self.request_state(AvatarState.MISS_STUMBLE, current_time_sec)
        else:
            # Pick kick type based on hit target vertical height:
            # Low target (> 500) -> Inside foot (Paa)
            # Mid target (440 - 500) -> Knee bump (Tuhod)
            # High target (< 440) -> Elbow rebound (Siko)
            target_y = position[1] if isinstance(position, (tuple, list)) else 520.0
            if target_y > 490.0:
                kick_type = AvatarState.PAA_KICK
            elif target_y >= 430.0:
                kick_type = AvatarState.TUHOD_KICK
            else:
                kick_type = AvatarState.SIKO_KICK

            self.request_state(kick_type, current_time_sec)

    def _on_sipa_landed(self, was_miss: bool = False, **kwargs) -> None:
        """Reacts to sipa touching pavement."""
        if was_miss:
            current_time_sec = pygame.time.get_ticks() / 1000.0
            self.request_state(AvatarState.MISS_STUMBLE, current_time_sec)

    def update(self, dt: float, current_time_sec: float = 0.0) -> None:
        """Advances animation frames, handles state completion, and tracks target position."""
        num_frames, frame_dur_ms, is_looping = STATE_CONFIG[self.current_state]
        self.frame_timer_ms += dt * 1000.0

        if self.frame_timer_ms >= frame_dur_ms:
            self.frame_timer_ms -= frame_dur_ms
            self.frame_index += 1

            if self.frame_index >= num_frames:
                if is_looping:
                    self.frame_index = 0
                else:
                    # Non-looping animation finished
                    self._on_animation_complete(current_time_sec)

        # Smooth horizontal lerp toward target_x
        self.pos.x += (self.target_x - self.pos.x) * min(1.0, 6.0 * dt)

    def _on_animation_complete(self, current_time_sec: float) -> None:
        """Handles transitions at the end of a non-looping animation."""
        if self.current_state in (AvatarState.PAA_KICK, AvatarState.TUHOD_KICK, AvatarState.SIKO_KICK):
            # Check if an input was buffered within the 200ms window
            if self.buffered_state and (current_time_sec - self.buffered_time_sec <= self.buffer_window_sec):
                next_kick = self.buffered_state
                self.buffered_state = None
                self._set_state(next_kick)
            else:
                self.buffered_state = None
                self._set_state(AvatarState.HIT_RECOVER)

        elif self.current_state == AvatarState.HIT_RECOVER:
            self._set_state(AvatarState.IDLE)

        elif self.current_state in (AvatarState.MISS_STUMBLE, AvatarState.CELEBRATE):
            self._set_state(AvatarState.IDLE)

    def track_position(self, target_x: float) -> None:
        """Directs the avatar to face and follow a target horizontal position on court."""
        # Offset avatar slightly behind target so the kick hits forward
        self.facing_right = target_x >= self.pos.x
        offset = -40.0 if self.facing_right else 40.0
        self.target_x = max(180.0, min(1100.0, target_x + offset))

    def draw(self, surface: pygame.Surface) -> None:
        """Renders the current frame, flipped horizontally if facing left."""
        frame_list = self.frames.get(self.current_state, self.frames[AvatarState.IDLE])
        safe_index = min(self.frame_index, len(frame_list) - 1)
        frame_surf = frame_list[safe_index]

        if not self.facing_right:
            frame_surf = pygame.transform.flip(frame_surf, True, False)

        # Draw centered horizontally, with feet on pos.y (GROUND_Y)
        draw_x = int(self.pos.x - 64)
        draw_y = int(self.pos.y - 116)
        surface.blit(frame_surf, (draw_x, draw_y))

    def destroy(self) -> None:
        """Unsubscribes from event bus."""
        event_bus.unsubscribe(GameEvent.HIT_RESULT, self._on_hit_result)
        event_bus.unsubscribe(GameEvent.SIPA_LANDED, self._on_sipa_landed)
