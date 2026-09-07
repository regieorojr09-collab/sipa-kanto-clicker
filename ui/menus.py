"""Menu overlays and pause dialog for Sipa: Kanto Clicker."""

import pygame
from pygame.math import Vector2
from typing import Optional

from core.settings import (
    LOGICAL_W,
    LOGICAL_H,
    LOGICAL_CENTER_X,
    COLOR_SUNSHINE,
    COLOR_BRICK_RED,
    COLOR_RETRO_CYAN,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
)
from scenes.scene_manager import Scene, SceneManager


class PauseOverlay(Scene):
    """
    Modal pause menu pushed on top of the active scene stack.
    Suspends game loop updates while keeping the frozen gameplay frame visible beneath it.
    """

    def __init__(self, manager: SceneManager, on_restart_callback=None) -> None:
        super().__init__(manager)
        self.on_restart_callback = on_restart_callback
        self.mouse_pos: Vector2 = Vector2(0, 0)

        # Card layout
        card_w, card_h = 440, 360
        self.card_rect: pygame.Rect = pygame.Rect(
            LOGICAL_CENTER_X - (card_w // 2),
            (LOGICAL_H // 2) - (card_h // 2),
            card_w,
            card_h
        )

        # Interactive buttons
        btn_w, btn_h = 320, 52
        btn_x = LOGICAL_CENTER_X - (btn_w // 2)

        self.btn_resume: pygame.Rect = pygame.Rect(btn_x, self.card_rect.y + 110, btn_w, btn_h)
        self.btn_restart: pygame.Rect = pygame.Rect(btn_x, self.card_rect.y + 175, btn_w, btn_h)
        self.btn_quit: pygame.Rect = pygame.Rect(btn_x, self.card_rect.y + 240, btn_w, btn_h)

        self.hovered_btn: Optional[str] = None

        # Fonts
        self.font_title: Optional[pygame.font.Font] = None
        self.font_sub: Optional[pygame.font.Font] = None
        self.font_btn: Optional[pygame.font.Font] = None

    def _init_fonts(self) -> None:
        if self.font_title is None:
            self.font_title = pygame.font.Font(None, 52)
            self.font_sub = pygame.font.Font(None, 24)
            self.font_btn = pygame.font.Font(None, 30)

    def on_enter(self, **kwargs) -> None:
        self._init_fonts()

    def handle_event(self, event: pygame.event.Event, logical_mouse_pos: Vector2) -> None:
        self.mouse_pos = logical_mouse_pos

        # Track button hovers
        if self.btn_resume.collidepoint(self.mouse_pos.x, self.mouse_pos.y):
            self.hovered_btn = "resume"
        elif self.btn_restart.collidepoint(self.mouse_pos.x, self.mouse_pos.y):
            self.hovered_btn = "restart"
        elif self.btn_quit.collidepoint(self.mouse_pos.x, self.mouse_pos.y):
            self.hovered_btn = "quit"
        else:
            self.hovered_btn = None

        # Mouse click handling
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered_btn == "resume":
                self._resume()
            elif self.hovered_btn == "restart":
                self._restart()
            elif self.hovered_btn == "quit":
                self._quit_to_title()

        # Keyboard shortcuts
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_SPACE):
                self._resume()
            elif event.key == pygame.K_r:
                self._restart()
            elif event.key == pygame.K_q:
                self._quit_to_title()

    def _resume(self) -> None:
        self.manager.pop()

    def _restart(self) -> None:
        self.manager.pop()
        if self.on_restart_callback:
            self.on_restart_callback()

    def _quit_to_title(self) -> None:
        from scenes.title_scene import TitleScene
        self.manager.switch(TitleScene(self.manager))

    def update(self, dt: float) -> None:
        # Pause screen has no physics progression
        pass

    def draw(self, surface: pygame.Surface) -> None:
        self._init_fonts()
        assert self.font_title and self.font_sub and self.font_btn

        # 1. Semi-transparent backdrop overlay
        backdrop = pygame.Surface((LOGICAL_W, LOGICAL_H), pygame.SRCALPHA)
        backdrop.fill((12, 14, 20, 200))
        surface.blit(backdrop, (0, 0))

        # 2. Centered dialog card
        pygame.draw.rect(surface, (10, 12, 16), self.card_rect.move(4, 4), border_radius=14)
        pygame.draw.rect(surface, COLOR_CARD_BG, self.card_rect, border_radius=14)
        pygame.draw.rect(surface, COLOR_CARD_BORDER, self.card_rect, width=2, border_radius=14)

        # Header Title
        title_surf = self.font_title.render("HINTO MUNA (PAUSED)", True, COLOR_SUNSHINE)
        surface.blit(title_surf, title_surf.get_rect(center=(LOGICAL_CENTER_X, self.card_rect.y + 44)))

        # Subtitle
        sub_surf = self.font_sub.render("Pahinga muna sa laro, pre.", True, COLOR_TEXT_MUTED)
        surface.blit(sub_surf, sub_surf.get_rect(center=(LOGICAL_CENTER_X, self.card_rect.y + 78)))

        # 3. Buttons
        buttons = [
            ("resume", self.btn_resume, "ITULOY (RESUME) [ESC]", COLOR_SUNSHINE),
            ("restart", self.btn_restart, "UMULIT (RESTART) [R]", COLOR_RETRO_CYAN),
            ("quit", self.btn_quit, "LUMABAS (QUIT) [Q]", COLOR_BRICK_RED),
        ]

        for btn_id, rect, label, accent in buttons:
            is_hovered = (self.hovered_btn == btn_id)
            bg_color = (48, 54, 70) if is_hovered else (32, 36, 48)
            border_color = accent if is_hovered else COLOR_CARD_BORDER

            pygame.draw.rect(surface, bg_color, rect, border_radius=10)
            pygame.draw.rect(surface, border_color, rect, width=2, border_radius=10)

            text_color = COLOR_TEXT_PRIMARY if is_hovered else (210, 215, 225)
            surf_lbl = self.font_btn.render(label, True, text_color)
            surface.blit(surf_lbl, surf_lbl.get_rect(center=rect.center))
