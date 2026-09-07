"""Headless integration test to verify Phase 1 foundation components."""

import os
import unittest
# Force dummy video driver for headless testing
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
from pygame.math import Vector2

from core.settings import LOGICAL_W, LOGICAL_H
from core.events import EventBus, GameEvent
from core.engine import Engine
from scenes.scene_manager import Scene, SceneManager
from scenes.title_scene import TitleScene
from scenes.play_scene import PlayScene


class DummyTestScene(Scene):
    def __init__(self, manager: SceneManager, name: str) -> None:
        super().__init__(manager)
        self.name = name
        self.entered = False
        self.exited = False

    def on_enter(self, **kwargs) -> None:
        self.entered = True
        self.exited = False

    def on_exit(self) -> None:
        self.exited = True

    def handle_event(self, event: pygame.event.Event, logical_mouse_pos: Vector2) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass


class TestPhase1Foundation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_event_bus(self):
        bus = EventBus()
        received = []

        def on_hit(**payload):
            received.append(payload)

        bus.subscribe(GameEvent.HIT_RESULT, on_hit)
        bus.publish(GameEvent.HIT_RESULT, judgment="Swak", points=300)

        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["judgment"], "Swak")
        self.assertEqual(received[0]["points"], 300)

        # Test unsubscribe
        bus.unsubscribe(GameEvent.HIT_RESULT, on_hit)
        bus.publish(GameEvent.HIT_RESULT, judgment="Puwede", points=100)
        self.assertEqual(len(received), 1)

    def test_engine_scaling_and_coordinate_mapping(self):
        engine = Engine(initial_window_size=(1280, 720))

        # 1:1 scale test
        self.assertAlmostEqual(engine.scale, 1.0)
        logical = engine.canvas_to_logical_pos((640, 360))
        self.assertAlmostEqual(logical.x, 640.0)
        self.assertAlmostEqual(logical.y, 360.0)

        # 2x scale (2560 x 1440)
        engine.recalculate_viewport(2560, 1440)
        self.assertAlmostEqual(engine.scale, 2.0)
        logical_2x = engine.canvas_to_logical_pos((1280, 720))
        self.assertAlmostEqual(logical_2x.x, 640.0)
        self.assertAlmostEqual(logical_2x.y, 360.0)

        # Pillarboxed (wider: e.g. 1920 x 720)
        engine.recalculate_viewport(1920, 720)
        self.assertAlmostEqual(engine.scale, 1.0)
        # In 1920x720, viewport is 1280 wide centered at x = (1920 - 1280)/2 = 320
        self.assertEqual(engine.viewport_rect.x, 320)
        self.assertEqual(engine.viewport_rect.y, 0)
        # Mouse clicked at physical 320 should map to logical x=0
        mapped_origin = engine.canvas_to_logical_pos((320, 0))
        self.assertAlmostEqual(mapped_origin.x, 0.0)
        self.assertAlmostEqual(mapped_origin.y, 0.0)

        # Letterboxed (taller: e.g. 1280 x 1000)
        engine.recalculate_viewport(1280, 1000)
        self.assertAlmostEqual(engine.scale, 1.0)
        # Viewport is 720 high centered at y = (1000 - 720)/2 = 140
        self.assertEqual(engine.viewport_rect.y, 140)
        mapped_top = engine.canvas_to_logical_pos((0, 140))
        self.assertAlmostEqual(mapped_top.y, 0.0)

    def test_scene_manager_lifecycle(self):
        manager = SceneManager()
        scene_a = DummyTestScene(manager, "A")
        scene_b = DummyTestScene(manager, "B")

        manager.switch(scene_a)
        self.assertIs(manager.current_scene, scene_a)
        self.assertTrue(scene_a.entered)

        # Push B
        manager.push(scene_b)
        self.assertIs(manager.current_scene, scene_b)
        self.assertTrue(scene_a.exited)
        self.assertTrue(scene_b.entered)

        # Pop B, returns to A
        popped = manager.pop()
        self.assertIs(popped, scene_b)
        self.assertIs(manager.current_scene, scene_a)
        self.assertTrue(scene_a.entered)

    def test_title_and_play_scenes(self):
        manager = SceneManager()
        title = TitleScene(manager)
        manager.switch(title)
        self.assertIsInstance(manager.current_scene, TitleScene)

        # Simulate update & draw without crashing
        surface = pygame.Surface((LOGICAL_W, LOGICAL_H))
        title.update(0.016)
        title.draw(surface)

        # Simulate clicking start button
        click_event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": title.button_rect.center})
        title.handle_event(click_event, Vector2(title.button_rect.centerx, title.button_rect.centery))

        # Should have transitioned to PlayScene
        self.assertIsInstance(manager.current_scene, PlayScene)
        play = manager.current_scene
        play.update(0.016)
        play.draw(surface)
        self.assertEqual(play.click_count, 0)

        # Click inside play scene
        play_click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"button": 1, "pos": (400, 300)})
        play.handle_event(play_click, Vector2(400, 300))
        self.assertEqual(play.click_count, 1)
        self.assertEqual(len(play.ripples), 1)


if __name__ == "__main__":
    unittest.main()
