"""Core gameplay scene for Sipa: Kanto Clicker integrating physics, rhythm targets, and HUD."""

import random
import pygame
from pygame.math import Vector2
from typing import List, Optional

from core.events import GameEvent, event_bus
from core.settings import (
    LOGICAL_W,
    LOGICAL_H,
    LOGICAL_CENTER_X,
    GROUND_Y,
    KICK_TARGET_Y,
    BASE_KICK_VELOCITY,
    COLOR_BG_DARK,
    COLOR_ASPHALT,
    COLOR_CHALK,
    COLOR_SUNSHINE,
    COLOR_BRICK_RED,
    COLOR_CARD_BORDER,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_MUTED,
    COLOR_RETRO_CYAN,
    COLOR_TASSEL_MAGENTA,
)
from entities.sipa import Sipa
from systems.hit_system import HitSystem
from systems.scoring import ScoreKeeper
from ui.hud import HUD
from scenes.scene_manager import Scene, SceneManager


class HitRippleVFX:
    """Visual feedback ring produced on a successful kick or target hit."""

    def __init__(self, pos: Vector2, color: tuple[int, int, int] = COLOR_RETRO_CYAN) -> None:
        self.pos: Vector2 = Vector2(pos.x, pos.y)
        self.color: tuple[int, int, int] = color
        self.radius: float = 24.0
        self.max_radius: float = 72.0
        self.alpha: float = 255.0
        self.is_alive: bool = True

    def update(self, dt: float) -> None:
        self.radius += 160.0 * dt
        self.alpha -= 450.0 * dt
        if self.alpha <= 0.0 or self.radius >= self.max_radius:
            self.is_alive = False

    def draw(self, surface: pygame.Surface) -> None:
        if not self.is_alive or self.alpha <= 0.0:
            return
        size = int(self.radius * 2) + 4
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        center = (size // 2, size // 2)
        pygame.draw.circle(
            surf,
            (*self.color, max(0, min(255, int(self.alpha)))),
            center,
            int(self.radius),
            width=3
        )
        surface.blit(surf, (self.pos.x - center[0], self.pos.y - center[1]))


class PlayScene(Scene):
    """
    Main arcade/rhythm play scene.
    Coordinates the Sipa kinematic projectile, HitSystem approach rings,
    player click timing, ScoreKeeper, and HUD overlay.
    """

    def __init__(self, manager: SceneManager) -> None:
        super().__init__(manager)
        self.mouse_pos: Vector2 = Vector2(LOGICAL_CENTER_X, GROUND_Y)

        # Core Entities & Systems
        self.sipa: Sipa = Sipa(x=380.0, y=GROUND_Y)
        self.hit_system: HitSystem = HitSystem()
        self.score_keeper: ScoreKeeper = ScoreKeeper(difficulty_mult=1.0)
        self.hud: HUD = HUD(self.score_keeper)

        # Round & Arc State
        self.click_count: int = 0
        self.has_spawned_target_for_arc: bool = False
        self.serve_timer: float = 0.5  # Initial serve delay
        self.is_serving: bool = False
        self.ripples: List[HitRippleVFX] = []

        # Return Button
        self.back_button_rect: pygame.Rect = pygame.Rect(32, 24, 180, 42)
        self.is_back_hovered: bool = False

        # Fonts
        self.font_court: Optional[pygame.font.Font] = None
        self.font_btn: Optional[pygame.font.Font] = None

    def _init_fonts(self) -> None:
        if self.font_court is None:
            self.font_court = pygame.font.Font(None, 24)
            self.font_btn = pygame.font.Font(None, 26)

    def on_enter(self, **kwargs) -> None:
        self._init_fonts()
        self.serve_timer = 0.5
        self.is_serving = False
        self.has_spawned_target_for_arc = False
        self.sipa.reset(x=380.0, y=GROUND_Y)

    def on_exit(self) -> None:
        self.score_keeper.destroy()
        self.hud.destroy()
        self.hit_system.clear()

    def serve_sipa(self) -> None:
        """Launches a new sipa from either side of the court towards center."""
        # Alternate serve origin: either player side (left) or rival side (right)
        serve_from_left = random.random() > 0.3
        start_x = 340.0 if serve_from_left else (LOGICAL_W - 340.0)
        target_dir = 1.0 if serve_from_left else -1.0

        self.sipa.reset(x=start_x, y=GROUND_Y - 10.0)

        # Upward high arc
        vx = target_dir * random.uniform(220.0, 320.0)
        vy = -random.uniform(780.0, 880.0)
        self.sipa.launch(Vector2(vx, vy), spin=random.uniform(2.0, 3.5))

        self.has_spawned_target_for_arc = False
        self.is_serving = False

    def handle_event(self, event: pygame.event.Event, logical_mouse_pos: Vector2) -> None:
        self.mouse_pos = logical_mouse_pos
        self.is_back_hovered = self.back_button_rect.collidepoint(self.mouse_pos.x, self.mouse_pos.y)

        # 1. Back Button Click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_back_hovered:
                from scenes.title_scene import TitleScene
                self.manager.switch(TitleScene(self.manager))
                return

        # 2. ESC Key -> Return to Title
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            from scenes.title_scene import TitleScene
            self.manager.switch(TitleScene(self.manager))
            return

        # 3. Hit Input: Mouse Left-Click or Z/X Keys
        is_hit_trigger = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            is_hit_trigger = True
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_z, pygame.K_x):
            is_hit_trigger = True

        if is_hit_trigger:
            self._process_hit_attempt()

    def _process_hit_attempt(self) -> None:
        """Evaluates player click against active rhythm targets and executes kicks."""
        self.click_count += 1
        current_time_ms = float(pygame.time.get_ticks())
        hit_result = self.hit_system.check_hit(self.mouse_pos, current_time_ms)

        if hit_result is not None:
            judgment = str(hit_result["judgment"])
            was_miss = bool(hit_result["was_miss"])
            pos = hit_result["position"]
            target_pos = Vector2(pos[0], pos[1]) if isinstance(pos, (tuple, list)) else Vector2(pos)

            if not was_miss:
                # Spawn hit ripple VFX
                ripple_color = COLOR_SUNSHINE if judgment == "Swak!" else COLOR_RETRO_CYAN
                self.ripples.append(HitRippleVFX(target_pos, ripple_color))

                # Relaunch sipa with exit velocity scaled by accuracy tier
                multiplier = 1.0
                if judgment == "Swak!":
                    multiplier = 1.0
                elif judgment == "Puwede":
                    multiplier = 0.85
                elif judgment == "Daplis":
                    multiplier = 0.68

                # Determine trajectory: arc towards opposite side of court
                center_bias = 1.0 if self.sipa.pos.x < LOGICAL_CENTER_X else -1.0
                vx = center_bias * random.uniform(220.0, 340.0) + random.uniform(-25.0, 25.0)
                vy = -BASE_KICK_VELOCITY * multiplier

                self.sipa.launch(Vector2(vx, vy), spin=random.uniform(2.5, 4.0))
                # Ready next target for the new arc
                self.has_spawned_target_for_arc = False

            else:
                # Missed hit timing: sipa drops and breaks combo
                self.ripples.append(HitRippleVFX(target_pos, COLOR_BRICK_RED))
        else:
            # Clicked empty space: subtle tactile cursor ripple
            self.ripples.append(HitRippleVFX(self.mouse_pos, (90, 100, 120)))

    def update(self, dt: float) -> None:
        current_time_ms = float(pygame.time.get_ticks())

        # 1. Update Sipa Kinematics
        self.sipa.update(dt)

        # 2. Check trajectory apex to predict landing and spawn approach ring
        if self.sipa.is_airborne and self.sipa.vel.y >= 0.0 and not self.has_spawned_target_for_arc:
            self.has_spawned_target_for_arc = True
            pred_x, pred_y, arrival_ms = self.sipa.predict_landing(KICK_TARGET_Y)

            if arrival_ms > 120.0:
                t_arrive = current_time_ms + arrival_ms
                self.hit_system.spawn_target(
                    cx=pred_x,
                    cy=pred_y,
                    t_arrive=t_arrive,
                    t_duration=arrival_ms
                )

        # 3. Update Hit System (processes expired/missed targets)
        self.hit_system.update(current_time_ms)

        # 4. Handle Ground Landing & Serve Resets
        if self.sipa.is_grounded and not self.is_serving:
            self.is_serving = True
            self.serve_timer = 0.8  # 800ms reset delay before next serve

        if self.is_serving:
            self.serve_timer -= dt
            if self.serve_timer <= 0.0:
                self.serve_sipa()

        # 5. Update Visual Effects & HUD
        for ripple in self.ripples:
            ripple.update(dt)
        self.ripples = [r for r in self.ripples if r.is_alive]

        self.hud.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self._init_fonts()
        assert self.font_court and self.font_btn
        current_time_ms = float(pygame.time.get_ticks())

        # 1. Court Backdrop
        surface.fill(COLOR_BG_DARK)

        # Street asphalt road
        asphalt_rect = pygame.Rect(
            0,
            int(GROUND_Y) - 50,
            LOGICAL_W,
            LOGICAL_H - int(GROUND_Y) + 50
        )
        pygame.draw.rect(surface, COLOR_ASPHALT, asphalt_rect)

        # Street pavement chalk baseline
        pygame.draw.line(surface, COLOR_CHALK, (0, int(GROUND_Y)), (LOGICAL_W, int(GROUND_Y)), 3)

        # Court perspective lines
        pygame.draw.line(surface, COLOR_CHALK, (220, int(GROUND_Y)), (340, LOGICAL_H), 2)
        pygame.draw.line(surface, COLOR_CHALK, (LOGICAL_W - 220, int(GROUND_Y)), (LOGICAL_W - 340, LOGICAL_H), 2)
        pygame.draw.line(surface, COLOR_CHALK, (LOGICAL_CENTER_X, int(GROUND_Y)), (LOGICAL_CENTER_X, LOGICAL_H), 2)

        # Kicking zone guideline (subtle dashed/translucent line at KICK_TARGET_Y)
        pygame.draw.line(surface, (65, 72, 92), (60, int(KICK_TARGET_Y)), (LOGICAL_W - 60, int(KICK_TARGET_Y)), 1)
        surf_kick_lbl = self.font_court.render("KICK ZONE", True, (90, 98, 120))
        surface.blit(surf_kick_lbl, (70, int(KICK_TARGET_Y) - 18))

        # 2. Hit Targets & Approach Rings
        self.hit_system.draw(surface, current_time_ms)

        # 3. Hit Ripples VFX
        for ripple in self.ripples:
            ripple.draw(surface)

        # 4. Sipa Projectile (Motion trail, tassels, and metal washer)
        self.sipa.draw(surface)

        # 5. Live HUD Overlay (Score, Combo, Accuracy, Floating Judgments)
        self.hud.draw(surface)

        # 6. Cursor Aim Crosshair at Logical Mouse Position
        mx, my = int(self.mouse_pos.x), int(self.mouse_pos.y)
        pygame.draw.circle(surface, COLOR_TEXT_PRIMARY, (mx, my), 5, width=1)
        pygame.draw.line(surface, COLOR_TEXT_PRIMARY, (mx - 10, my), (mx + 10, my), 1)
        pygame.draw.line(surface, COLOR_TEXT_PRIMARY, (mx, my - 10), (mx, my + 10), 1)

        # 7. Return to Title Button
        btn_bg = COLOR_BRICK_RED if not self.is_back_hovered else (240, 85, 80)
        pygame.draw.rect(surface, btn_bg, self.back_button_rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_CARD_BORDER, self.back_button_rect, width=2, border_radius=8)
        surf_btn = self.font_btn.render("← BUMALIK (TITLE)", True, COLOR_TEXT_PRIMARY)
        surface.blit(surf_btn, surf_btn.get_rect(center=self.back_button_rect.center))
