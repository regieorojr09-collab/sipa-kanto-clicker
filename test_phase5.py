"""Automated test suite for Phase 5: Art, Polish, Scenery, & Production Deployment.

Verifies:
1. StreetScenery procedural generation, cloud drifting and wrapping, and dynamic sky color rage shifting.
2. AudioManager procedural BGM synthesis (normal and rage tempo), pause/resume, tempo scaling, and crowd cheers.
3. TransitionOverlay fade math (alpha progression 0 -> 255 -> 0), state machine, and midpoint scene switching.
4. ResultsScene dynamic score rolling interpolation (0 to final score over 1.2s) and celebratory particle sparkles.
5. PlayScene full Phase 5 integration running with scenery, camera shake, BGM tempo scaling, and pause overlay.
"""

import os
import unittest
import pygame
from pygame.math import Vector2

# Force headless dummy driver for testing environments
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from core.settings import (
    LOGICAL_W,
    LOGICAL_H,
    GROUND_Y,
    COLOR_SUNSHINE,
    COLOR_RETRO_CYAN,
)
from core.events import GameEvent, event_bus
from scenes.scene_manager import SceneManager
from scenes.play_scene import PlayScene
from scenes.results_scene import ResultsScene, compute_street_rank
from ui.scenery import StreetScenery, ProceduralCloud
from ui.fx import TransitionOverlay, TransitionState
from systems.audio import AudioManager, _synthesize_bgm_track


class TestPhase5ArtPolishDeployment(unittest.TestCase):
    """Automated verification suite for Phase 5 deliverables."""

    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.display.set_mode((LOGICAL_W, LOGICAL_H))

    def test_street_scenery_generation_and_clouds(self):
        """Verifies procedural street scenery initialization, cloud motion, and wrap-around."""
        scenery = StreetScenery()
        self.assertGreater(len(scenery.clouds), 0)
        self.assertIsNotNone(scenery.sky_surface)
        self.assertIsNotNone(scenery.city_silhouette)
        self.assertIsNotNone(scenery.sari_sari_surface)
        self.assertIsNotNone(scenery.tricycle_surface)
        self.assertIsNotNone(scenery.asphalt_surface)

        # 1. Cloud drifting
        cloud = scenery.clouds[0]
        initial_x = cloud.x
        scenery.update(1.0, pikon_meter=0.0)
        self.assertGreater(cloud.x, initial_x)

        # 2. Cloud horizontal wrap-around
        cloud.x = LOGICAL_W + 90.0
        cloud.update(0.1)
        self.assertLess(cloud.x, 0.0)

        # 3. Sky rage color shift
        # Sample mid-sky color at pikon 0% (cool dusk)
        scenery.update(0.1, pikon_meter=0.0)
        col_calm = scenery.sky_surface.get_at((LOGICAL_W // 2, int(GROUND_Y * 0.5)))

        # Update to 100% pikon rage (warm amber / sunset fire)
        scenery.update(0.1, pikon_meter=100.0)
        col_rage = scenery.sky_surface.get_at((LOGICAL_W // 2, int(GROUND_Y * 0.5)))

        # Red channel should increase significantly under rage
        self.assertGreater(col_rage.r, col_calm.r)

        # 4. Rendering with camera screen shake offset
        test_surf = pygame.Surface((LOGICAL_W, LOGICAL_H))
        scenery.draw(test_surf, offset=Vector2(5.0, -3.0))

    def test_bgm_synthesizer_and_tempo_scaling(self):
        """Verifies procedural PCM BGM generation, start/pause/resume, and tempo scaling."""
        # 1. Direct BGM buffer synthesis
        normal_track = _synthesize_bgm_track(tempo_bpm=120.0, is_rage=False)
        rage_track = _synthesize_bgm_track(tempo_bpm=152.0, is_rage=True)

        self.assertIsNotNone(normal_track)
        self.assertIsNotNone(rage_track)

        # Normal track (120 BPM) is 4.0 seconds; Rage track (152 BPM) is ~3.15 seconds
        self.assertGreater(normal_track.get_length(), rage_track.get_length())

        # 2. AudioManager BGM lifecycle
        audio = AudioManager()
        self.assertIsNotNone(audio.bgm_normal)
        self.assertIsNotNone(audio.bgm_rage)
        self.assertFalse(audio.is_bgm_playing)

        # Start before unlock -> requested flag set
        audio.start_bgm()
        self.assertTrue(audio._bgm_requested)

        # Unlock audio -> starts BGM
        audio.unlock_audio()
        self.assertTrue(audio.is_unlocked)

        # Pause and Resume
        audio.pause_bgm()
        self.assertTrue(audio._bgm_paused)
        audio.resume_bgm()
        self.assertFalse(audio._bgm_paused)

        # 3. Dynamic Tempo Scaling with Pikon Meter
        audio.update_bgm(pikon_meter=50.0)
        self.assertFalse(audio.is_rage_bgm)

        # Exceed 80% rage threshold -> switches to rage BGM
        audio.update_bgm(pikon_meter=85.0)
        self.assertTrue(audio.is_rage_bgm)

        # Drop below 80% -> returns to normal BGM
        audio.update_bgm(pikon_meter=70.0)
        self.assertFalse(audio.is_rage_bgm)

        # 4. Crowd Cheering
        audio.play_crowd_cheer(combo=10)
        audio.play_crowd_cheer(combo=20)

        audio.destroy()

    def test_transition_overlay_math(self):
        """Verifies TransitionOverlay state machine and alpha interpolation progression."""
        overlay = TransitionOverlay(width=LOGICAL_W, height=LOGICAL_H)
        self.assertEqual(overlay.state, TransitionState.IDLE)
        self.assertEqual(overlay.alpha, 0)
        self.assertFalse(overlay.is_active)

        midpoint_called = False

        def on_midpoint():
            nonlocal midpoint_called
            midpoint_called = True

        # Start 0.4s transition (half-duration = 0.2s)
        overlay.start_transition(on_midpoint_callback=on_midpoint, duration=0.4)
        self.assertEqual(overlay.state, TransitionState.FADING_OUT)
        self.assertTrue(overlay.is_active)

        # Quarter way: fading out (alpha rising)
        overlay.update(0.1)
        self.assertGreater(overlay.alpha, 0)
        self.assertLess(overlay.alpha, 255)
        self.assertFalse(midpoint_called)

        # Halfway point: reaches full black and executes midpoint callback
        overlay.update(0.1)
        self.assertTrue(midpoint_called)
        self.assertEqual(overlay.state, TransitionState.FADING_IN)

        # Fading in (alpha descending)
        overlay.update(0.1)
        self.assertGreater(overlay.alpha, 0)
        self.assertLess(overlay.alpha, 255)

        # Complete transition: returns to IDLE with 0 alpha
        overlay.update(0.1)
        self.assertEqual(overlay.state, TransitionState.IDLE)
        self.assertEqual(overlay.alpha, 0)
        self.assertFalse(overlay.is_active)

        # Render test
        surf = pygame.Surface((LOGICAL_W, LOGICAL_H))
        overlay.draw(surf)

    def test_results_screen_score_roll_and_sparkles(self):
        """Verifies ResultsScene rolling score animation and celebratory sparkles."""
        manager = SceneManager()
        stats = {
            "score": 12500,
            "max_combo": 18,
            "accuracy": 96.5,
            "counts": {"Swak!": 14, "Puwede": 3, "Daplis": 1, "Bagsak!": 0},
        }
        results = ResultsScene(manager, stats=stats)
        manager.switch(results)

        # Initial state: score starts rolling from 0
        self.assertEqual(results.target_score, 12500)
        self.assertEqual(results.displayed_score, 0)
        self.assertTrue(results.is_rolling)

        # S-Rank should activate celebratory sparkles
        grade, _, _ = compute_street_rank(96.5)
        self.assertEqual(grade, "S")

        # Step 0.6 seconds in realistic 16ms frame increments (halfway through 1.2s roll)
        for _ in range(35):
            results.update(0.016)
        self.assertGreater(results.displayed_score, 0)
        self.assertLess(results.displayed_score, 12500)
        self.assertTrue(results.is_rolling)
        self.assertGreater(len(results.sparkle_emitter.particles), 0)

        # Step remaining duration past 1.2s: reaches exact target score
        for _ in range(45):
            results.update(0.016)
        self.assertEqual(results.displayed_score, 12500)
        self.assertFalse(results.is_rolling)

        # Render pass
        surf = pygame.Surface((LOGICAL_W, LOGICAL_H))
        results.draw(surf)

        manager.pop()

    def test_full_play_scene_phase5_integration(self):
        """Verifies PlayScene integrated with StreetScenery, BGM tempo scaling, and Pause Overlay."""
        manager = SceneManager()
        scene = PlayScene(manager)
        manager.switch(scene)

        surface = pygame.Surface((LOGICAL_W, LOGICAL_H))

        # 1. Verify scenery and BGM attached
        self.assertIsNotNone(scene.scenery)
        self.assertIsNotNone(scene.audio_manager)

        # 2. Advance frames and check scenery update
        initial_cloud_x = scene.scenery.clouds[0].x
        for _ in range(30):
            scene.update(0.016)
        self.assertGreater(scene.scenery.clouds[0].x, initial_cloud_x)

        # 3. Simulate high rage and verify BGM & sky respond
        scene.difficulty_controller.pikon_meter = 85.0
        scene.update(0.016)
        self.assertTrue(scene.audio_manager.is_rage_bgm)
        self.assertEqual(scene.scenery.pikon_meter, 85.0)

        # 4. Simulate pause overlay and verify BGM pause
        scene._open_pause_menu()
        self.assertTrue(scene.audio_manager._bgm_paused)

        # Pop pause overlay
        manager.pop()
        scene.audio_manager.resume_bgm()
        self.assertFalse(scene.audio_manager._bgm_paused)

        # 5. Render full frame
        scene.draw(surface)

        manager.pop()


if __name__ == "__main__":
    unittest.main()
