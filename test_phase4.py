"""Automated headless test suite for Phase 4: Difficulty Controller, Pikon Modifiers, Pause, and Results."""

import math
import os
import unittest

# Force dummy video driver for headless testing
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
from pygame.math import Vector2

from core.events import GameEvent, event_bus
from core.settings import LOGICAL_W, LOGICAL_H, GROUND_Y
from entities.sipa import Sipa
from systems.difficulty import DifficultyController, DifficultyLevel
from ui.menus import PauseOverlay
from scenes.results_scene import ResultsScene, compute_street_rank
from scenes.scene_manager import SceneManager
from scenes.title_scene import TitleScene
from scenes.play_scene import PlayScene


class TestPhase4(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        event_bus.clear()

    def test_pikon_meter_accumulation_decay_and_thresholds(self):
        """Verifies Pikon accumulation, threshold event dispatches, modifiers, and passive decay."""
        ctrl = DifficultyController(DifficultyLevel.SAKTO)
        self.assertEqual(ctrl.pikon_meter, 0.0)

        thresholds_received = []

        def on_threshold(level: int = 0, modifier: str = "", **kwargs):
            thresholds_received.append((level, modifier))

        event_bus.subscribe(GameEvent.PIKON_THRESHOLD, on_threshold)

        # 1. Accumulate hits up to 35% (+5 per Swak hit)
        for _ in range(7):
            event_bus.publish(GameEvent.HIT_RESULT, judgment="Swak!", points=300, was_miss=False, combo=1)

        self.assertEqual(ctrl.pikon_meter, 35.0)
        # Should have triggered 30% Hangin modifier
        self.assertIn((30, "Hangin"), thresholds_received)
        self.assertNotEqual(ctrl.wind_force, 0.0)

        # 2. Push past 50% (Bilis) and 65% (Dalawa)
        for _ in range(7):
            event_bus.publish(GameEvent.HIT_RESULT, judgment="Swak!", points=300, was_miss=False, combo=1)

        self.assertEqual(ctrl.pikon_meter, 70.0)
        self.assertIn((50, "Bilis"), thresholds_received)
        self.assertIn((65, "Dalawa"), thresholds_received)
        self.assertLess(ctrl.approach_rate_mult, 1.0)
        self.assertTrue(ctrl.double_target)

        # 3. Test Miss penalty: drops by 15%
        event_bus.publish(GameEvent.HIT_RESULT, judgment="Bagsak!", points=0, was_miss=True)
        self.assertEqual(ctrl.pikon_meter, 55.0)

        # 4. Passive decay when idle > 3 seconds
        ctrl.update(3.0)  # Reaches idle threshold
        ctrl.update(2.0)  # 2 seconds of decay at 2%/s = -4%
        self.assertAlmostEqual(ctrl.pikon_meter, 51.0, places=1)

        ctrl.destroy()

    def test_wind_affected_sipa_kinematics_and_landing_prediction(self):
        """Verifies predictive landing solver accuracy under constant lateral wind acceleration."""
        sipa = Sipa(x=500.0, y=200.0)
        # Launch from apex with vx=0, vy=0 under wind_force = 120.0 px/s^2
        wind_accel = 120.0
        sipa.launch(velocity=Vector2(0.0, 0.0), wind_force=wind_accel)

        target_y = 520.0
        # Expected descent time: 0.5 * 980 * t^2 = 320 -> t = sqrt(320/490) s
        expected_t = math.sqrt(320.0 / 490.0)
        # Expected x displacement with vx0=0: 0.5 * wind_accel * t^2
        expected_dx = 0.5 * wind_accel * (expected_t * expected_t)
        expected_x = 500.0 + expected_dx

        pred_x, pred_y, arrival_ms = sipa.predict_landing(target_y)

        self.assertAlmostEqual(arrival_ms, expected_t * 1000.0, places=1)
        self.assertAlmostEqual(pred_x, expected_x, places=0)

        # Simulate frame-by-frame kinematics up to arrival time and verify agreement
        dt = 0.010
        total_time = 0.0
        while total_time < expected_t:
            sipa.update(dt)
            total_time += dt

        # Final position must be close to predicted position
        self.assertAlmostEqual(sipa.pos.x, pred_x, delta=3.0)

    def test_results_scene_street_rank_grading(self):
        """Verifies Filipino street rank thresholds and ResultsScene render stability."""
        self.assertEqual(compute_street_rank(98.0)[0], "S")
        self.assertEqual(compute_street_rank(98.0)[1], "HARI NG KANTO")

        self.assertEqual(compute_street_rank(89.0)[0], "A")
        self.assertEqual(compute_street_rank(89.0)[1], "BETERANO")

        self.assertEqual(compute_street_rank(79.0)[0], "B")
        self.assertEqual(compute_street_rank(79.0)[1], "MARUNONG")

        self.assertEqual(compute_street_rank(65.0)[0], "C")
        self.assertEqual(compute_street_rank(65.0)[1], "BAGITO")

        self.assertEqual(compute_street_rank(45.0)[0], "F")
        self.assertEqual(compute_street_rank(45.0)[1], "KULELAT")

        # Instantiate ResultsScene and test drawing
        manager = SceneManager()
        stats = {
            "score": 125400,
            "max_combo": 38,
            "accuracy": 92.4,
            "counts": {"Swak!": 42, "Puwede": 10, "Daplis": 2, "Bagsak!": 1},
        }
        results = ResultsScene(manager, stats=stats, difficulty_level=DifficultyLevel.SAKTO)
        manager.switch(results)

        surface = pygame.Surface((LOGICAL_W, LOGICAL_H))
        results.draw(surface)

        manager.pop()

    def test_pause_overlay_push_pop(self):
        """Verifies PauseOverlay modal stacking, resume, and keyboard triggers."""
        manager = SceneManager()
        play_scene = PlayScene(manager)
        manager.switch(play_scene)

        self.assertIs(manager.current_scene, play_scene)

        # Push pause menu
        pause = PauseOverlay(manager)
        manager.push(pause)
        self.assertIs(manager.current_scene, pause)

        # Draw paused frame without error
        surface = pygame.Surface((LOGICAL_W, LOGICAL_H))
        pause.draw(surface)

        # Resume via ESC key
        esc_event = pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_ESCAPE})
        pause.handle_event(esc_event, Vector2(0, 0))

        # Successfully popped back to play scene
        self.assertIs(manager.current_scene, play_scene)

        manager.pop()

    def test_title_scene_difficulty_selection(self):
        """Verifies difficulty selector button and key shortcuts in TitleScene."""
        manager = SceneManager()
        title = TitleScene(manager)
        manager.switch(title)

        # Default is SAKTO
        self.assertEqual(title.selected_difficulty, DifficultyLevel.SAKTO)

        # Keyboard '1' -> MADALI
        title.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_1}), Vector2(0, 0))
        self.assertEqual(title.selected_difficulty, DifficultyLevel.MADALI)

        # Keyboard '4' -> PIKON
        title.handle_event(pygame.event.Event(pygame.KEYDOWN, {"key": pygame.K_4}), Vector2(0, 0))
        self.assertEqual(title.selected_difficulty, DifficultyLevel.PIKON)

        # Mouse click on Mahirap button
        mahirap_rect = title.diff_buttons[DifficultyLevel.MAHIRAP]
        click_pos = Vector2(mahirap_rect.centerx, mahirap_rect.centery)
        title.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1}), click_pos)
        self.assertEqual(title.selected_difficulty, DifficultyLevel.MAHIRAP)

        manager.pop()


if __name__ == "__main__":
    unittest.main()
