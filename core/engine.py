"""Display engine, canvas letterbox scaling, and coordinate mapping for Sipa: Kanto Clicker."""

import sys
import pygame
from pygame.math import Vector2
from typing import Tuple, Union

from core.settings import (
    LOGICAL_W,
    LOGICAL_H,
    LOGICAL_SIZE,
    TARGET_FPS,
    MAX_DELTA_TIME,
    WINDOW_TITLE,
    COLOR_BG_DARK,
)


class Engine:
    """
    Manages display creation, delta timing, letterboxed aspect-ratio scaling,
    and coordinate transformation from browser canvas coordinates to 1280x720 logical coordinates.
    """

    def __init__(self, initial_window_size: Tuple[int, int] = LOGICAL_SIZE) -> None:
        pygame.display.set_caption(WINDOW_TITLE)

        # Window/display surface (physical canvas size)
        self.window_size: Tuple[int, int] = initial_window_size
        self.window_surface: pygame.Surface = pygame.display.set_mode(
            self.window_size,
            pygame.RESIZABLE
        )

        # Logical rendering surface (fixed 1280x720 canvas where all game logic/rendering happens)
        self.logical_surface: pygame.Surface = pygame.Surface(LOGICAL_SIZE).convert()

        # Viewport rectangle within the window surface for letterbox/pillarbox rendering
        self.viewport_rect: pygame.Rect = pygame.Rect(0, 0, LOGICAL_W, LOGICAL_H)
        self.scale: float = 1.0

        # Clock & delta timing
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.delta_time: float = 0.0

        # Apply browser canvas pixelation if running in Emscripten/Pygbag
        self._configure_web_canvas()

        # Initial viewport calculation
        self.recalculate_viewport(*self.window_size)

    def _configure_web_canvas(self) -> None:
        """Applies web-specific styling flags when running inside Pygbag WebAssembly."""
        if sys.platform == "emscripten":
            try:
                import platform  # type: ignore
                # Hint browser to preserve clean rendering
                platform.window.canvas.style.imageRendering = "auto"
            except Exception:
                pass

    def recalculate_viewport(self, new_width: int, new_height: int) -> None:
        """
        Recalculates the centered 16:9 viewport rect and scale factor whenever the window is resized.
        """
        self.window_size = (max(1, new_width), max(1, new_height))
        target_aspect = LOGICAL_W / LOGICAL_H
        window_aspect = self.window_size[0] / self.window_size[1]

        if window_aspect > target_aspect:
            # Pillarbox: Window is wider than 16:9
            self.scale = self.window_size[1] / LOGICAL_H
            vp_w = int(LOGICAL_W * self.scale)
            vp_h = self.window_size[1]
            vp_x = (self.window_size[0] - vp_w) // 2
            vp_y = 0
        else:
            # Letterbox: Window is taller than 16:9
            self.scale = self.window_size[0] / LOGICAL_W
            vp_w = self.window_size[0]
            vp_h = int(LOGICAL_H * self.scale)
            vp_x = 0
            vp_y = (self.window_size[1] - vp_h) // 2

        self.viewport_rect = pygame.Rect(vp_x, vp_y, max(1, vp_w), max(1, vp_h))

    def canvas_to_logical_pos(self, mouse_pos: Union[Tuple[int, int], Vector2]) -> Vector2:
        """
        Converts physical window/canvas mouse coordinates into logical (1280x720) coordinates.
        Ensures precision click detection regardless of browser zoom or fullscreen scaling.
        """
        raw_x, raw_y = mouse_pos[0], mouse_pos[1]

        # Offset by viewport position and scale back to 1280x720
        logical_x = (raw_x - self.viewport_rect.x) / self.scale if self.scale > 0 else 0.0
        logical_y = (raw_y - self.viewport_rect.y) / self.scale if self.scale > 0 else 0.0

        return Vector2(logical_x, logical_y)

    def is_within_viewport(self, mouse_pos: Union[Tuple[int, int], Vector2]) -> bool:
        """Returns whether a physical mouse position lies inside the active 16:9 game area."""
        return self.viewport_rect.collidepoint(mouse_pos[0], mouse_pos[1])

    def tick(self) -> float:
        """
        Advances the frame clock and returns delta time in seconds, clamped to avoid physics hitching.
        """
        raw_ms = self.clock.tick(TARGET_FPS)
        # Convert ms to seconds and clamp to MAX_DELTA_TIME
        self.delta_time = min(raw_ms / 1000.0, MAX_DELTA_TIME)
        return self.delta_time

    def render_to_screen(self) -> None:
        """
        Scales the logical 1280x720 surface into the calculated viewport on the window surface,
        filling any letterbox/pillarbox margins with the background dark color.
        """
        # 1. Fill window margins (letterbox / pillarbox bands)
        self.window_surface.fill(COLOR_BG_DARK)

        # 2. Scale logical surface to current viewport
        if self.viewport_rect.size == LOGICAL_SIZE:
            # 1:1 match, direct blit without scaling overhead
            self.window_surface.blit(self.logical_surface, self.viewport_rect.topleft)
        else:
            scaled_surface = pygame.transform.smoothscale(
                self.logical_surface,
                self.viewport_rect.size
            )
            self.window_surface.blit(scaled_surface, self.viewport_rect.topleft)
