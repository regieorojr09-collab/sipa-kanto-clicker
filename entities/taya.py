"""Taya NPC director entity: AI state machine, taunt/callout reactions, and procedural sprite rendering."""

import math
import random
from enum import Enum, auto
from typing import Dict, List, Optional, Tuple
import pygame
from pygame.math import Vector2

from core.events import GameEvent, event_bus
from core.settings import (
    GROUND_Y,
    COLOR_SUNSHINE,
    COLOR_BRICK_RED,
    COLOR_RETRO_CYAN,
    COLOR_TEXT_PRIMARY,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
)


class TayaState(Enum):
    """Behavioral and animation states for the Taya NPC director."""
    OBSERVING = auto()  # Idle watchful stance on sideline
    CALLING = auto()    # Calling out serves or round start ("Salo!", "Tira!")
    TAUNTING = auto()   # Pointing and laughing on player miss ("Bagsak!", "Kaya pa?")
    IMPRESSED = auto()  # Wide-eyed shock on high combos ("Lakas mo ah!")
    PIKON_RAGE = auto() # Gritting teeth / shaking fist at extreme combos
    MOCKING = auto()    # Dismissive shrugging ("Daplis lang pala!")


def _generate_procedural_taya_frames() -> Dict[TayaState, List[pygame.Surface]]:
    """Generates procedural 128x128 sprite frames for the Taya character."""
    frames_dict: Dict[TayaState, List[pygame.Surface]] = {}
    frame_size = 128

    c_skin = (195, 140, 95)
    c_cap = (45, 50, 68)
    c_shirt = COLOR_SUNSHINE
    c_shorts = (35, 40, 52)
    c_towel = (240, 242, 245)

    states = [
        (TayaState.OBSERVING, 4),
        (TayaState.CALLING, 4),
        (TayaState.TAUNTING, 4),
        (TayaState.IMPRESSED, 4),
        (TayaState.PIKON_RAGE, 4),
        (TayaState.MOCKING, 4),
    ]

    for state, num_frames in states:
        frame_list: List[pygame.Surface] = []

        for f in range(num_frames):
            surf = pygame.Surface((frame_size, frame_size), pygame.SRCALPHA)
            base_x, base_y = 64, 116
            bob = int(math.sin(f * (math.pi / 2.0)) * 2.0)

            # Head & Backwards Cap
            head_y = base_y - 68 + bob
            pygame.draw.circle(surf, c_skin, (base_x, head_y), 13)
            # Cap crown + backwards brim
            pygame.draw.circle(surf, c_cap, (base_x, head_y - 6), 13)
            pygame.draw.rect(surf, c_cap, (base_x - 14, head_y - 6, 8, 4), border_radius=1)

            # Torso / Bright yellow street shirt
            pygame.draw.rect(surf, c_shirt, (base_x - 13, base_y - 54 + bob, 26, 28), border_radius=4)
            # Good luck towel draped over shoulder
            pygame.draw.rect(surf, c_towel, (base_x - 14, base_y - 56 + bob, 7, 24), border_radius=2)

            # Shorts & Legs
            pygame.draw.rect(surf, c_shorts, (base_x - 13, base_y - 28 + bob, 26, 16), border_radius=3)
            pygame.draw.line(surf, c_skin, (base_x - 7, base_y - 12 + bob), (base_x - 7, base_y), 5)
            pygame.draw.line(surf, c_skin, (base_x + 7, base_y - 12 + bob), (base_x + 7, base_y), 5)

            # State-specific arm poses and expressions
            if state == TayaState.OBSERVING:
                # Crossed arms across chest
                pygame.draw.line(surf, c_skin, (base_x - 14, base_y - 48 + bob), (base_x + 14, base_y - 42 + bob), 5)
                pygame.draw.line(surf, c_skin, (base_x + 14, base_y - 48 + bob), (base_x - 14, base_y - 42 + bob), 5)

            elif state == TayaState.CALLING:
                # Hand cupped to mouth shouting
                pygame.draw.line(surf, c_skin, (base_x + 12, base_y - 50 + bob), (base_x + 16, head_y + 2), 4)
                pygame.draw.circle(surf, c_skin, (base_x + 16, head_y + 2), 4)
                # Left hand on hip
                pygame.draw.line(surf, c_skin, (base_x - 13, base_y - 50 + bob), (base_x - 20, base_y - 36 + bob), 4)

            elif state == TayaState.TAUNTING:
                # Right arm pointing forward, laughing
                point_extend = 18 + (f * 3)
                pygame.draw.line(surf, c_skin, (base_x + 12, base_y - 50 + bob), (base_x + point_extend, base_y - 50 + bob), 5)
                pygame.draw.circle(surf, c_skin, (base_x + point_extend + 2, base_y - 50 + bob), 4)
                # Left hand on hip
                pygame.draw.line(surf, c_skin, (base_x - 13, base_y - 50 + bob), (base_x - 20, base_y - 36 + bob), 4)

            elif state == TayaState.IMPRESSED:
                # Hands clutched to head in disbelief
                pygame.draw.line(surf, c_skin, (base_x - 13, base_y - 50 + bob), (base_x - 16, head_y - 2), 4)
                pygame.draw.line(surf, c_skin, (base_x + 13, base_y - 50 + bob), (base_x + 16, head_y - 2), 4)

            elif state == TayaState.PIKON_RAGE:
                # Clenched fists raised, trembling
                tremble = (f % 2) * 2 - 1
                pygame.draw.line(surf, c_skin, (base_x - 13, base_y - 50 + bob), (base_x - 22 + tremble, base_y - 68 + bob), 5)
                pygame.draw.line(surf, c_skin, (base_x + 13, base_y - 50 + bob), (base_x + 22 + tremble, base_y - 68 + bob), 5)
                pygame.draw.circle(surf, (230, 45, 45), (base_x - 22 + tremble, base_y - 70 + bob), 5)
                pygame.draw.circle(surf, (230, 45, 45), (base_x + 22 + tremble, base_y - 70 + bob), 5)

            else:  # MOCKING
                # Shrugging arms out
                pygame.draw.line(surf, c_skin, (base_x - 13, base_y - 50 + bob), (base_x - 26, base_y - 56 + bob), 4)
                pygame.draw.line(surf, c_skin, (base_x + 13, base_y - 50 + bob), (base_x + 26, base_y - 56 + bob), 4)

            frame_list.append(surf)

        frames_dict[state] = frame_list

    return frames_dict


class Taya:
    """
    Taya (challenger/game master) NPC standing on the left court sideline.
    Observes gameplay, calls serves, and reacts to player combos or misses
    with animated poses and street callout speech bubbles.
    """

    def __init__(self, x: float = 130.0, y: float = GROUND_Y) -> None:
        self.pos: Vector2 = Vector2(x, y)
        self.current_state: TayaState = TayaState.OBSERVING
        self.state_timer: float = 0.0

        # Animation playback
        self.frame_index: int = 0
        self.frame_timer_ms: float = 0.0
        self.frame_duration_ms: float = 140.0
        self.frames: Dict[TayaState, List[pygame.Surface]] = _generate_procedural_taya_frames()

        # Speech bubble / Callout text
        self.callout_text: Optional[str] = None
        self.callout_lifetime: float = 0.0
        self.callout_color: Tuple[int, int, int] = COLOR_TEXT_PRIMARY
        self.font_callout: Optional[pygame.font.Font] = None

        # Subscribe to gameplay events
        event_bus.subscribe(GameEvent.HIT_RESULT, self._on_hit_result)
        event_bus.subscribe(GameEvent.SIPA_LANDED, self._on_sipa_landed)
        event_bus.subscribe(GameEvent.COMBO_MILESTONE, self._on_combo_milestone)
        event_bus.subscribe(GameEvent.ROUND_START, self._on_round_start)
        event_bus.subscribe(GameEvent.PIKON_THRESHOLD, self._on_pikon_threshold)

    def _init_fonts(self) -> None:
        if self.font_callout is None:
            self.font_callout = pygame.font.Font(None, 24)

    def _on_pikon_threshold(self, level: int = 30, modifier: str = "", **kwargs) -> None:
        """Reacts dynamically when player pushes Pikon meter across difficulty thresholds."""
        if level >= 95:
            self.set_state(TayaState.PIKON_RAGE, duration=2.2, callout="Wala kang ligtas!", color=COLOR_BRICK_RED)
        elif level >= 80:
            self.set_state(TayaState.PIKON_RAGE, duration=2.0, callout="Pikon na 'ko ah!", color=COLOR_BRICK_RED)
        elif level == 65:
            self.set_state(TayaState.TAUNTING, duration=1.6, callout="Kayanin mo dalawa!", color=COLOR_SUNSHINE)
        elif level == 50:
            self.set_state(TayaState.TAUNTING, duration=1.6, callout="Bibilisan natin!", color=COLOR_SUNSHINE)
        elif level == 30:
            self.set_state(TayaState.CALLING, duration=1.6, callout="Mahangin ba?!", color=COLOR_RETRO_CYAN)

    def set_state(self, new_state: TayaState, duration: float = 1.4, callout: Optional[str] = None, color: Tuple[int, int, int] = COLOR_TEXT_PRIMARY) -> None:
        """Transitions Taya into a temporary reaction state with an optional speech bubble."""
        self.current_state = new_state
        self.state_timer = duration
        self.frame_index = 0
        self.frame_timer_ms = 0.0

        if callout:
            self.callout_text = callout
            self.callout_lifetime = duration
            self.callout_color = color

    def _on_hit_result(self, judgment: str, was_miss: bool = False, **kwargs) -> None:
        """Reacts to hit accuracy."""
        if was_miss or judgment == "Bagsak!":
            taunts = ["Bagsak!", "Pano yan?", "Nadale ka!", "Kaya pa ba?", "Ay, nadulas!"]
            self.set_state(
                TayaState.TAUNTING,
                duration=1.5,
                callout=random.choice(taunts),
                color=COLOR_BRICK_RED
            )

    def _on_sipa_landed(self, was_miss: bool = False, **kwargs) -> None:
        """Reacts to grounded sipa."""
        if was_miss and self.current_state not in (TayaState.TAUNTING, TayaState.MOCKING):
            self.set_state(
                TayaState.MOCKING,
                duration=1.4,
                callout="Lupa na!",
                color=COLOR_BRICK_RED
            )

    def _on_combo_milestone(self, combo_count: int = 10, **kwargs) -> None:
        """Reacts to player building high combos."""
        if combo_count >= 20:
            self.set_state(
                TayaState.PIKON_RAGE,
                duration=1.8,
                callout="Pikon na 'ko ah!",
                color=COLOR_BRICK_RED
            )
        else:
            compliments = ["Lakas mo ah!", "Swak na swak!", "Galing!", "Tuloy mo lang!"]
            self.set_state(
                TayaState.IMPRESSED,
                duration=1.5,
                callout=random.choice(compliments),
                color=COLOR_RETRO_CYAN
            )

    def _on_round_start(self, **kwargs) -> None:
        """Shouts callout when round begins."""
        self.set_state(TayaState.CALLING, duration=1.2, callout="Salo!", color=COLOR_SUNSHINE)

    def trigger_serve_call(self) -> None:
        """Called when a new serve is launched."""
        calls = ["Salo!", "Tira na!", "Handa!", "Habol!"]
        self.set_state(TayaState.CALLING, duration=1.2, callout=random.choice(calls), color=COLOR_SUNSHINE)

    def update(self, dt: float) -> None:
        """Updates frame animation and speech bubble timer."""
        # Animation loop
        frame_list = self.frames.get(self.current_state, self.frames[TayaState.OBSERVING])
        self.frame_timer_ms += dt * 1000.0
        if self.frame_timer_ms >= self.frame_duration_ms:
            self.frame_timer_ms -= self.frame_duration_ms
            self.frame_index = (self.frame_index + 1) % len(frame_list)

        # Timed state transition back to OBSERVING
        if self.current_state != TayaState.OBSERVING:
            self.state_timer -= dt
            if self.state_timer <= 0.0:
                self.current_state = TayaState.OBSERVING
                self.frame_index = 0

        # Speech bubble decay
        if self.callout_lifetime > 0.0:
            self.callout_lifetime -= dt
            if self.callout_lifetime <= 0.0:
                self.callout_text = None

    def draw(self, surface: pygame.Surface) -> None:
        """Renders Taya sprite and active speech bubble."""
        self._init_fonts()
        frame_list = self.frames.get(self.current_state, self.frames[TayaState.OBSERVING])
        safe_idx = self.frame_index % len(frame_list)
        surf_frame = frame_list[safe_idx]

        # Taya faces right toward center court
        draw_x = int(self.pos.x - 64)
        draw_y = int(self.pos.y - 116)
        surface.blit(surf_frame, (draw_x, draw_y))

        # Speech Bubble / Callout Text
        if self.callout_text and self.callout_lifetime > 0.0 and self.font_callout:
            surf_txt = self.font_callout.render(self.callout_text, True, self.callout_color)
            txt_w = surf_txt.get_width()
            txt_h = surf_txt.get_height()

            bubble_rect = pygame.Rect(
                draw_x + 32,
                draw_y - 28,
                txt_w + 16,
                txt_h + 10
            )

            # Bubble background + outline
            pygame.draw.rect(surface, COLOR_CARD_BG, bubble_rect, border_radius=6)
            pygame.draw.rect(surface, COLOR_CARD_BORDER, bubble_rect, width=1, border_radius=6)
            surface.blit(surf_txt, (bubble_rect.x + 8, bubble_rect.y + 5))

    def destroy(self) -> None:
        """Unsubscribes from event bus."""
        event_bus.unsubscribe(GameEvent.HIT_RESULT, self._on_hit_result)
        event_bus.unsubscribe(GameEvent.SIPA_LANDED, self._on_sipa_landed)
        event_bus.unsubscribe(GameEvent.COMBO_MILESTONE, self._on_combo_milestone)
        event_bus.unsubscribe(GameEvent.ROUND_START, self._on_round_start)
        event_bus.unsubscribe(GameEvent.PIKON_THRESHOLD, self._on_pikon_threshold)
