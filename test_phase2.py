"""Automated headless test suite for Phase 2: Sipa kinematics, approach rings, and scoring."""

import math
import os
import unittest

# Force dummy video driver for headless testing
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
from pygame.math import Vector2

from core.events import EventBus, GameEvent, event_bus
from core.settings import (
    LOGICAL_W,
    LOGICAL_H,
    GRAVITY,
    HIT_CIRCLE_RADIUS,
    APPROACH_RING_MAX_R,
    TIMING_SWAK_MS,
    TIMING_PUWEDE_MS,
    TIMING_DAPLIS_MS,
    POINTS_SWAK,
    POINTS_PUWEDE,
    POINTS_DAPLIS,
    POINTS_BAGSAK,
    COLOR_RETRO_CYAN,
    COLOR_SUNSHINE,
    COLOR_RETRO_MAGENTA,
)
from entities.sipa import Sipa
from systems.hit_system import HitSystem, HitTarget, TargetState
from systems.scoring import ScoreKeeper
from scenes.scene_manager import SceneManager
from scenes.play_scene import PlayScene


class TestPhase2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        event_bus.clear()

    def test_sipa_quadratic_prediction(self):
        """Validates the analytical quadratic solver against exact mathematical ground truth."""
        sipa = Sipa(x=500.0, y=200.0)
        sipa.vel = Vector2(200.0, 0.0)  # Horizontal flight from apex

        target_y = 520.0
        # Expected time: y(t) = 200 + 0.5 * 980 * t^2 = 520
        # 490 * t^2 = 320 -> t = sqrt(320 / 490) s
        expected_t = math.sqrt(320.0 / 490.0)
        expected_arrival_ms = expected_t * 1000.0
        expected_x = 500.0 + (200.0 * expected_t)

        pred_x, pred_y, arrival_ms = sipa.predict_landing(target_y)

        self.assertAlmostEqual(pred_y, target_y, places=2)
        self.assertAlmostEqual(arrival_ms, expected_arrival_ms, places=2)
        self.assertAlmostEqual(pred_x, expected_x, places=2)

        # Test upward launch:
        sipa.pos = Vector2(400.0, 500.0)
        sipa.vel = Vector2(100.0, -600.0)
        # 490 * t^2 - 600 * t - 20 = 0
        # t = (600 + sqrt(360000 + 39200)) / 980
        expected_upward_t = (600.0 + math.sqrt(399200.0)) / 980.0
        _, _, upward_arrival_ms = sipa.predict_landing(520.0)
        self.assertAlmostEqual(upward_arrival_ms, expected_upward_t * 1000.0, places=2)

    def test_approach_ring_radius_and_color_interpolation(self):
        """Verifies approach ring radius shrinking and Cyan -> Yellow -> Magenta color transitions."""
        target = HitTarget(
            cx=640.0,
            cy=500.0,
            t_arrive=1000.0,
            t_duration=800.0,
            r_hit=32.0,
            r_max=128.0,
        )

        # At spawn (t = 200 ms, factor = 1.0)
        r_start = target.get_current_ring_radius(200.0)
        color_start = target.get_ring_color(200.0)
        self.assertAlmostEqual(r_start, 128.0)
        self.assertEqual(color_start, COLOR_RETRO_CYAN)

        # At midpoint (t = 600 ms, factor = 0.5)
        r_mid = target.get_current_ring_radius(600.0)
        color_mid = target.get_ring_color(600.0)
        self.assertAlmostEqual(r_mid, 80.0)  # 32 + (128 - 32) * 0.5 = 80
        self.assertEqual(color_mid, COLOR_SUNSHINE)

        # At arrival time (t = 1000 ms, factor = 0.0)
        r_arrive = target.get_current_ring_radius(1000.0)
        color_arrive = target.get_ring_color(1000.0)
        self.assertAlmostEqual(r_arrive, 32.0)
        self.assertEqual(color_arrive, COLOR_RETRO_MAGENTA)

        # Past arrival time (t = 1050 ms, clamped)
        r_late = target.get_current_ring_radius(1050.0)
        self.assertAlmostEqual(r_late, 32.0)

    def test_euclidean_hit_detection_and_timing_judgments(self):
        """Verifies spatial distance checking and timing accuracy judgment windows."""
        hit_system = HitSystem()
        target = hit_system.spawn_target(cx=500.0, cy=400.0, t_arrive=1000.0, r_hit=32.0)

        # 1. Miss outside circle radius (distance = 50px > 32px)
        miss_click = hit_system.check_hit(Vector2(550.0, 400.0), current_time_ms=1000.0)
        self.assertIsNone(miss_click)
        self.assertTrue(target.is_active)

        # 2. Inside circle radius - Test "Swak!" (<= 25ms error)
        swak_result = hit_system.check_hit(Vector2(510.0, 400.0), current_time_ms=1015.0)
        self.assertIsNotNone(swak_result)
        assert swak_result is not None
        self.assertEqual(swak_result["judgment"], "Swak!")
        self.assertEqual(swak_result["points"], POINTS_SWAK)
        self.assertFalse(swak_result["was_miss"])
        self.assertEqual(target.state, TargetState.HIT)

        # 3. Test "Puwede" (<= 70ms error)
        hit_system.clear()
        target2 = hit_system.spawn_target(cx=500.0, cy=400.0, t_arrive=2000.0, r_hit=32.0)
        puwede_result = hit_system.check_hit(Vector2(500.0, 400.0), current_time_ms=2050.0)
        assert puwede_result is not None
        self.assertEqual(puwede_result["judgment"], "Puwede")
        self.assertEqual(puwede_result["points"], POINTS_PUWEDE)

        # 4. Test "Daplis" (<= 120ms error)
        hit_system.clear()
        target3 = hit_system.spawn_target(cx=500.0, cy=400.0, t_arrive=3000.0, r_hit=32.0)
        daplis_result = hit_system.check_hit(Vector2(500.0, 400.0), current_time_ms=3100.0)
        assert daplis_result is not None
        self.assertEqual(daplis_result["judgment"], "Daplis")
        self.assertEqual(daplis_result["points"], POINTS_DAPLIS)

        # 5. Test Late Miss / Bagsak! via click (> 120ms error)
        hit_system.clear()
        target4 = hit_system.spawn_target(cx=500.0, cy=400.0, t_arrive=4000.0, r_hit=32.0)
        late_result = hit_system.check_hit(Vector2(500.0, 400.0), current_time_ms=4150.0)
        assert late_result is not None
        self.assertEqual(late_result["judgment"], "Bagsak!")
        self.assertTrue(late_result["was_miss"])

        # 6. Test Expiration without click via update()
        hit_system.clear()
        target5 = hit_system.spawn_target(cx=500.0, cy=400.0, t_arrive=5000.0, r_hit=32.0)
        expired = hit_system.update(current_time_ms=5150.0)
        self.assertEqual(len(expired), 1)
        self.assertEqual(expired[0]["judgment"], "Bagsak!")
        self.assertEqual(len(hit_system.active_targets), 0)

    def test_score_combo_multiplier_formula(self):
        """Verifies score accumulation, combo multiplier math, and accuracy percentages."""
        score_keeper = ScoreKeeper(difficulty_mult=1.5)

        # 1. First Swak hit (Combo = 1, Base = 300)
        # Factor = 1 + min(1, 100) / 25 = 1 + 0.04 = 1.04
        # Points = int(300 * 1.04 * 1.5) = int(468.0) = 468
        event_bus.publish(GameEvent.HIT_RESULT, judgment="Swak!", points=300, was_miss=False)
        self.assertEqual(score_keeper.current_combo, 1)
        self.assertEqual(score_keeper.score, 468)
        self.assertAlmostEqual(score_keeper.accuracy, 100.0)

        # 2. Add 24 more consecutive Swak hits (Combo = 25)
        for _ in range(24):
            event_bus.publish(GameEvent.HIT_RESULT, judgment="Swak!", points=300, was_miss=False)
        self.assertEqual(score_keeper.current_combo, 25)
        self.assertEqual(score_keeper.max_combo, 25)
        self.assertAlmostEqual(score_keeper.accuracy, 100.0)

        # 3. Bagsak (Miss) -> Breaks combo and drops accuracy
        event_bus.publish(GameEvent.HIT_RESULT, judgment="Bagsak!", points=0, was_miss=True)
        self.assertEqual(score_keeper.current_combo, 0)
        self.assertEqual(score_keeper.max_combo, 25)
        # Total notes = 26, 25 Swak, 1 Bagsak -> Accuracy = (25 * 300) / (26 * 300) * 100%
        expected_acc = (25.0 / 26.0) * 100.0
        self.assertAlmostEqual(score_keeper.accuracy, expected_acc, places=2)

        score_keeper.destroy()

    def test_play_scene_headless_loop(self):
        """Simulates PlayScene initialization, event dispatch, kinematic updates, and rendering."""
        manager = SceneManager()
        scene = PlayScene(manager)
        manager.switch(scene)

        surface = pygame.Surface((LOGICAL_W, LOGICAL_H))

        # Initial serve
        scene.serve_sipa()
        self.assertTrue(scene.sipa.is_airborne)

        # Step frame updates
        for _ in range(60):
            scene.update(0.016)

        # Render pass without crashing
        scene.draw(surface)

        # Test Z/X hit key dispatch
        key_event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_z})
        scene.handle_event(key_event, Vector2(640, 360))

        # Teardown
        manager.pop()


if __name__ == "__main__":
    unittest.main()
