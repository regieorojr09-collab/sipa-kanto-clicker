"""Core gameplay scene for Sipa: Kanto Clicker integrating physics, rhythm targets, avatar, taya, difficulty modifiers, and HUD."""

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
    COLOR_TASSEL_GOLD,
    COLOR_TASSEL_GREEN,
)
from entities.sipa import Sipa
from entities.avatar import Avatar
from entities.taya import Taya
from systems.hit_system import HitSystem
from systems.scoring import ScoreKeeper
from systems.difficulty import DifficultyController, DifficultyLevel
from systems.audio import AudioManager
from ui.hud import HUD
from ui.scenery import StreetScenery
from ui.fx import ParticleEmitter, ScreenShake
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

    def draw(self, surface: pygame.Surface, offset: Vector2 = Vector2(0, 0)) -> None:
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
        surface.blit(surf, (self.pos.x + offset.x - center[0], self.pos.y + offset.y - center[1]))


class PlayScene(Scene):
    """
    Main arcade/rhythm play scene coordinating:
    - Sipa kinematic projectile with wind acceleration
    - Avatar animation state machine (Paa, Tuhod, Siko, Stumble)
    - Taya NPC sideline director & taunter
    - HitSystem approach rings with difficulty scaling
    - DifficultyController (Pikon Meter, Hangin, Bilis, Dalawa modifiers)
    - ScoreKeeper & live HUD
    - Procedural StreetScenery parallax background & dynamic rage lighting
    - Procedural BGM synthesizer with dynamic tempo scaling & crowd cheering
    - VFX (ScreenShake, ParticleEmitter)
    - Round quota and transition to ResultsScene
    """

    def __init__(self, manager: SceneManager, difficulty_level: DifficultyLevel = DifficultyLevel.SAKTO) -> None:
        super().__init__(manager)
        self.difficulty_level: DifficultyLevel = difficulty_level
        self.mouse_pos: Vector2 = Vector2(LOGICAL_CENTER_X, GROUND_Y)

        # Entities
        self.sipa: Sipa = Sipa(x=380.0, y=GROUND_Y)
        self.avatar: Avatar = Avatar(x=460.0, y=GROUND_Y)
        self.taya: Taya = Taya(x=130.0, y=GROUND_Y)

        # Scenery & Systems
        self.scenery: StreetScenery = StreetScenery()
        self.difficulty_controller: DifficultyController = DifficultyController(level=self.difficulty_level)
        self.score_keeper: ScoreKeeper = ScoreKeeper(difficulty_mult=self.difficulty_controller.level.score_mult)
        self.hit_system: HitSystem = HitSystem()
        self.audio_manager: AudioManager = AudioManager()

        # UI & VFX
        self.hud: HUD = HUD(self.score_keeper, self.difficulty_controller)
        self.particle_emitter: ParticleEmitter = ParticleEmitter(max_particles=160)
        self.screen_shake: ScreenShake = ScreenShake(max_offset=14.0)

        # Event subscription for unified hit VFX/audio
        event_bus.subscribe(GameEvent.HIT_RESULT, self._on_game_hit_result)

        # Round & Arc State
        self.click_count: int = 0
        self.has_spawned_target_for_arc: bool = False
        self.serve_timer: float = 0.5
        self.is_serving: bool = False
        self.serves_completed: int = 0
        self.max_serves: int = 15  # 15 serves per round quota
        self.ripples: List[HitRippleVFX] = []

        # Pause / Menu Button
        self.pause_button_rect: pygame.Rect = pygame.Rect(32, 24, 180, 42)
        self.is_pause_hovered: bool = False
        self._is_paused: bool = False

        # Fonts
        self.font_court: Optional[pygame.font.Font] = None
        self.font_btn: Optional[pygame.font.Font] = None
        self.font_quota: Optional[pygame.font.Font] = None

    def _init_fonts(self) -> None:
        if self.font_court is None:
            self.font_court = pygame.font.Font(None, 24)
            self.font_btn = pygame.font.Font(None, 26)
            self.font_quota = pygame.font.Font(None, 22)

    def on_enter(self, **kwargs) -> None:
        self._init_fonts()
        # If resuming from pause overlay, simply resume audio and keep state intact
        if self._is_paused:
            self._is_paused = False
            self.audio_manager.resume_bgm()
            return

        if "difficulty_level" in kwargs and kwargs["difficulty_level"]:
            self.difficulty_level = kwargs["difficulty_level"]
            self.difficulty_controller.level = self.difficulty_level
            self.score_keeper.difficulty_mult = self.difficulty_level.score_mult

        self.serve_timer = 0.5
        self.is_serving = False
        self.has_spawned_target_for_arc = False
        self.sipa.reset(x=380.0, y=GROUND_Y)
        self.avatar.pos = Vector2(460.0, GROUND_Y)
        self.taya.pos = Vector2(130.0, GROUND_Y)

        self.audio_manager.start_bgm()
        event_bus.publish(GameEvent.ROUND_START)

    def on_exit(self) -> None:
        # If suspended by a modal overlay (e.g. PauseOverlay), pause BGM without destroying gameplay state
        if self._is_paused:
            self.audio_manager.pause_bgm()
            return

        event_bus.unsubscribe(GameEvent.HIT_RESULT, self._on_game_hit_result)
        self.audio_manager.stop_bgm()
        self.score_keeper.destroy()
        self.hud.destroy()
        self.hit_system.clear()
        self.avatar.destroy()
        self.taya.destroy()
        self.audio_manager.destroy()
        self.difficulty_controller.destroy()
        self.particle_emitter.clear()

    def _restart_round(self) -> None:
        """Restarts the active round from zero."""
        self._is_paused = False
        self.score_keeper.reset()
        self.difficulty_controller.reset()
        self.hit_system.clear()
        self.serves_completed = 0
        self.has_spawned_target_for_arc = False
        self.audio_manager.resume_bgm()
        self.serve_sipa()

    def _finish_round(self) -> None:
        """Transitions to the round results screen."""
        self._is_paused = False
        from scenes.results_scene import ResultsScene
        stats = self.score_keeper.get_stats()
        event_bus.publish(
            GameEvent.ROUND_END,
            passed=True,
            final_score=self.score_keeper.score,
            max_combo=self.score_keeper.max_combo
        )
        self.audio_manager.stop_bgm()
        self.manager.switch_with_transition(
            ResultsScene(self.manager, stats=stats, difficulty_level=self.difficulty_level),
            duration=0.35
        )

    def serve_sipa(self) -> None:
        """Launches a new sipa from court sidelines toward center with wind and Taya callout."""
        serve_from_left = random.random() > 0.3
        start_x = 340.0 if serve_from_left else (LOGICAL_W - 340.0)
        target_dir = 1.0 if serve_from_left else -1.0

        self.sipa.reset(x=start_x, y=GROUND_Y - 10.0)

        vx = target_dir * random.uniform(220.0, 320.0)
        vy = -random.uniform(780.0, 880.0)
        active_wind = self.difficulty_controller.wind_force
        self.sipa.launch(Vector2(vx, vy), spin=random.uniform(2.0, 3.5), wind_force=active_wind)

        self.has_spawned_target_for_arc = False
        self.is_serving = False
        self.serves_completed += 1

        # Taya shouts serve callout
        self.taya.trigger_serve_call()

    def handle_event(self, event: pygame.event.Event, logical_mouse_pos: Vector2) -> None:
        self.mouse_pos = logical_mouse_pos
        self.is_pause_hovered = self.pause_button_rect.collidepoint(self.mouse_pos.x, self.mouse_pos.y)

        # 1. Pause Button Click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_pause_hovered:
                self._open_pause_menu()
                return

        # 2. ESC Key -> Push Pause Menu
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._open_pause_menu()
            return

        # 3. Hit Input: Mouse Left-Click or Z/X Keys
        is_hit_trigger = False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            is_hit_trigger = True
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_z, pygame.K_x):
            is_hit_trigger = True

        if is_hit_trigger:
            self._process_hit_attempt()

    def _open_pause_menu(self) -> None:
        """Pushes the pause overlay on top of the active scene and pauses BGM."""
        self._is_paused = True
        self.audio_manager.pause_bgm()
        from ui.menus import PauseOverlay
        self.manager.push(PauseOverlay(self.manager, on_restart_callback=self._restart_round))


    def _on_game_hit_result(self, judgment: str, was_miss: bool = False, position: tuple = (640, 360), **kwargs) -> None:
        """Unified responder for hit/miss events: drives SFX, ripples, screen shake, particles, and crowd cheers."""
        target_pos = Vector2(position[0], position[1]) if isinstance(position, (tuple, list)) else Vector2(position)

        if not was_miss:
            # 1. SFX
            self.audio_manager.play_kick(judgment)

            # 2. VFX: Ripple & Particle Burst
            ripple_color = COLOR_SUNSHINE if judgment == "Swak!" else COLOR_RETRO_CYAN
            self.ripples.append(HitRippleVFX(target_pos, ripple_color))
            self.particle_emitter.burst(
                target_pos,
                count=22 if judgment == "Swak!" else 14,
                colors=[COLOR_SUNSHINE, COLOR_RETRO_CYAN, COLOR_TASSEL_GOLD, COLOR_TASSEL_GREEN]
            )

            # 3. Check Combo Milestones (10 and 20+ combos trigger spectator crowd cheering)
            combo = self.score_keeper.current_combo
            if combo > 0 and combo % 10 == 0:
                event_bus.publish(GameEvent.COMBO_MILESTONE, combo_count=combo)
                self.audio_manager.play_crowd_cheer(combo)
        else:
            # Miss feedback
            self.audio_manager.play_miss()
            self.screen_shake.add_trauma(0.55)
            self.ripples.append(HitRippleVFX(target_pos, COLOR_BRICK_RED))
            self.particle_emitter.burst(target_pos, count=12, colors=[COLOR_BRICK_RED])

    def _process_hit_attempt(self) -> None:
        """Evaluates player click against active rhythm targets and relaunches sipa."""
        self.click_count += 1
        current_time_ms = float(pygame.time.get_ticks())
        hit_result = self.hit_system.check_hit(self.mouse_pos, current_time_ms)

        if hit_result is not None:
            judgment = str(hit_result["judgment"])
            was_miss = bool(hit_result["was_miss"])

            if not was_miss:
                # Relaunch sipa with exit velocity scaled by accuracy tier
                multiplier = 1.0
                if judgment == "Swak!":
                    multiplier = 1.0
                elif judgment == "Puwede":
                    multiplier = 0.85
                elif judgment == "Daplis":
                    multiplier = 0.68

                center_bias = 1.0 if self.sipa.pos.x < LOGICAL_CENTER_X else -1.0
                vx = center_bias * random.uniform(220.0, 340.0) + random.uniform(-25.0, 25.0)
                vy = -BASE_KICK_VELOCITY * multiplier
                active_wind = self.difficulty_controller.wind_force

                self.sipa.launch(Vector2(vx, vy), spin=random.uniform(2.5, 4.0), wind_force=active_wind)
                self.has_spawned_target_for_arc = False
        else:
            # Clicked empty space: subtle cursor feedback
            self.ripples.append(HitRippleVFX(self.mouse_pos, (90, 100, 120)))

    def update(self, dt: float) -> None:
        current_time_ms = float(pygame.time.get_ticks())
        current_time_sec = current_time_ms / 1000.0

        # 1. Update Difficulty Controller (Pikon decay, modifiers)
        self.difficulty_controller.update(dt)

        # 2. Update Scenery & Dynamic BGM tempo
        self.scenery.update(dt, self.difficulty_controller.pikon_meter)
        self.audio_manager.update_bgm(self.difficulty_controller.pikon_meter)

        # 3. Update Entities
        self.sipa.update(dt)

        if self.hit_system.active_targets:
            self.avatar.track_position(self.hit_system.active_targets[0].cx)
        elif self.sipa.is_airborne:
            self.avatar.track_position(self.sipa.pos.x)

        self.avatar.update(dt, current_time_sec)
        self.taya.update(dt)

        # 4. Check trajectory apex to predict landing and spawn approach ring
        if self.sipa.is_airborne and self.sipa.vel.y >= 0.0 and not self.has_spawned_target_for_arc:
            self.has_spawned_target_for_arc = True
            pred_x, pred_y, arrival_ms = self.sipa.predict_landing(KICK_TARGET_Y)

            if arrival_ms > 120.0:
                t_arrive = current_time_ms + arrival_ms
                dur = arrival_ms * self.difficulty_controller.approach_rate_mult

                # Apply Chaos offset if unlocked
                if self.difficulty_controller.chaos_offset:
                    pred_x = max(100.0, min(1180.0, pred_x + random.uniform(-25.0, 25.0)))

                self.hit_system.spawn_target(
                    cx=pred_x,
                    cy=pred_y,
                    t_arrive=t_arrive,
                    t_duration=dur
                )

                # Dalawa modifier: spawn secondary quick target
                if self.difficulty_controller.double_target:
                    offset_x = -60.0 if pred_x > LOGICAL_CENTER_X else 60.0
                    self.hit_system.spawn_target(
                        cx=max(100.0, min(1180.0, pred_x + offset_x)),
                        cy=pred_y - 35.0,
                        t_arrive=t_arrive - 140.0,
                        t_duration=dur * 0.85
                    )

        # 5. Update Hit System (processes expired/missed targets)
        expired_events = self.hit_system.update(current_time_ms)
        if expired_events:
            self.audio_manager.play_miss()
            self.screen_shake.add_trauma(0.45)

        # 6. Handle Ground Landing & Serve Resets or Round Complete
        if self.sipa.is_grounded and not self.is_serving:
            if self.serves_completed >= self.max_serves:
                self._finish_round()
                return

            self.is_serving = True
            self.serve_timer = 0.8
            self.screen_shake.add_trauma(0.25)

        if self.is_serving:
            self.serve_timer -= dt
            if self.serve_timer <= 0.0:
                self.serve_sipa()

        # 7. Update VFX & UI
        self.screen_shake.update(dt)
        self.particle_emitter.update(dt)

        for ripple in self.ripples:
            ripple.update(dt)
        self.ripples = [r for r in self.ripples if r.is_alive]

        self.hud.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        self._init_fonts()
        assert self.font_court and self.font_btn and self.font_quota
        current_time_ms = float(pygame.time.get_ticks())

        # Camera Shake Offset (applied to scenery and world geometry)
        cam = self.screen_shake.get_offset()
        ox, oy = int(cam.x), int(cam.y)

        # 1. Render Procedural Street Scenery (Background, clouds, skyline, sari-sari store, tricycle, asphalt)
        self.scenery.draw(surface, cam)

        # Kicking zone guideline
        pygame.draw.line(surface, (65, 72, 92), (60, int(KICK_TARGET_Y) + oy), (LOGICAL_W - 60, int(KICK_TARGET_Y) + oy), 1)
        surf_kick_lbl = self.font_court.render("KICK ZONE", True, (90, 98, 120))
        surface.blit(surf_kick_lbl, (70, int(KICK_TARGET_Y) - 18 + oy))

        # 2. World Entities (Offset by screen shake)
        world_surf = pygame.Surface((LOGICAL_W, LOGICAL_H), pygame.SRCALPHA)

        self.taya.draw(world_surf)
        self.avatar.draw(world_surf)
        self.sipa.draw(world_surf)
        self.hit_system.draw(world_surf, current_time_ms)

        for ripple in self.ripples:
            ripple.draw(world_surf)
        self.particle_emitter.draw(world_surf)

        surface.blit(world_surf, (ox, oy))

        # 3. Fixed UI Overlay (No Screen Shake for crisp readability)
        self.hud.draw(surface)

        # Round Progress / Quota Tracker
        quota_str = f"TIRA (SERVES): {self.serves_completed}/{self.max_serves}"
        surf_quota = self.font_quota.render(quota_str, True, COLOR_TEXT_MUTED)
        surface.blit(surf_quota, (34, 76))

        # 4. Cursor Crosshair at Logical Mouse Position
        mx, my = int(self.mouse_pos.x), int(self.mouse_pos.y)
        pygame.draw.circle(surface, COLOR_TEXT_PRIMARY, (mx, my), 5, width=1)
        pygame.draw.line(surface, COLOR_TEXT_PRIMARY, (mx - 10, my), (mx + 10, my), 1)
        pygame.draw.line(surface, COLOR_TEXT_PRIMARY, (mx, my - 10), (mx, my + 10), 1)

        # 5. Pause Button
        btn_bg = COLOR_BRICK_RED if not self.is_pause_hovered else (240, 85, 80)
        pygame.draw.rect(surface, btn_bg, self.pause_button_rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_CARD_BORDER, self.pause_button_rect, width=2, border_radius=8)
        surf_btn = self.font_btn.render("⏸ PAUSE [ESC]", True, COLOR_TEXT_PRIMARY)
        surface.blit(surf_btn, surf_btn.get_rect(center=self.pause_button_rect.center))

