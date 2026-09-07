"""Placeholder play scene for Phase 1 verification in Sipa: Kanto Clicker."""

import pygame
from pygame.math import Vector2
from typing import List, Optional, Tuple

from core.settings import (
    LOGICAL_W,
    LOGICAL_H,
    LOGICAL_CENTER_X,
    COLOR_BG_DARK,
    COLOR_ASPHALT,
    COLOR_CHALK,
    COLOR_SUNSHINE,
    COLOR_BRICK_RED,
    COLOR_RETRO_CYAN,
    COLOR_NEON_GREEN,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    GROUND_Y,
)
from scenes.scene_manager import Scene, SceneManager


class ClickRipple:
    """Animated expanding ring used to visually test hit detection and coordinate mapping."""

    def __init__(self, pos: Vector2) -> None:
        self.pos: Vector2 = Vector2(pos.x, pos.y)
        self.radius: float = 12.0
        self.max_radius: float = 64.0
        self.alpha: float = 255.0
        self.is_alive: bool = True

    def update(self, dt: float) -> None:
        self.radius += 140.0 * dt
        self.alpha -= 400.0 * dt
        if self.alpha <= 0 or self.radius >= self.max_radius:
            self.is_alive = False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.is_alive or self.alpha <= 0:
            return
        temp_surf = pygame.Surface((int(self.radius * 2) + 4, int(self.radius * 2) + 4), pygame.SRCALPHA)
        center = (int(self.radius) + 2, int(self.radius) + 2)
        color = (*COLOR_RETRO_CYAN, max(0, min(255, int(self.alpha))))
        pygame.draw.circle(temp_surf, color, center, int(self.radius), width=3)
        surface.blit(temp_surf, (self.pos.x - center[0], self.pos.y - center[1]))


class PlayScene(Scene):
    """
    Phase 1 Core Engine Test scene.
    Verifies input event dispatching, coordinate inverse-mapping, and scene transitions.
    """

    def __init__(self, manager: SceneManager) -> None:
        super().__init__(manager)
        self.mouse_pos: Vector2 = Vector2(0, 0)
        self.click_count: int = 0
        self.last_click_pos: Optional[Vector2] = None
        self.ripples: List[ClickRipple] = []

        # Return Button
        self.back_button_rect: pygame.Rect = pygame.Rect(32, 28, 220, 48)
        self.is_back_hovered: bool = False

        # Fonts
        self.font_header: Optional[pygame.font.Font] = None
        self.font_body: Optional[pygame.font.Font] = None

    def _init_fonts(self) -> None:
        if self.font_header is None:
            self.font_header = pygame.font.Font(None, 40)
            self.font_body = pygame.font.Font(None, 26)

    def on_enter(self, **kwargs) -> None:
        self._init_fonts()
        self.ripples.clear()

    def handle_event(self, event: pygame.event.Event, logical_mouse_pos: Vector2) -> None:
        self.mouse_pos = logical_mouse_pos
        self.is_back_hovered = self.back_button_rect.collidepoint(self.mouse_pos.x, self.mouse_pos.y)

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_back_hovered:
                from scenes.title_scene import TitleScene
                self.manager.switch(TitleScene(self.manager))
                return

            # Register click ripple at exact logical coordinate
            self.click_count += 1
            self.last_click_pos = Vector2(logical_mouse_pos.x, logical_mouse_pos.y)
            self.ripples.append(ClickRipple(self.last_click_pos))

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                from scenes.title_scene import TitleScene
                self.manager.switch(TitleScene(self.manager))
            elif event.key in (pygame.K_z, pygame.K_x):
                # Keyboard hit testing (Osu!-style keybinds)
                self.click_count += 1
                self.last_click_pos = Vector2(logical_mouse_pos.x, logical_mouse_pos.y)
                self.ripples.append(ClickRipple(self.last_click_pos))

    def update(self, dt: float) -> None:
        for ripple in self.ripples:
            ripple.update(dt)
        self.ripples = [r for r in self.ripples if r.is_alive]

    def draw(self, surface: pygame.Surface) -> None:
        self._init_fonts()

        # 1. Court background
        surface.fill(COLOR_BG_DARK)

        # Asphalt street pavement
        asphalt_h = LOGICAL_H - int(GROUND_Y) + 40
        pygame.draw.rect(
            surface,
            COLOR_ASPHALT,
            pygame.Rect(0, int(GROUND_Y) - 40, LOGICAL_W, asphalt_h)
        )

        # Chalk ground line (Ground Y)
        pygame.draw.line(surface, COLOR_CHALK, (0, int(GROUND_Y)), (LOGICAL_W, int(GROUND_Y)), 3)

        # Ground label
        surf_ground_lbl = self.font_body.render(f"Pavement Line: Ground Y = {int(GROUND_Y)}px", True, COLOR_TEXT_MUTED)
        surface.blit(surf_ground_lbl, (LOGICAL_W - 320, int(GROUND_Y) + 12))

        # 2. Header banner
        header_text = "ESKINITA COURT — PHASE 1: CORE ENGINE TEST"
        surf_header = self.font_header.render(header_text, True, COLOR_SUNSHINE)
        surface.blit(surf_header, surf_header.get_rect(center=(LOGICAL_CENTER_X, 52)))

        # 3. Active click ripples (coordinate verification)
        for ripple in self.ripples:
            ripple.draw(surface)

        # 4. Status Card
        card_rect = pygame.Rect(LOGICAL_CENTER_X - 250, 120, 500, 150)
        pygame.draw.rect(surface, COLOR_CARD_BG, card_rect, border_radius=12)
        pygame.draw.rect(surface, COLOR_CARD_BORDER, card_rect, width=2, border_radius=12)

        lines = [
            f"Clicks Registered: {self.click_count}",
            f"Current Logical Cursor: ({int(self.mouse_pos.x)}, {int(self.mouse_pos.y)})",
            f"Last Click Position: {f'({int(self.last_click_pos.x)}, {int(self.last_click_pos.y)})' if self.last_click_pos else 'None'}",
            "Left Click or Z/X to spawn test ripple rings • ESC to Return",
        ]

        for i, line in enumerate(lines):
            color = COLOR_NEON_GREEN if i == 0 else (COLOR_TEXT_PRIMARY if i < 3 else COLOR_RETRO_CYAN)
            surf_line = self.font_body.render(line, True, color)
            surface.blit(surf_line, (card_rect.x + 24, card_rect.y + 20 + (i * 28)))

        # 5. Back button
        btn_color = COLOR_BRICK_RED if not self.is_back_hovered else (240, 85, 80)
        pygame.draw.rect(surface, btn_color, self.back_button_rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_CARD_BORDER, self.back_button_rect, width=2, border_radius=8)
        surf_btn = self.font_body.render("← BUMALIK (TITLE)", True, COLOR_TEXT_PRIMARY)
        surface.blit(surf_btn, surf_btn.get_rect(center=self.back_button_rect.center))
