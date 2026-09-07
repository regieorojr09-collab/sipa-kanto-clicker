"""Automated headless test suite for Phase 3: Avatar FSM, Taya AI, Audio, and VFX."""

import os
import unittest

# Force dummy video driver for headless testing
os.environ["SDL_VIDEODRIVER"] = "dummy"

import pygame
from pygame.math import Vector2

from core.events import GameEvent, event_bus
from core.settings import LOGICAL_W, LOGICAL_H, GROUND_Y
from entities.avatar import Avatar, AvatarState
from entities.taya import Taya, TayaState
from systems.audio import AudioManager
from ui.fx import ParticleEmitter, ScreenShake
from scenes.scene_manager import SceneManager
from scenes.play_scene import PlayScene


class TestPhase3(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()
        pygame.font.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        event_bus.clear()

    def test_avatar_fsm_priority_gating(self):
        """Verifies priority gating: Miss Stumble interrupts kicks; kicks cannot interrupt kicks."""
        avatar = Avatar(x=460.0, y=GROUND_Y)
        self.assertEqual(avatar.current_state, AvatarState.IDLE)

        # 1. Idle -> Paa Kick (Priority 3 > 0)
        accepted = avatar.request_state(AvatarState.PAA_KICK, current_time_sec=1.0)
        self.assertTrue(accepted)
        self.assertEqual(avatar.current_state, AvatarState.PAA_KICK)
        self.assertTrue(avatar.is_locked)

        # 2. Paa Kick -> Tuhod Kick (Priority 3 == 3, locked): should buffer, not interrupt
        accepted2 = avatar.request_state(AvatarState.TUHOD_KICK, current_time_sec=1.05)
        self.assertFalse(accepted2)
        self.assertEqual(avatar.current_state, AvatarState.PAA_KICK)
        self.assertEqual(avatar.buffered_state, AvatarState.TUHOD_KICK)

        # 3. Paa Kick -> Miss Stumble (Priority 4 > 3): MUST interrupt immediately!
        accepted3 = avatar.request_state(AvatarState.MISS_STUMBLE, current_time_sec=1.10)
        self.assertTrue(accepted3)
        self.assertEqual(avatar.current_state, AvatarState.MISS_STUMBLE)
        # Buffer must be cleared on stumble
        self.assertIsNone(avatar.buffered_state)

        avatar.destroy()

    def test_avatar_input_buffering(self):
        """Verifies 200 ms input buffer execution and expiration."""
        avatar = Avatar(x=460.0, y=GROUND_Y)

        # Start Paa Kick at t = 1.0s
        avatar.request_state(AvatarState.PAA_KICK, current_time_sec=1.0)

        # Buffer Tuhod Kick at t = 1.15s (within 200ms window)
        avatar.request_state(AvatarState.TUHOD_KICK, current_time_sec=1.15)
        self.assertEqual(avatar.buffered_state, AvatarState.TUHOD_KICK)

        # Advance frames through all 6 Paa Kick frames (6 * 50ms = 300ms total)
        # Complete Paa Kick at t = 1.30s (1.30 - 1.15 = 0.15s <= 0.20s)
        for _ in range(7):
            avatar.update(0.055, current_time_sec=1.30)

        # Buffered Tuhod Kick should now have executed!
        self.assertEqual(avatar.current_state, AvatarState.TUHOD_KICK)
        self.assertIsNone(avatar.buffered_state)

        # Now test buffer expiry: buffer a kick, but finish after 250ms (> 200ms)
        avatar.request_state(AvatarState.SIKO_KICK, current_time_sec=1.35)
        # Advance 5 frames (5 * 56ms = 280ms) with current_time = 1.65s (1.65 - 1.35 = 0.30s > 0.20s)
        for _ in range(5):
            avatar.update(0.056, current_time_sec=1.65)

        # Expired buffer discarded; state transitions to HIT_RECOVER
        self.assertEqual(avatar.current_state, AvatarState.HIT_RECOVER)

        # Further advance through 3 recovery frames (3 * 40ms = 120ms) -> returns to IDLE
        for _ in range(3):
            avatar.update(0.045, current_time_sec=1.80)
        self.assertEqual(avatar.current_state, AvatarState.IDLE)

        avatar.destroy()

    def test_taya_state_reactions(self):
        """Verifies Taya reactions to miss events, combo milestones, and timed reset to OBSERVING."""
        taya = Taya(x=130.0, y=GROUND_Y)
        self.assertEqual(taya.current_state, TayaState.OBSERVING)

        # 1. Player miss triggers Taunting
        event_bus.publish(GameEvent.HIT_RESULT, judgment="Bagsak!", was_miss=True)
        self.assertEqual(taya.current_state, TayaState.TAUNTING)
        self.assertIsNotNone(taya.callout_text)

        # 2. Advance time past duration -> returns to OBSERVING
        taya.update(2.0)
        self.assertEqual(taya.current_state, TayaState.OBSERVING)

        # 3. Combo milestone 10 -> Impressed
        event_bus.publish(GameEvent.COMBO_MILESTONE, combo_count=10)
        self.assertEqual(taya.current_state, TayaState.IMPRESSED)

        # 4. Combo milestone 25 -> Pikon Rage
        event_bus.publish(GameEvent.COMBO_MILESTONE, combo_count=25)
        self.assertEqual(taya.current_state, TayaState.PIKON_RAGE)

        taya.destroy()

    def test_particle_emitter_and_screen_shake(self):
        """Verifies particle capacity caps, lifespan decay, and screen shake trauma math."""
        # 1. Particle pooling cap
        emitter = ParticleEmitter(max_particles=40)
        emitter.burst(Vector2(640, 360), count=60)
        self.assertLessEqual(len(emitter.particles), 40)

        # 2. Lifespan decay
        emitter.update(1.0)
        self.assertEqual(len(emitter.particles), 0)

        # 3. Screen shake trauma
        shake = ScreenShake(max_offset=16.0)
        self.assertEqual(shake.get_offset(), Vector2(0, 0))

        shake.add_trauma(0.8)
        self.assertAlmostEqual(shake.trauma, 0.8)
        offset = shake.get_offset()
        self.assertGreater(offset.length_squared(), 0.0)

        # Trauma decay
        shake.update(0.4)
        self.assertLess(shake.trauma, 0.8)

    def test_audio_manager_headless_safety(self):
        """Verifies that AudioManager handles play and unlock calls without exceptions."""
        audio = AudioManager()
        audio.unlock_audio()
        audio.play_kick("Swak!")
        audio.play_kick("Puwede")
        audio.play_kick("Daplis")
        audio.play_miss()
        audio.play_cheer()
        audio.destroy()

    def test_play_scene_full_phase3_pipeline(self):
        """Verifies PlayScene execution with Avatar, Taya, ScreenShake, Audio, and Particle rendering."""
        manager = SceneManager()
        scene = PlayScene(manager)
        manager.switch(scene)

        surface = pygame.Surface((LOGICAL_W, LOGICAL_H))

        # Serve
        scene.serve_sipa()
        self.assertTrue(scene.sipa.is_airborne)

        # Step 60 frames
        for _ in range(60):
            scene.update(0.016)

        # Draw frame
        scene.draw(surface)

        # Simulate hit event triggering avatar kick & particles
        event_bus.publish(GameEvent.HIT_RESULT, judgment="Swak!", points=300, position=(600, 520), was_miss=False)
        self.assertEqual(scene.avatar.current_state, AvatarState.PAA_KICK)
        self.assertGreater(len(scene.particle_emitter.particles), 0)

        manager.pop()


if __name__ == "__main__":
    unittest.main()
