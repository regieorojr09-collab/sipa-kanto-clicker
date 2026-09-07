"""Visual effects module: particle bursts and procedural screen shake for Sipa: Kanto Clicker."""

import math
import random
from typing import List, Optional, Tuple
import pygame
from pygame.math import Vector2

from core.settings import (
    COLOR_SUNSHINE,
    COLOR_RETRO_CYAN,
    COLOR_RETRO_MAGENTA,
    COLOR_TASSEL_GOLD,
    COLOR_TASSEL_GREEN,
    COLOR_BRICK_RED,
)


class Particle:
    """Individual animated spark/star particle with gravity, drag, and alpha fading."""

    def __init__(
        self,
        pos: Vector2,
        vel: Vector2,
        color: Tuple[int, int, int],
        size: float = 5.0,
        lifetime: float = 0.5,
        is_star: bool = False,
    ) -> None:
        self.pos: Vector2 = Vector2(pos.x, pos.y)
        self.vel: Vector2 = Vector2(vel.x, vel.y)
        self.color: Tuple[int, int, int] = color
        self.size: float = size
        self.max_life: float = max(0.1, lifetime)
        self.life: float = self.max_life
        self.is_star: bool = is_star
        self.angle: float = random.uniform(0.0, 360.0)
        self.spin: float = random.uniform(-360.0, 360.0)

    @property
    def is_alive(self) -> bool:
        return self.life > 0.0

    def update(self, dt: float) -> None:
        if not self.is_alive:
            return

        self.life -= dt
        # Kinematics: gravity + slight air drag
        self.vel.y += 520.0 * dt
        self.vel.x *= (1.0 - (0.6 * dt))
        self.pos += self.vel * dt
        self.angle += self.spin * dt

    def draw(self, surface: pygame.Surface) -> None:
        if not self.is_alive:
            return

        life_factor = max(0.0, self.life / self.max_life)
        alpha = int(life_factor * 255)
        current_size = max(1.0, self.size * (0.3 + (0.7 * life_factor)))

        int_size = int(current_size * 2) + 4
        particle_surf = pygame.Surface((int_size, int_size), pygame.SRCALPHA)
        center = (int_size // 2, int_size // 2)

        if self.is_star:
            # Draw diamond star sparkle
            r = int(current_size)
            points = [
                (center[0], center[1] - r),
                (center[0] + (r * 0.4), center[1]),
                (center[0], center[1] + r),
                (center[0] - (r * 0.4), center[1]),
            ]
            pygame.draw.polygon(particle_surf, (*self.color, alpha), points)
        else:
            # Draw glowing spark circle
            pygame.draw.circle(
                particle_surf,
                (*self.color, alpha),
                center,
                int(current_size)
            )

        surface.blit(particle_surf, (self.pos.x - center[0], self.pos.y - center[1]))


class ParticleEmitter:
    """
    Manages active particle pool with capacity caps to safeguard 60 FPS in WebAssembly.
    """

    def __init__(self, max_particles: int = 160) -> None:
        self.max_particles: int = max_particles
        self.particles: List[Particle] = []

    def burst(
        self,
        pos: Vector2,
        count: int = 18,
        colors: Optional[List[Tuple[int, int, int]]] = None,
        speed_min: float = 100.0,
        speed_max: float = 340.0,
        lifetime: float = 0.55,
    ) -> None:
        """Spawns an explosive radial burst of star and spark particles at position."""
        if colors is None:
            colors = [
                COLOR_SUNSHINE,
                COLOR_RETRO_CYAN,
                COLOR_RETRO_MAGENTA,
                COLOR_TASSEL_GOLD,
                COLOR_TASSEL_GREEN,
            ]

        # Prevent pool bloat
        available_slots = self.max_particles - len(self.particles)
        spawn_count = min(count, max(0, available_slots))

        for _ in range(spawn_count):
            angle_rad = random.uniform(0.0, 2.0 * math.pi)
            speed = random.uniform(speed_min, speed_max)
            vel = Vector2(math.cos(angle_rad) * speed, math.sin(angle_rad) * speed)
            color = random.choice(colors)
            size = random.uniform(3.5, 6.5)
            is_star = random.random() > 0.4

            p = Particle(
                pos=pos,
                vel=vel,
                color=color,
                size=size,
                lifetime=lifetime * random.uniform(0.7, 1.2),
                is_star=is_star,
            )
            self.particles.append(p)

    def update(self, dt: float) -> None:
        """Advances active particles and prunes dead ones."""
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if p.is_alive]

    def draw(self, surface: pygame.Surface) -> None:
        """Renders all alive particles."""
        for p in self.particles:
            p.draw(surface)

    def clear(self) -> None:
        """Flushes all particles."""
        self.particles.clear()


class ScreenShake:
    """
    Non-linear trauma-based screen shake for impact feedback.
    Offset is calculated as trauma^2 for punchy, organic dissipation.
    """

    def __init__(self, max_offset: float = 16.0) -> None:
        self.max_offset: float = max_offset
        self.trauma: float = 0.0  # Normalized 0.0 to 1.0
        self.decay_rate: float = 2.4  # Trauma lost per second

    def add_trauma(self, amount: float) -> None:
        """Adds shake trauma clamped to 1.0."""
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, dt: float) -> None:
        """Decays trauma toward 0."""
        if self.trauma > 0.0:
            self.trauma = max(0.0, self.trauma - (self.decay_rate * dt))

    def get_offset(self) -> Vector2:
        """Returns the current camera pixel offset vector."""
        if self.trauma <= 0.001:
            return Vector2(0.0, 0.0)

        # Quadratic falloff for snappy feel
        shake_factor = self.trauma * self.trauma
        offset_x = (random.random() * 2.0 - 1.0) * self.max_offset * shake_factor
        offset_y = (random.random() * 2.0 - 1.0) * self.max_offset * shake_factor
        return Vector2(offset_x, offset_y)
