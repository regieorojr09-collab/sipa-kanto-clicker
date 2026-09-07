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
    Renders live gameplay status: Score, Combo count, Accuracy %, Pikon Meter gauge,
    and floating judgments.
    """

    def __init__(self, score_keeper: ScoreKeeper, difficulty_controller=None) -> None:
        self.score_keeper: ScoreKeeper = score_keeper
        self.difficulty_controller = difficulty_controller
        self.floating_judgments: List[FloatingJudgment] = []
        self.time_elapsed: float = 0.0

        # Cached fonts
        self.font_score: Optional[pygame.font.Font] = None
        self.font_combo: Optional[pygame.font.Font] = None
        self.font_judgment: Optional[pygame.font.Font] = None
        self.font_label: Optional[pygame.font.Font] = None
        self.font_pikon: Optional[pygame.font.Font] = None

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
            self.font_pikon = pygame.font.Font(None, 20)

    def _on_hit_result(
        self,
        judgment: str,
        position: Tuple[float, float] = (640.0, 360.0),
        **kwargs
    ) -> None:
        """Spawns floating judgment feedback at the hit coordinate."""
        color = self._judgment_colors.get(judgment, COLOR_TEXT_PRIMARY)
        popup_pos = (position[0], max(100.0, position[1] - 40.0))
        self.floating_judgments.append(FloatingJudgment(judgment, popup_pos, color))

    def update(self, dt: float) -> None:
        """Advances floating judgment animations and timer."""
        self.time_elapsed += dt
        for j in self.floating_judgments:
            j.update(dt)
        self.floating_judgments = [j for j in self.floating_judgments if j.is_alive]

    def draw(self, surface: pygame.Surface) -> None:
        """Renders HUD panels, typography, Pikon Meter, and floating popups."""
        self._init_fonts()
        assert self.font_score and self.font_combo and self.font_label and self.font_judgment and self.font_pikon

        # 1. Top-Right Score Panel
        score_val = self.score_keeper.score
        score_str = f"{score_val:07d}"

        surf_shadow = self.font_score.render(score_str, True, (0, 0, 0))
        surface.blit(surf_shadow, (LOGICAL_W - 228, 26))

        surf_score = self.font_score.render(score_str, True, COLOR_SUNSHINE)
        surface.blit(surf_score, (LOGICAL_W - 230, 24))

        surf_score_lbl = self.font_label.render("SCORE", True, COLOR_TEXT_MUTED)
        surface.blit(surf_score_lbl, (LOGICAL_W - 230, 8))

        acc_val = self.score_keeper.accuracy
        acc_str = f"ACCURACY  {acc_val:5.1f}%"
        surf_acc = self.font_label.render(acc_str, True, COLOR_RETRO_CYAN)
        surface.blit(surf_acc, (LOGICAL_W - 230, 72))

        # 2. Top-Center Pikon Meter & Difficulty Display
        if self.difficulty_controller:
            pikon = self.difficulty_controller.pikon_meter
            level_name = self.difficulty_controller.level.display_name
            mult_str = f"{self.difficulty_controller.level.score_mult:.1f}x"

            bar_w, bar_h = 220, 16
            bar_x = (LOGICAL_W // 2) - (bar_w // 2)
            bar_y = 20

            # Difficulty Tag
            diff_str = f"{level_name.upper()} [{mult_str}]"
            surf_diff = self.font_pikon.render(diff_str, True, COLOR_TEXT_MUTED)
            surface.blit(surf_diff, surf_diff.get_rect(center=(LOGICAL_W // 2, bar_y - 10)))

            # Meter Frame
            bg_rect = pygame.Rect(bar_x, bar_y, bar_w, bar_h)
            pygame.draw.rect(surface, (20, 24, 34), bg_rect, border_radius=4)

            # Fill bar
            fill_w = max(0, int((bar_w - 4) * (pikon / 100.0)))
            if fill_w > 0:
                if pikon >= 80.0:
                    bar_color = (255, 45, 65)  # Crimson Rage
                elif pikon >= 50.0:
                    bar_color = (255, 180, 20)  # Orange
                elif pikon >= 30.0:
                    bar_color = COLOR_SUNSHINE
                else:
                    bar_color = (50, 220, 120)  # Calm Green

                fill_rect = pygame.Rect(bar_x + 2, bar_y + 2, fill_w, bar_h - 4)
                pygame.draw.rect(surface, bar_color, fill_rect, border_radius=3)

            # Pulsing border at Pikon Rage (>= 80%)
            if pikon >= 80.0:
                import math
                pulse = int(180 + 75 * math.sin(self.time_elapsed * 8.0))
                border_col = (pulse, 35, 55)
            else:
                border_col = COLOR_CARD_BORDER

            pygame.draw.rect(surface, border_col, bg_rect, width=2, border_radius=4)

            # Meter Label
            pikon_lbl = f"PIKON: {int(pikon)}%"
            surf_pikon_txt = self.font_pikon.render(pikon_lbl, True, COLOR_TEXT_PRIMARY)
            surface.blit(surf_pikon_txt, surf_pikon_txt.get_rect(center=(LOGICAL_W // 2, bar_y + 24)))

            # Active Modifiers Indicators
            mods = []
            if self.difficulty_controller.wind_force != 0.0:
                mods.append("HANGIN")
            if self.difficulty_controller.approach_rate_mult < 1.0:
                mods.append("BILIS")
            if self.difficulty_controller.double_target:
                mods.append("DALAWA")

            if mods:
                mods_str = "MODS: " + " • ".join(mods)
                surf_mods = self.font_pikon.render(mods_str, True, COLOR_RETRO_CYAN)
                surface.blit(surf_mods, surf_mods.get_rect(center=(LOGICAL_W // 2, bar_y + 40)))

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
