"""Browser-safe procedural audio system, chiptune sound generator, and BGM synthesizer for Sipa: Kanto Clicker."""

import array
import math
import random
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


def _synthesize_bgm_track(tempo_bpm: float = 120.0, is_rage: bool = False, sample_rate: int = 44100) -> Optional[pygame.mixer.Sound]:
    """
    Synthesizes a looping syncopated chiptune track in pure Python.
    Features a bassline, acoustic-style plucked arpeggio, and rhythmic percussion.
    """
    total_beats = 8.0  # 2 bars of 4/4
    duration = total_beats * (60.0 / tempo_bpm)
    num_samples = int(sample_rate * duration)
    step_duration = duration / 32.0  # 32 sixteenth-note steps

    # Bass note frequencies (Hz) for 32 steps (0 = rest)
    bass_steps = [
        110.0, 0, 0, 110.0,  0, 0, 130.8, 0,
        146.8, 0, 0, 164.8,  0, 0, 98.0,  0,
        110.0, 0, 0, 110.0,  0, 0, 130.8, 0,
        164.8, 0, 0, 146.8,  0, 0, 82.4,  0,
    ]

    # Plucked arpeggio frequencies (Hz) for 32 steps
    pluck_steps = [
        440.0, 0, 523.2, 0,  659.2, 0, 440.0, 0,
        587.3, 0, 659.2, 0,  523.2, 0, 392.0, 0,
        440.0, 0, 523.2, 0,  659.2, 0, 783.9, 0,
        659.2, 0, 587.3, 0,  523.2, 0, 493.8, 0,
    ]

    samples: list[int] = []
    # Seed pseudo-random generator deterministically for percussion texture
    rng = random.Random(42 if not is_rage else 99)

    for i in range(num_samples):
        t = i / sample_rate
        step_idx = min(31, int(t / step_duration))
        sub_t = t - (step_idx * step_duration)

        # 1. Bassline (Punchy Triangle wave with sub-bass)
        bass_val = 0.0
        bass_freq = bass_steps[step_idx]
        if bass_freq > 0.0:
            decay = math.exp(-12.0 * sub_t) if not is_rage else math.exp(-15.0 * sub_t)
            phase = (t * bass_freq) % 1.0
            triangle = 4.0 * abs(phase - 0.5) - 1.0
            sub_sine = math.sin(2.0 * math.pi * (bass_freq * 0.5) * t)
            bass_val = (triangle * 0.75 + sub_sine * 0.25) * decay

        # 2. Plucked Acoustic/Chiptune Arpeggio (Harmonic Sine)
        pluck_val = 0.0
        pluck_freq = pluck_steps[step_idx]
        if pluck_freq > 0.0:
            decay_pluck = math.exp(-16.0 * sub_t)
            fund = math.sin(2.0 * math.pi * pluck_freq * t)
            second = 0.35 * math.sin(2.0 * math.pi * (pluck_freq * 2.0) * t)
            pluck_val = (fund + second) * decay_pluck

        # 3. Light Percussive Tap (Hi-hat click on sixteenth notes)
        perc_val = 0.0
        if step_idx % 2 == 0:
            decay_perc = math.exp(-75.0 * sub_t)
            noise = rng.uniform(-1.0, 1.0)
            perc_val = noise * decay_perc * (0.28 if not is_rage else 0.45)

        # Mix channels
        mix = (bass_val * 0.52) + (pluck_val * 0.34) + (perc_val * 0.14)
        amp = 24000 if not is_rage else 27000
        samples.append(int(mix * amp))

    return _generate_pcm_sound(samples, sample_rate)


class AudioManager:
    """
    Manages sound synthesis and audio playback.
    Pre-synthesizes procedural retro SFX and looping BGM into memory.
    Safely unlocks browser AudioContext on first click.
    Fails completely silently in headless / missing audio environments.
    """

    def __init__(self) -> None:
        self.is_unlocked: bool = False
        self.is_available: bool = False
        self.sounds: Dict[str, pygame.mixer.Sound] = {}

        # BGM state
        self.bgm_normal: Optional[pygame.mixer.Sound] = None
        self.bgm_rage: Optional[pygame.mixer.Sound] = None
        self.bgm_channel: Optional[pygame.mixer.Channel] = None
        self.is_bgm_playing: bool = False
        self.is_rage_bgm: bool = False
        self._bgm_requested: bool = False
        self._bgm_paused: bool = False

        self._init_mixer()
        if self.is_available:
            self._synthesize_sfx()
            self._synthesize_bgm()

        # Subscribe to browser interaction unlock event
        event_bus.subscribe(GameEvent.AUDIO_UNLOCK, self.unlock_audio)

    def _init_mixer(self) -> None:
        """Initializes the Pygame audio mixer with low latency buffer size (512 samples)."""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=512)
            self.is_available = True
            # Reserve dedicated channel 0 for BGM
            try:
                pygame.mixer.set_num_channels(8)
                self.bgm_channel = pygame.mixer.Channel(0)
            except Exception:
                self.bgm_channel = None
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

        # 5. Ambient Crowd Cheer / Spectator Roar & Whistle (Combo milestone 10 / 20)
        duration_crowd = 0.48
        num_samples_crowd = int(sample_rate * duration_crowd)
        crowd_samples = []
        rng = random.Random(77)
        for i in range(num_samples_crowd):
            t = i / sample_rate
            # Rising excited whistle (1600 Hz -> 2400 Hz)
            whistle_freq = 1600.0 + (800.0 * (t / duration_crowd))
            whistle_wave = math.sin(2.0 * math.pi * whistle_freq * t) * math.exp(-6.0 * t)

            # Clapping crowd roar simulation (modulated noise)
            clap_pulse = math.sin(2.0 * math.pi * 14.0 * t)  # Rhythmic burst
            noise = rng.uniform(-0.8, 0.8) * (0.6 + 0.4 * clap_pulse) * math.exp(-4.5 * t)

            sample_val = (whistle_wave * 0.4) + (noise * 0.6)
            crowd_samples.append(int(sample_val * 24000))

        snd = _generate_pcm_sound(crowd_samples, sample_rate)
        if snd:
            self.sounds["crowd_cheer"] = snd

    def _synthesize_bgm(self) -> None:
        """Pre-synthesizes normal and high-rage tempo BGM tracks."""
        self.bgm_normal = _synthesize_bgm_track(tempo_bpm=120.0, is_rage=False)
        self.bgm_rage = _synthesize_bgm_track(tempo_bpm=152.0, is_rage=True)

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

        if self._bgm_requested:
            self.start_bgm()

    def start_bgm(self) -> None:
        """Starts looping background music on dedicated channel."""
        self._bgm_requested = True
        if not self.is_available or not self.is_unlocked:
            return

        track = self.bgm_rage if self.is_rage_bgm else self.bgm_normal
        if track:
            try:
                if self.bgm_channel:
                    self.bgm_channel.set_volume(0.45)
                    self.bgm_channel.play(track, loops=-1)
                else:
                    track.set_volume(0.45)
                    track.play(loops=-1)
                self.is_bgm_playing = True
                self._bgm_paused = False
            except Exception:
                pass

    def pause_bgm(self) -> None:
        """Pauses BGM during modal dialogs / PauseOverlay."""
        self._bgm_paused = True
        if not self.is_available:
            return
        try:
            if self.bgm_channel and self.bgm_channel.get_busy():
                self.bgm_channel.pause()
            elif self.bgm_normal:
                self.bgm_normal.stop()
                if self.bgm_rage:
                    self.bgm_rage.stop()
        except Exception:
            pass

    def resume_bgm(self) -> None:
        """Resumes paused BGM."""
        was_paused = self._bgm_paused
        self._bgm_paused = False
        if not self.is_available or not self.is_unlocked:
            return
        try:
            if was_paused and self.bgm_channel:
                self.bgm_channel.unpause()
            elif self._bgm_requested:
                self.start_bgm()
        except Exception:
            pass

    def stop_bgm(self) -> None:
        """Stops background music playback."""
        self._bgm_requested = False
        self.is_bgm_playing = False
        self._bgm_paused = False
        if not self.is_available:
            return
        try:
            if self.bgm_channel:
                self.bgm_channel.stop()
            if self.bgm_normal:
                self.bgm_normal.stop()
            if self.bgm_rage:
                self.bgm_rage.stop()
        except Exception:
            pass

    def update_bgm(self, pikon_meter: float) -> None:
        """
        Dynamically scales BGM tempo when Taya's Pikon Meter enters rage mode (>= 80%).
        Switches between normal (120 BPM) and high-octane rage (152 BPM) tracks.
        """
        is_rage = pikon_meter >= 80.0
        if is_rage != self.is_rage_bgm:
            self.is_rage_bgm = is_rage
            if self.is_bgm_playing and not self._bgm_paused:
                self.start_bgm()

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

    def play_crowd_cheer(self, combo: int = 10) -> None:
        """Plays crowd applause/cheer sound for milestone combos."""
        if not self.is_available or not self.is_unlocked:
            return
        try:
            if "crowd_cheer" in self.sounds:
                vol = 0.75 if combo < 20 else 0.95
                self.sounds["crowd_cheer"].set_volume(vol)
                self.sounds["crowd_cheer"].play()
            elif "cheer" in self.sounds:
                self.sounds["cheer"].set_volume(0.85)
                self.sounds["cheer"].play()
        except Exception:
            pass

    def destroy(self) -> None:
        """Stops audio and unsubscribes from event bus."""
        self.stop_bgm()
        event_bus.unsubscribe(GameEvent.AUDIO_UNLOCK, self.unlock_audio)

