"""Browser-safe procedural audio system and chiptune sound generator for Sipa: Kanto Clicker."""

import array
import math
import logging
from typing import Dict, Optional
import pygame

from core.events import GameEvent, event_bus

logger = logging.getLogger(__name__)


def _generate_pcm_sound(samples: list[int], sample_rate: int = 44100) -> Optional[pygame.mixer.Sound]:
    """Wraps raw 16-bit PCM integer samples into a pygame.mixer.Sound instance."""
    try:
        data = array.array("h", [max(-32767, min(32767, int(s))) for s in samples])
        return pygame.mixer.Sound(buffer=data)
    except Exception as exc:
        logger.debug("Failed to create procedural sound: %s", exc)
        return None


class AudioManager:
    """
    Manages sound synthesis and audio playback.
    Pre-synthesizes procedural retro SFX into memory and unlocks browser AudioContext on first click.
    Fails completely silently in headless / missing audio environments.
    """

    def __init__(self) -> None:
        self.is_unlocked: bool = False
        self.is_available: bool = False
        self.sounds: Dict[str, pygame.mixer.Sound] = {}

        self._init_mixer()
        if self.is_available:
            self._synthesize_sfx()

        # Subscribe to browser interaction unlock event
        event_bus.subscribe(GameEvent.AUDIO_UNLOCK, self.unlock_audio)

    def _init_mixer(self) -> None:
        """Initializes the Pygame audio mixer with low latency buffer size (512 samples)."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            self.is_available = True
        except Exception as exc:
            logger.debug("Audio device unavailable: %s", exc)
            self.is_available = False

    def _synthesize_sfx(self) -> None:
        """Procedurally generates chiptune/metallic arcade sound effects in pure Python."""
        sample_rate = 44100

        # 1. Metallic Washer Clink (Rapid frequency drop with exponential decay)
        duration = 0.09
        num_samples = int(sample_rate * duration)
        clink_samples = []
        for i in range(num_samples):
            t = i / sample_rate
            # 1400Hz dropping to 700Hz
            freq = 1400.0 - (700.0 * (t / duration))
            decay = math.exp(-35.0 * t)
            wave = (0.7 * math.sin(2.0 * math.pi * freq * t)) + (0.3 * math.sin(2.0 * math.pi * freq * 2.4 * t))
            clink_samples.append(int(wave * decay * 28000))

        snd = _generate_pcm_sound(clink_samples, sample_rate)
        if snd:
            self.sounds["clink"] = snd

        # 2. Shoe Thud (Low-end body thump)
        duration = 0.11
        num_samples = int(sample_rate * duration)
        thud_samples = []
        for i in range(num_samples):
            t = i / sample_rate
            freq = 180.0 - (120.0 * (t / duration))
            decay = math.exp(-25.0 * t)
            wave = math.sin(2.0 * math.pi * freq * t)
            thud_samples.append(int(wave * decay * 26000))

        snd = _generate_pcm_sound(thud_samples, sample_rate)
        if snd:
            self.sounds["thud"] = snd

        # 3. Miss Stumble Buzz (Low square/sawtooth dissonance)
        duration = 0.22
        num_samples = int(sample_rate * duration)
        buzz_samples = []
        for i in range(num_samples):
            t = i / sample_rate
            freq = 110.0 - (30.0 * (t / duration))
            decay = math.exp(-12.0 * t)
            # Square wave approximation
            phase = (t * freq) % 1.0
            wave = 0.8 if phase < 0.5 else -0.8
            buzz_samples.append(int(wave * decay * 20000))

        snd = _generate_pcm_sound(buzz_samples, sample_rate)
        if snd:
            self.sounds["miss"] = snd

        # 4. Combo Cheer / Chime (Arpeggiated chime)
        duration = 0.25
        num_samples = int(sample_rate * duration)
        cheer_samples = []
        notes = [523.25, 659.25, 783.99, 1046.50]  # C5, E5, G5, C6 arpeggio
        note_dur = duration / len(notes)
        for i in range(num_samples):
            t = i / sample_rate
            note_idx = min(len(notes) - 1, int(t / note_dur))
            freq = notes[note_idx]
            sub_t = t - (note_idx * note_dur)
            decay = math.exp(-18.0 * sub_t)
            wave = math.sin(2.0 * math.pi * freq * t)
            cheer_samples.append(int(wave * decay * 22000))

        snd = _generate_pcm_sound(cheer_samples, sample_rate)
        if snd:
            self.sounds["cheer"] = snd

    def unlock_audio(self, **kwargs) -> None:
        """Called upon first user interaction to warm up browser AudioContext."""
        if self.is_unlocked:
            return
        self.is_unlocked = True
        if self.is_available and "clink" in self.sounds:
            try:
                self.sounds["clink"].set_volume(0.3)
                self.sounds["clink"].play()
            except Exception:
                pass

    def play_kick(self, judgment: str = "Swak!") -> None:
        """Plays metallic impact sounds tailored to judgment accuracy."""
        if not self.is_available or not self.is_unlocked:
            return

        try:
            if judgment == "Swak!":
                if "clink" in self.sounds:
                    self.sounds["clink"].set_volume(1.0)
                    self.sounds["clink"].play()
                if "thud" in self.sounds:
                    self.sounds["thud"].set_volume(0.85)
                    self.sounds["thud"].play()
            elif judgment == "Puwede":
                if "clink" in self.sounds:
                    self.sounds["clink"].set_volume(0.7)
                    self.sounds["clink"].play()
                if "thud" in self.sounds:
                    self.sounds["thud"].set_volume(0.7)
                    self.sounds["thud"].play()
            else:  # Daplis
                if "thud" in self.sounds:
                    self.sounds["thud"].set_volume(0.6)
                    self.sounds["thud"].play()
        except Exception:
            pass

    def play_miss(self) -> None:
        """Plays stumble/miss feedback sound."""
        if not self.is_available or not self.is_unlocked:
            return
        try:
            if "miss" in self.sounds:
                self.sounds["miss"].set_volume(0.9)
                self.sounds["miss"].play()
        except Exception:
            pass

    def play_cheer(self) -> None:
        """Plays combo milestone fanfare chime."""
        if not self.is_available or not self.is_unlocked:
            return
        try:
            if "cheer" in self.sounds:
                self.sounds["cheer"].set_volume(0.8)
                self.sounds["cheer"].play()
        except Exception:
            pass

    def destroy(self) -> None:
        """Unsubscribes from event bus."""
        event_bus.unsubscribe(GameEvent.AUDIO_UNLOCK, self.unlock_audio)
