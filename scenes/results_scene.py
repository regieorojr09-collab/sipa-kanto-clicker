"""Round results and performance grading scene for Sipa: Kanto Clicker."""

import math
import random
import pygame
from pygame.math import Vector2
from typing import Dict, Optional, Tuple

from core.settings import (
    LOGICAL_W,
    LOGICAL_H,
    LOGICAL_CENTER_X,
    COLOR_BG_DARK,
    COLOR_SUNSHINE,
    COLOR_BRICK_RED,
    COLOR_RETRO_CYAN,
    COLOR_NEON_GREEN,
    COLOR_TASSEL_GOLD,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
)
from scenes.scene_manager import Scene, SceneManager
from ui.fx import ParticleEmitter


def compute_street_rank(accuracy: float) -> Tuple[str, str, Tuple[int, int, int]]:
    """
    Computes Filipino street rank grade and title based on rhythm accuracy.
    - S (>= 95%): "Hari ng Kanto" (Gold)
    - A (>= 85%): "Beterano" (Cyan)
    - B (>= 75%): "Marunong" (Green)
    - C (>= 60%): "Bagito" (Orange)
    - F (< 60%):  "Kulelat" (Brick Red)
    """
    if accuracy >= 95.0:
        return ("S", "HARI NG KANTO", COLOR_SUNSHINE)
    elif accuracy >= 85.0:
        return ("A", "BETERANO", COLOR_RETRO_CYAN)
    elif accuracy >= 75.0:
        return ("B", "MARUNONG", COLOR_NEON_GREEN)
    elif accuracy >= 60.0:
        return ("C", "BAGITO", COLOR_TASSEL_GOLD)
    else:
        return ("F", "KULELAT", COLOR_BRICK_RED)


class ResultsScene(Scene):
    """
    Displays the final score breakdown, max combo, accuracy rating, and rank badge.
    Features rolling score animation, Filipino street-art borders, and celebratory sparkles.
    """

    def __init__(self, manager: SceneManager, stats: Optional[Dict[str, object]] = None, difficulty_level=None) -> None:
        super().__init__(manager)
        self.stats: Dict[str, object] = stats or {
            "score": 0,
            "max_combo": 0,
            "accuracy": 100.0,
            "counts": {"Swak!": 0, "Puwede": 0, "Daplis": 0, "Bagsak!": 0},
        }
        self.difficulty_level = difficulty_level
        self.mouse_pos: Vector2 = Vector2(0, 0)
        self.hovered_button: Optional[str] = None

        # Rolling Score Animation State
        self.target_score: int = int(self.stats.get("score", 0))
        self.displayed_score: int = 0
        self.roll_timer: float = 0.0
        self.roll_duration: float = 1.2
        self.is_rolling: bool = True

        # Celebratory Sparkle Emitter for S/A ranks
        self.sparkle_emitter: ParticleEmitter = ParticleEmitter(max_particles=80)
        self.sparkle_spawn_timer: float = 0.0

        # Interactive Buttons
        btn_w, btn_h = 240, 52
        self.btn_play_again: pygame.Rect = pygame.Rect(
            LOGICAL_CENTER_X - btn_w - 20,
            580,
            btn_w,
            btn_h
        )
        self.btn_title: pygame.Rect = pygame.Rect(
            LOGICAL_CENTER_X + 20,
            580,
            btn_w,
            btn_h
        )

        # Fonts
        self.font_header: Optional[pygame.font.Font] = None
        self.font_grade: Optional[pygame.font.Font] = None
        self.font_title_lbl: Optional[pygame.font.Font] = None
        self.font_stat_val: Optional[pygame.font.Font] = None
        self.font_stat_lbl: Optional[pygame.font.Font] = None
        self.font_btn: Optional[pygame.font.Font] = None

    def _init_fonts(self) -> None:
        if self.font_header is None:
            self.font_header = pygame.font.Font(None, 46)
            self.font_grade = pygame.font.Font(None, 110)
            self.font_title_lbl = pygame.font.Font(None, 34)
            self.font_stat_val = pygame.font.Font(None, 40)
            self.font_stat_lbl = pygame.font.Font(None, 24)
            self.font_btn = pygame.font.Font(None, 30)

    def on_enter(self, **kwargs) -> None:
        self._init_fonts()
        if "stats" in kwargs:
            self.stats = kwargs["stats"]
            self.target_score = int(self.stats.get("score", 0))
            self.displayed_score = 0
            self.roll_timer = 0.0
            self.is_rolling = True
        if "difficulty_level" in kwargs:
            self.difficulty_level = kwargs["difficulty_level"]
        self.sparkle_emitter.clear()

    def handle_event(self, event: pygame.event.Event, logical_mouse_pos: Vector2) -> None:
        self.mouse_pos = logical_mouse_pos

        # Check button hovers
        if self.btn_play_again.collidepoint(self.mouse_pos.x, self.mouse_pos.y):
            self.hovered_button = "play_again"
        elif self.btn_title.collidepoint(self.mouse_pos.x, self.mouse_pos.y):
            self.hovered_button = "title"
        else:
            self.hovered_button = None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_rolling:
                self.displayed_score = self.target_score
                self.is_rolling = False
            if self.hovered_button == "play_again":
                self._play_again()
            elif self.hovered_button == "title":
                self._go_to_title()

        elif event.type == pygame.KEYDOWN:
            if self.is_rolling:
                self.displayed_score = self.target_score
                self.is_rolling = False
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._play_again()
            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                self._go_to_title()

    def _play_again(self) -> None:
        from scenes.play_scene import PlayScene
        self.manager.switch_with_transition(
            PlayScene(self.manager, difficulty_level=self.difficulty_level),
            duration=0.35
        )

    def _go_to_title(self) -> None:
        from scenes.title_scene import TitleScene
        self.manager.switch_with_transition(TitleScene(self.manager), duration=0.35)

    def update(self, dt: float) -> None:
        # 1. Rolling score animation with cubic ease-out
        if self.is_rolling:
            self.roll_timer += dt
            progress = min(1.0, max(0.0, self.roll_timer / self.roll_duration))
            eased = 1.0 - math.pow(1.0 - progress, 3.0)
            self.displayed_score = int(self.target_score * eased)
            if progress >= 1.0:
                self.displayed_score = self.target_score
                self.is_rolling = False

        # 2. Celebratory sparkles on S and A ranks
        acc = float(self.stats.get("accuracy", 100.0))
        grade_letter, _, _ = compute_street_rank(acc)
        if grade_letter in ("S", "A"):
            self.sparkle_spawn_timer += dt
            if self.sparkle_spawn_timer >= 0.08:
                self.sparkle_spawn_timer = 0.0
                card_w = 820
                card_x = LOGICAL_CENTER_X - (card_w // 2)
                grade_box_rect = pygame.Rect(card_x + 40, 145, 240, 360)

                sx = random.uniform(grade_box_rect.left + 15, grade_box_rect.right - 15)
                sy = random.uniform(grade_box_rect.top + 15, grade_box_rect.bottom - 15)
                colors = [COLOR_SUNSHINE, COLOR_TASSEL_GOLD, COLOR_RETRO_CYAN]
                self.sparkle_emitter.burst(
                    Vector2(sx, sy),
                    count=2,
                    colors=colors,
                    speed_min=20.0,
                    speed_max=75.0,
                    lifetime=0.55
                )

        self.sparkle_emitter.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self._init_fonts()
        assert self.font_header and self.font_grade and self.font_title_lbl and self.font_stat_val and self.font_stat_lbl and self.font_btn

        surface.fill(COLOR_BG_DARK)

        # 1. Header Banner
        header_text = "TAPOS ANG LARO! (ROUND COMPLETE)"
        surf_header = self.font_header.render(header_text, True, COLOR_SUNSHINE)
        surface.blit(surf_header, surf_header.get_rect(center=(LOGICAL_CENTER_X, 56)))

        # 2. Results Container Card
        card_w, card_h = 820, 440
        card_rect = pygame.Rect(LOGICAL_CENTER_X - (card_w // 2), 105, card_w, card_h)
        pygame.draw.rect(surface, (12, 14, 20), card_rect.move(4, 4), border_radius=16)
        pygame.draw.rect(surface, COLOR_CARD_BG, card_rect, border_radius=16)
        pygame.draw.rect(surface, COLOR_CARD_BORDER, card_rect, width=2, border_radius=16)

        # 3. Grade & Title Badge (Left column of card)
        acc = float(self.stats.get("accuracy", 100.0))
        grade_letter, street_title, grade_color = compute_street_rank(acc)

        grade_box_rect = pygame.Rect(card_rect.x + 40, card_rect.y + 40, 240, 360)
        pygame.draw.rect(surface, (20, 24, 34), grade_box_rect, border_radius=12)

        # Filipino Street-Art Decorative Borders
        # Outer thick border
        pygame.draw.rect(surface, grade_color, grade_box_rect, width=3, border_radius=12)
        # Inner fine border line
        inner_rect = grade_box_rect.inflate(-12, -12)
        pygame.draw.rect(surface, (45, 52, 70), inner_rect, width=1, border_radius=8)

        # Decorative Jeepney Diamond Studs on corners
        stud_color = COLOR_SUNSHINE if grade_letter in ("S", "A") else grade_color
        stud_corners = [
            (grade_box_rect.left + 8, grade_box_rect.top + 8),
            (grade_box_rect.right - 8, grade_box_rect.top + 8),
            (grade_box_rect.left + 8, grade_box_rect.bottom - 8),
            (grade_box_rect.right - 8, grade_box_rect.bottom - 8),
        ]
        for cx, cy in stud_corners:
            diamond_pts = [(cx, cy - 6), (cx + 6, cy), (cx, cy + 6), (cx - 6, cy)]
            pygame.draw.polygon(surface, stud_color, diamond_pts)

        # Top edge festive chevron accents (Banderitas style)
        for bx in range(grade_box_rect.left + 30, grade_box_rect.right - 30, 26):
            tri_pts = [(bx, grade_box_rect.top), (bx + 13, grade_box_rect.top + 10), (bx + 26, grade_box_rect.top)]
            pygame.draw.polygon(surface, grade_color, tri_pts)

        # Grade Letter
        surf_grade = self.font_grade.render(grade_letter, True, grade_color)
        surface.blit(surf_grade, surf_grade.get_rect(center=(grade_box_rect.centerx, grade_box_rect.y + 110)))

        # Street Rank Title
        surf_title = self.font_title_lbl.render(street_title, True, COLOR_TEXT_PRIMARY)
        surface.blit(surf_title, surf_title.get_rect(center=(grade_box_rect.centerx, grade_box_rect.y + 220)))

        # Accuracy Subtitle
        surf_acc_str = self.font_stat_lbl.render(f"Accuracy: {acc:.1f}%", True, COLOR_RETRO_CYAN)
        surface.blit(surf_acc_str, surf_acc_str.get_rect(center=(grade_box_rect.centerx, grade_box_rect.y + 270)))

        # Draw particle sparkles on top of badge
        self.sparkle_emitter.draw(surface)

        # 4. Numeric Performance Stats (Right column of card)
        stats_x = card_rect.x + 320
        stats_y = card_rect.y + 40

        max_combo = int(self.stats.get("max_combo", 0))
        counts = self.stats.get("counts", {})

        stat_rows = [
            ("TOTAL SCORE", f"{self.displayed_score:,}", COLOR_SUNSHINE),
            ("MAX COMBO", f"{max_combo}x", COLOR_NEON_GREEN),
            ("SWAK! (300 pts)", str(counts.get("Swak!", 0)), COLOR_SUNSHINE),
            ("PUWEDE (100 pts)", str(counts.get("Puwede", 0)), COLOR_RETRO_CYAN),
            ("DAPLIS (50 pts)", str(counts.get("Daplis", 0)), COLOR_TASSEL_GOLD),
            ("BAGSAK! (Miss)", str(counts.get("Bagsak!", 0)), COLOR_BRICK_RED),
        ]

        for i, (label, val_str, color) in enumerate(stat_rows):
            row_y = stats_y + (i * 56)
            # Label
            surf_lbl = self.font_stat_lbl.render(label, True, COLOR_TEXT_MUTED)
            surface.blit(surf_lbl, (stats_x, row_y))
            # Value
            surf_val = self.font_stat_val.render(val_str, True, color)
            surface.blit(surf_val, (stats_x + 280, row_y - 4))
            # Subtle divider line
            if i < len(stat_rows) - 1:
                pygame.draw.line(surface, (40, 46, 62), (stats_x, row_y + 44), (stats_x + 440, row_y + 44), 1)

        # 5. Interactive Action Buttons
        # Play Again Button
        is_pa_hover = (self.hovered_button == "play_again")
        pa_bg = COLOR_SUNSHINE if is_pa_hover else (45, 52, 68)
        pa_txt_col = (20, 24, 30) if is_pa_hover else COLOR_TEXT_PRIMARY
        pygame.draw.rect(surface, pa_bg, self.btn_play_again, border_radius=10)
        pygame.draw.rect(surface, COLOR_SUNSHINE, self.btn_play_again, width=2, border_radius=10)
        surf_pa = self.font_btn.render("ULIT (PLAY AGAIN) [SPACE]", True, pa_txt_col)
        surface.blit(surf_pa, surf_pa.get_rect(center=self.btn_play_again.center))

        # Title Screen Button
        is_t_hover = (self.hovered_button == "title")
        t_bg = COLOR_BRICK_RED if is_t_hover else (45, 52, 68)
        t_txt_col = COLOR_TEXT_PRIMARY
        pygame.draw.rect(surface, t_bg, self.btn_title, border_radius=10)
        pygame.draw.rect(surface, COLOR_CARD_BORDER, self.btn_title, width=2, border_radius=10)
        surf_t = self.font_btn.render("MENU (TITLE) [ESC]", True, t_txt_col)
        surface.blit(surf_t, surf_t.get_rect(center=self.btn_title.center))

