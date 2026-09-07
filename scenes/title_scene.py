"""Title and attract scene with interactive difficulty selector and audio unlocking."""

import math
import pygame
from pygame.math import Vector2
from typing import Dict, Optional, Tuple

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
    COLOR_NEON_GREEN,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_ACCENT,
    COLOR_ACCENT_HOVER,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    GROUND_Y,
)
from systems.difficulty import DifficultyLevel
from scenes.scene_manager import Scene, SceneManager


class TitleScene(Scene):
    """
    Main title screen presenting the Filipino street arcade theme.
    Allows selecting gameplay difficulty (Madali, Sakto, Mahirap, Pikon)
    and provides the primary user click required to unlock browser WebAudio.
    """

    def __init__(self, manager: SceneManager) -> None:
        super().__init__(manager)
        self.time_elapsed: float = 0.0
        self.audio_unlocked: bool = False
        self.mouse_pos: Vector2 = Vector2(0, 0)
        self.is_button_hovered: bool = False

        # Selected Difficulty
        self.selected_difficulty: DifficultyLevel = DifficultyLevel.SAKTO
        self.diff_buttons: Dict[DifficultyLevel, pygame.Rect] = {}
        self.hovered_diff: Optional[DifficultyLevel] = None

        # Build difficulty buttons geometry
        diffs = [DifficultyLevel.MADALI, DifficultyLevel.SAKTO, DifficultyLevel.MAHIRAP, DifficultyLevel.PIKON]
        tab_w, tab_h = 130, 42
        spacing = 14
        total_w = (len(diffs) * tab_w) + ((len(diffs) - 1) * spacing)
        start_x = LOGICAL_CENTER_X - (total_w // 2)
        diff_y = 390

        for i, d in enumerate(diffs):
            x = start_x + (i * (tab_w + spacing))
            self.diff_buttons[d] = pygame.Rect(x, diff_y, tab_w, tab_h)

        # Interactive Start Button geometry
        button_w, button_h = 420, 68
        self.button_rect: pygame.Rect = pygame.Rect(
            LOGICAL_CENTER_X - (button_w // 2),
            465,
            button_w,
            button_h
        )

        # Lazy font cache
        self.font_title: Optional[pygame.font.Font] = None
        self.font_subtitle: Optional[pygame.font.Font] = None
        self.font_button: Optional[pygame.font.Font] = None
        self.font_diff: Optional[pygame.font.Font] = None
        self.font_info: Optional[pygame.font.Font] = None

    def _init_fonts(self) -> None:
        if self.font_title is None:
            self.font_title = pygame.font.Font(None, 78)
            self.font_subtitle = pygame.font.Font(None, 34)
            self.font_button = pygame.font.Font(None, 36)
            self.font_diff = pygame.font.Font(None, 24)
            self.font_info = pygame.font.Font(None, 24)

    def on_enter(self, **kwargs) -> None:
        self.time_elapsed = 0.0
        self._init_fonts()

    def handle_event(self, event: pygame.event.Event, logical_mouse_pos: Vector2) -> None:
        self.mouse_pos = logical_mouse_pos
        self.is_button_hovered = self.button_rect.collidepoint(self.mouse_pos.x, self.mouse_pos.y)

        # Check hover on difficulty buttons
        self.hovered_diff = None
        for d, rect in self.diff_buttons.items():
            if rect.collidepoint(self.mouse_pos.x, self.mouse_pos.y):
                self.hovered_diff = d
                break

        # Handle mouse clicks
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered_diff is not None:
                self.selected_difficulty = self.hovered_diff
            elif self.is_button_hovered:
                self._proceed_to_game()

        # Keyboard shortcuts
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_z, pygame.K_x):
                self._proceed_to_game()
            elif event.key == pygame.K_1:
                self.selected_difficulty = DifficultyLevel.MADALI
            elif event.key == pygame.K_2:
                self.selected_difficulty = DifficultyLevel.SAKTO
            elif event.key == pygame.K_3:
                self.selected_difficulty = DifficultyLevel.MAHIRAP
            elif event.key == pygame.K_4:
                self.selected_difficulty = DifficultyLevel.PIKON

    def _proceed_to_game(self) -> None:
        """Publishes the browser audio unlock event and switches to the PlayScene with chosen difficulty."""
        if not self.audio_unlocked:
            self.audio_unlocked = True
            event_bus.publish(GameEvent.AUDIO_UNLOCK)

        from scenes.play_scene import PlayScene
        self.manager.switch_with_transition(
            PlayScene(self.manager, difficulty_level=self.selected_difficulty),
            duration=0.35
        )

    def update(self, dt: float) -> None:
        self.time_elapsed += dt

    def draw(self, surface: pygame.Surface) -> None:
        self._init_fonts()
        assert self.font_title and self.font_subtitle and self.font_button and self.font_diff and self.font_info

        # 1. Background street court backdrop
        surface.fill(COLOR_BG_DARK)

        # Asphalt street floor
        street_rect = pygame.Rect(0, int(GROUND_Y) - 50, LOGICAL_W, LOGICAL_H - int(GROUND_Y) + 50)
        pygame.draw.rect(surface, COLOR_ASPHALT, street_rect)

        # Chalk ground baseline & court perspective lines
        pygame.draw.line(surface, COLOR_CHALK, (0, int(GROUND_Y)), (LOGICAL_W, int(GROUND_Y)), 3)
        pygame.draw.line(surface, COLOR_CHALK, (220, int(GROUND_Y)), (340, LOGICAL_H), 2)
        pygame.draw.line(surface, COLOR_CHALK, (LOGICAL_W - 220, int(GROUND_Y)), (LOGICAL_W - 340, LOGICAL_H), 2)
        pygame.draw.line(surface, COLOR_CHALK, (LOGICAL_CENTER_X, int(GROUND_Y)), (LOGICAL_CENTER_X, LOGICAL_H), 2)

        # 2. Main Title Banner with Retro Filipino Arcade Shadow
        title_text = "SIPA: KANTO CLICKER"
        sub_text = "ESKINITA RHYTHM & PRECISION ARCADE"

        bobbing_y = int(math.sin(self.time_elapsed * 2.5) * 6.0)
        title_base_y = 160 + bobbing_y

        surf_shadow = self.font_title.render(title_text, True, (0, 0, 0))
        surface.blit(surf_shadow, surf_shadow.get_rect(center=(LOGICAL_CENTER_X + 4, title_base_y + 4)))

        surf_brick = self.font_title.render(title_text, True, COLOR_BRICK_RED)
        surface.blit(surf_brick, surf_brick.get_rect(center=(LOGICAL_CENTER_X + 2, title_base_y + 2)))

        surf_face = self.font_title.render(title_text, True, COLOR_SUNSHINE)
        surface.blit(surf_face, surf_face.get_rect(center=(LOGICAL_CENTER_X, title_base_y)))

        surf_sub = self.font_subtitle.render(sub_text, True, COLOR_RETRO_CYAN)
        surface.blit(surf_sub, surf_sub.get_rect(center=(LOGICAL_CENTER_X, title_base_y + 62)))

        surf_tag = self.font_info.render("TIMING IS EVERYTHING • SWAK • PUWEDE • DAPLIS", True, COLOR_TEXT_MUTED)
        surface.blit(surf_tag, surf_tag.get_rect(center=(LOGICAL_CENTER_X, title_base_y + 100)))

        # 3. Difficulty Selector Tabs
        lbl_diff_title = self.font_info.render("PUMILI NG HIRAP (SELECT DIFFICULTY):", True, COLOR_TEXT_MUTED)
        surface.blit(lbl_diff_title, lbl_diff_title.get_rect(center=(LOGICAL_CENTER_X, 368)))

        for d, rect in self.diff_buttons.items():
            is_selected = (self.selected_difficulty == d)
            is_hovered = (self.hovered_diff == d)

            if is_selected:
                tab_bg = COLOR_CARD_BG
                border_color = COLOR_SUNSHINE if d != DifficultyLevel.PIKON else COLOR_BRICK_RED
                txt_color = COLOR_SUNSHINE if d != DifficultyLevel.PIKON else (255, 75, 75)
                border_w = 3
            else:
                tab_bg = (36, 42, 56) if is_hovered else (24, 28, 38)
                border_color = (70, 78, 98) if is_hovered else COLOR_CARD_BORDER
                txt_color = (200, 205, 215)
                border_w = 1

            pygame.draw.rect(surface, tab_bg, rect, border_radius=8)
            pygame.draw.rect(surface, border_color, rect, width=border_w, border_radius=8)

            label = f"{d.display_name} [{d.score_mult:.1f}x]"
            surf_tab = self.font_diff.render(label, True, txt_color)
            surface.blit(surf_tab, surf_tab.get_rect(center=rect.center))

        # 4. Interactive "Click to Start / Unlock Audio" Button
        btn_bg = COLOR_ACCENT_HOVER if self.is_button_hovered else COLOR_ACCENT
        btn_border = COLOR_SUNSHINE if self.is_button_hovered else COLOR_CARD_BORDER

        pygame.draw.rect(surface, (10, 12, 16), self.button_rect.move(4, 4), border_radius=12)
        pygame.draw.rect(surface, btn_bg, self.button_rect, border_radius=12)
        pygame.draw.rect(surface, btn_border, self.button_rect, width=3, border_radius=12)

        btn_label = f"SIMULAN ({self.selected_difficulty.display_name.upper()})"
        surf_btn_txt = self.font_button.render(btn_label, True, (15, 18, 24))
        surface.blit(surf_btn_txt, surf_btn_txt.get_rect(center=self.button_rect.center))

        # 5. Animated prompt
        pulse_alpha = int(140 + 115 * math.sin(self.time_elapsed * 5.0))
        surf_prompt = self.font_info.render("Browser Audio Unlocks on First Click • Left Click or Z/X", True, COLOR_TEXT_PRIMARY)
        surf_prompt.set_alpha(pulse_alpha)
        surface.blit(surf_prompt, surf_prompt.get_rect(center=(LOGICAL_CENTER_X, 555)))

        # 6. Coordinate debug indicator
        coord_str = f"Canvas: ({int(self.mouse_pos.x)}, {int(self.mouse_pos.y)}) | Logical: 1280x720 | 60 FPS"
        surf_coords = self.font_info.render(coord_str, True, COLOR_TEXT_MUTED)
        surface.blit(surf_coords, (24, LOGICAL_H - 32))
