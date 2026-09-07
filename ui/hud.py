"""In-game heads-up display (HUD) rendering score, combo, accuracy, and floating judgment feedback."""

import pygame
from pygame.math import Vector2
from typing import Dict, List, Optional, Tuple

from core.events import GameEvent, event_bus
from core.settings import (
    LOGICAL_W,
    COLOR_SUNSHINE,
    COLOR_BRICK_RED,
    COLOR_RETRO_CYAN,
    COLOR_NEON_GREEN,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_TASSEL_GOLD,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
)
from systems.scoring import ScoreKeeper


class FloatingJudgment:
    """Animated text pop-up indicating hit accuracy (Swak!, Puwede, Daplis, Bagsak!)."""

    def __init__(self, text: str, pos: Tuple[float, float], color: Tuple[int, int, int]) -> None:
        self.text: str = text
        self.pos: Vector2 = Vector2(pos[0], pos[1])
        self.color: Tuple[int, int, int] = color
        self.lifetime_ms: float = 600.0  # Fades out over 600 ms
        self.elapsed_ms: float = 0.0
        self.is_alive: bool = True

    def update(self, dt: float) -> None:
        self.elapsed_ms += dt * 1000.0
        # Drift upward
        self.pos.y -= 45.0 * dt
        if self.elapsed_ms >= self.lifetime_ms:
            self.is_alive = False

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        if not self.is_alive or self.elapsed_ms >= self.lifetime_ms:
            return

        alpha_factor = max(0.0, 1.0 - (self.elapsed_ms / self.lifetime_ms))
        alpha = int(alpha_factor * 255)

        # Render text with drop shadow
        text_surf = font.render(self.text, True, self.color)
        shadow_surf = font.render(self.text, True, (0, 0, 0))

        text_surf.set_alpha(alpha)
        shadow_surf.set_alpha(alpha)

        rect = text_surf.get_rect(center=(int(self.pos.x), int(self.pos.y)))
        surface.blit(shadow_surf, rect.move(2, 2))
        surface.blit(text_surf, rect)


class HUD:
    """
    Renders live gameplay status: Score, Combo count, Accuracy %, and floating judgments.
    """

    def __init__(self, score_keeper: ScoreKeeper) -> None:
        self.score_keeper: ScoreKeeper = score_keeper
        self.floating_judgments: List[FloatingJudgment] = []

        # Cached fonts
        self.font_score: Optional[pygame.font.Font] = None
        self.font_combo: Optional[pygame.font.Font] = None
        self.font_judgment: Optional[pygame.font.Font] = None
        self.font_label: Optional[pygame.font.Font] = None

        # Color map for judgments
        self._judgment_colors: Dict[str, Tuple[int, int, int]] = {
            "Swak!": COLOR_SUNSHINE,
            "Puwede": COLOR_RETRO_CYAN,
            "Daplis": COLOR_TASSEL_GOLD,
            "Bagsak!": COLOR_BRICK_RED,
        }

        # Subscribe to hit results for floating popups
        event_bus.subscribe(GameEvent.HIT_RESULT, self._on_hit_result)

    def _init_fonts(self) -> None:
        if self.font_score is None:
            self.font_score = pygame.font.Font(None, 52)
            self.font_combo = pygame.font.Font(None, 68)
            self.font_judgment = pygame.font.Font(None, 44)
            self.font_label = pygame.font.Font(None, 24)

    def _on_hit_result(
        self,
        judgment: str,
        position: Tuple[float, float] = (640.0, 360.0),
        **kwargs
    ) -> None:
        """Spawns floating judgment feedback at the hit coordinate."""
        color = self._judgment_colors.get(judgment, COLOR_TEXT_PRIMARY)
        # Position judgment slightly above the hit position
        popup_pos = (position[0], max(100.0, position[1] - 40.0))
        self.floating_judgments.append(FloatingJudgment(judgment, popup_pos, color))

    def update(self, dt: float) -> None:
        """Advances floating judgment animations and cleans up dead popups."""
        for j in self.floating_judgments:
            j.update(dt)
        self.floating_judgments = [j for j in self.floating_judgments if j.is_alive]

    def draw(self, surface: pygame.Surface) -> None:
        """Renders HUD panels, typography, and floating popups."""
        self._init_fonts()
        assert self.font_score and self.font_combo and self.font_label and self.font_judgment

        # 1. Top-Right Score Panel
        score_val = self.score_keeper.score
        score_str = f"{score_val:07d}"

        # Drop shadow
        surf_shadow = self.font_score.render(score_str, True, (0, 0, 0))
        surface.blit(surf_shadow, (LOGICAL_W - 228, 26))

        # Main score text
        surf_score = self.font_score.render(score_str, True, COLOR_SUNSHINE)
        surface.blit(surf_score, (LOGICAL_W - 230, 24))

        # Score label
        surf_score_lbl = self.font_label.render("SCORE", True, COLOR_TEXT_MUTED)
        surface.blit(surf_score_lbl, (LOGICAL_W - 230, 8))

        # Accuracy Readout
        acc_val = self.score_keeper.accuracy
        acc_str = f"ACCURACY  {acc_val:5.1f}%"
        surf_acc = self.font_label.render(acc_str, True, COLOR_RETRO_CYAN)
        surface.blit(surf_acc, (LOGICAL_W - 230, 72))

        # 2. Combo Counter (Left-Center)
        combo_val = self.score_keeper.current_combo
        if combo_val > 0:
            combo_str = f"{combo_val}x"
            # Combo number
            surf_combo_num = self.font_combo.render(combo_str, True, COLOR_NEON_GREEN)
            surface.blit(surf_combo_num, (48, 140))
            # Combo subtitle
            surf_combo_lbl = self.font_label.render("COMBO", True, COLOR_TEXT_PRIMARY)
            surface.blit(surf_combo_lbl, (52, 200))

        # 3. Floating Judgments
        for j in self.floating_judgments:
            j.draw(surface, self.font_judgment)

    def destroy(self) -> None:
        """Unsubscribes from the event bus."""
        event_bus.unsubscribe(GameEvent.HIT_RESULT, self._on_hit_result)
