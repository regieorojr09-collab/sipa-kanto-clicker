"""Title and attract scene with interactive browser audio unlocking for Sipa: Kanto Clicker."""

import math
import pygame
from pygame.math import Vector2
from typing import Optional

from core.events import GameEvent, event_bus
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
    COLOR_RETRO_MAGENTA,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    GROUND_Y,
)
from scenes.scene_manager import Scene, SceneManager


class TitleScene(Scene):
    """
    Main title screen presenting the Filipino street arcade theme.
    Provides the primary user interaction required by Web browsers to unlock the AudioContext.
    """

    def __init__(self, manager: SceneManager) -> None:
        super().__init__(manager)
        self.time_elapsed: float = 0.0
        self.audio_unlocked: bool = False
        self.mouse_pos: Vector2 = Vector2(0, 0)
        self.is_button_hovered: bool = False

        # Interactive Start Button geometry
        button_w, button_h = 420, 76
        self.button_rect: pygame.Rect = pygame.Rect(
            LOGICAL_CENTER_X - (button_w // 2),
            460,
            button_w,
            button_h
        )

        # Lazy font cache
        self.font_title: Optional[pygame.font.Font] = None
        self.font_subtitle: Optional[pygame.font.Font] = None
        self.font_button: Optional[pygame.font.Font] = None
        self.font_info: Optional[pygame.font.Font] = None

    def _init_fonts(self) -> None:
        """Initializes default system fonts if not already cached."""
        if self.font_title is None:
            self.font_title = pygame.font.Font(None, 78)
            self.font_subtitle = pygame.font.Font(None, 34)
            self.font_button = pygame.font.Font(None, 38)
            self.font_info = pygame.font.Font(None, 24)

    def on_enter(self, **kwargs) -> None:
        self.time_elapsed = 0.0
        self._init_fonts()

    def handle_event(self, event: pygame.event.Event, logical_mouse_pos: Vector2) -> None:
        self.mouse_pos = logical_mouse_pos
        self.is_button_hovered = self.button_rect.collidepoint(self.mouse_pos.x, self.mouse_pos.y)

        # Trigger start on button click or Space/Enter
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_button_hovered:
                self._proceed_to_game()
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_z, pygame.K_x):
                self._proceed_to_game()

    def _proceed_to_game(self) -> None:
        """Publishes the browser audio unlock event and switches to the PlayScene."""
        if not self.audio_unlocked:
            self.audio_unlocked = True
            event_bus.publish(GameEvent.AUDIO_UNLOCK)

        # Delayed import to avoid circular dependency
        from scenes.play_scene import PlayScene
        self.manager.switch(PlayScene(self.manager))

    def update(self, dt: float) -> None:
        self.time_elapsed += dt

    def draw(self, surface: pygame.Surface) -> None:
        self._init_fonts()

        # 1. Background street court backdrop
        surface.fill(COLOR_BG_DARK)

        # Asphalt street floor
        street_rect = pygame.Rect(0, int(GROUND_Y) - 50, LOGICAL_W, LOGICAL_H - int(GROUND_Y) + 50)
        pygame.draw.rect(surface, COLOR_ASPHALT, street_rect)

        # Chalk ground baseline
        pygame.draw.line(surface, COLOR_CHALK, (0, int(GROUND_Y)), (LOGICAL_W, int(GROUND_Y)), 3)

        # Chalk court boundaries (perspective lines)
        pygame.draw.line(surface, COLOR_CHALK, (220, int(GROUND_Y)), (340, LOGICAL_H), 2)
        pygame.draw.line(surface, COLOR_CHALK, (LOGICAL_W - 220, int(GROUND_Y)), (LOGICAL_W - 340, LOGICAL_H), 2)
        pygame.draw.line(surface, COLOR_CHALK, (LOGICAL_CENTER_X, int(GROUND_Y)), (LOGICAL_CENTER_X, LOGICAL_H), 2)

        # 2. Main Title Banner with Retro Filipino Arcade Shadow
        title_text = "SIPA: KANTO CLICKER"
        sub_text = "ESKINITA RHYTHM & PRECISION ARCADE"

        # Pulsing title glow offset
        bobbing_y = int(math.sin(self.time_elapsed * 2.5) * 6.0)
        title_base_y = 170 + bobbing_y

        # Deep shadow
        surf_shadow = self.font_title.render(title_text, True, (0, 0, 0))
        surface.blit(surf_shadow, surf_shadow.get_rect(center=(LOGICAL_CENTER_X + 4, title_base_y + 4)))

        # Brick red outline layer
        surf_brick = self.font_title.render(title_text, True, COLOR_BRICK_RED)
        surface.blit(surf_brick, surf_brick.get_rect(center=(LOGICAL_CENTER_X + 2, title_base_y + 2)))

        # Bright Manila Sun golden face
        surf_face = self.font_title.render(title_text, True, COLOR_SUNSHINE)
        surface.blit(surf_face, surf_face.get_rect(center=(LOGICAL_CENTER_X, title_base_y)))

        # Subtitle
        surf_sub = self.font_subtitle.render(sub_text, True, COLOR_RETRO_CYAN)
        surface.blit(surf_sub, surf_sub.get_rect(center=(LOGICAL_CENTER_X, title_base_y + 64)))

        # Decorative taglines
        surf_tag = self.font_info.render("TIMING IS EVERYTHING • SWAK • PUWEDE • DAPLIS", True, COLOR_TEXT_MUTED)
        surface.blit(surf_tag, surf_tag.get_rect(center=(LOGICAL_CENTER_X, title_base_y + 105)))

        # 3. Interactive "Click to Start / Unlock Audio" Button
        btn_bg = COLOR_ACCENT_HOVER if self.is_button_hovered else COLOR_ACCENT
        btn_border = COLOR_SUNSHINE if self.is_button_hovered else COLOR_CARD_BORDER

        # Button shadow
        pygame.draw.rect(surface, (10, 12, 16), self.button_rect.move(4, 4), border_radius=12)
        # Button body
        pygame.draw.rect(surface, btn_bg, self.button_rect, border_radius=12)
        # Button highlight border
        pygame.draw.rect(surface, btn_border, self.button_rect, width=3, border_radius=12)

        # Button Text
        btn_label = "PINDOT DITO (CLICK TO START)"
        btn_text_color = (15, 18, 24)
        surf_btn_txt = self.font_button.render(btn_label, True, btn_text_color)
        surface.blit(surf_btn_txt, surf_btn_txt.get_rect(center=self.button_rect.center))

        # 4. Animated prompt underneath
        pulse_alpha = int(140 + 115 * math.sin(self.time_elapsed * 5.0))
        surf_prompt = self.font_info.render("Browser Audio Unlocks on First Click • Mouse or Z/X Keys", True, COLOR_TEXT_PRIMARY)
        surf_prompt.set_alpha(pulse_alpha)
        surface.blit(surf_prompt, surf_prompt.get_rect(center=(LOGICAL_CENTER_X, 565)))

        # 5. Coordinate & Viewport debug indicator (verifies canvas scaling in WebAssembly)
        coord_str = f"Canvas Cursor: ({int(self.mouse_pos.x)}, {int(self.mouse_pos.y)}) | Logical: 1280x720 | 60 FPS"
        surf_coords = self.font_info.render(coord_str, True, COLOR_TEXT_MUTED)
        surface.blit(surf_coords, (24, LOGICAL_H - 36))
