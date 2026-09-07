"""Sipa projectile entity: kinematics, quadratic landing prediction, and procedural visuals."""

import math
from collections import deque
from typing import Deque, Tuple
import pygame
from pygame.math import Vector2

from core.settings import (
    GRAVITY,
    GROUND_Y,
    BOUND_MIN_X,
    BOUND_MAX_X,
    SIPA_RADIUS,
    COLOR_WASHER_GRAY,
    COLOR_WASHER_EDGE,
    COLOR_TASSEL_CYAN,
    COLOR_TASSEL_MAGENTA,
    COLOR_TASSEL_GOLD,
    COLOR_TASSEL_GREEN,
)


class Sipa:
    """
    The kicked projectile: a lead metal washer with colorful plastic tassels.
    Simulates 2D parabolic flight, wall boundaries, trajectory landing prediction,
    and a procedural decaying motion trail.
    """

    def __init__(self, x: float = 640.0, y: float = GROUND_Y) -> None:
        self.pos: Vector2 = Vector2(x, y)
        self.vel: Vector2 = Vector2(0.0, 0.0)
        self.spin: float = 0.0  # Rotations per second
        self.angle: float = 0.0  # Current rotation angle in degrees
        self.is_airborne: bool = False
        self.is_grounded: bool = True

        # Decaying motion trail: stores recent (Vector2 position, float angle)
        self.trail_points: Deque[Tuple[Vector2, float]] = deque(maxlen=15)

        # Pre-calculated tassel colors
        self._tassel_colors = [
            COLOR_TASSEL_CYAN,
            COLOR_TASSEL_MAGENTA,
            COLOR_TASSEL_GOLD,
            COLOR_TASSEL_GREEN,
        ]

    def launch(self, velocity: Vector2, spin: float = 2.0) -> None:
        """Launches or kicks the sipa with the specified initial velocity vector."""
        self.vel = Vector2(velocity.x, velocity.y)
        self.spin = spin
        self.is_airborne = True
        self.is_grounded = False
        self.trail_points.clear()

    def reset(self, x: float = 640.0, y: float = GROUND_Y) -> None:
        """Resets the sipa to a stationary position on the ground."""
        self.pos = Vector2(x, y)
        self.vel = Vector2(0.0, 0.0)
        self.spin = 0.0
        self.angle = 0.0
        self.is_airborne = False
        self.is_grounded = True
        self.trail_points.clear()

    def predict_landing(self, target_y: float) -> Tuple[float, float, float]:
        """
        Solves the quadratic equation to determine (predicted_x, target_y, arrival_time_ms)
        when the falling sipa will cross the specified kicking height target_y.
        
        Analytical formula:
            y(t) = y_0 + v_{y0} * t + 0.5 * g * t^2 = target_y
            0.5 * g * t^2 + v_{y0} * t + (y_0 - target_y) = 0
        """
        a = 0.5 * GRAVITY
        b = self.vel.y
        c = self.pos.y - target_y

        discriminant = (b * b) - (4.0 * a * c)

        if discriminant < 0.0 or a <= 0.0:
            # Trajectory apex does not reach or cannot calculate target_y
            return (self.pos.x, target_y, 0.0)

        # The positive root corresponds to the descending phase (falling downward)
        t_arrive_sec = (-b + math.sqrt(discriminant)) / (2.0 * a)

        if t_arrive_sec <= 0.0:
            return (self.pos.x, target_y, 0.0)

        # Calculate predicted X taking into account wall bounces within [BOUND_MIN_X, BOUND_MAX_X]
        curr_x = self.pos.x
        curr_vx = self.vel.x
        remaining_t = t_arrive_sec

        while remaining_t > 0.0:
            if curr_vx > 0.0:
                time_to_wall = (BOUND_MAX_X - curr_x) / curr_vx
                if time_to_wall < remaining_t:
                    curr_x = BOUND_MAX_X
                    curr_vx = -curr_vx * 0.75  # Dampen bounce
                    remaining_t -= time_to_wall
                else:
                    curr_x += curr_vx * remaining_t
                    break
            elif curr_vx < 0.0:
                time_to_wall = (curr_x - BOUND_MIN_X) / (-curr_vx)
                if time_to_wall < remaining_t:
                    curr_x = BOUND_MIN_X
                    curr_vx = -curr_vx * 0.75  # Dampen bounce
                    remaining_t -= time_to_wall
                else:
                    curr_x += curr_vx * remaining_t
                    break
            else:
                break

        arrival_time_ms = t_arrive_sec * 1000.0
        return (curr_x, target_y, arrival_time_ms)

    def update(self, dt: float) -> None:
        """Integrates velocity and gravity, performs boundary collisions, and advances trail."""
        if not self.is_airborne:
            return

        # Record trail position
        self.trail_points.append((Vector2(self.pos.x, self.pos.y), self.angle))

        # Kinematic integration
        self.vel.y += GRAVITY * dt
        self.pos.x += self.vel.x * dt
        self.pos.y += self.vel.y * dt

        # Wall horizontal bounds with bounce dampening
        if self.pos.x <= BOUND_MIN_X:
            self.pos.x = BOUND_MIN_X
            if self.vel.x < 0.0:
                self.vel.x = -self.vel.x * 0.75
                self.spin = -self.spin * 0.8
        elif self.pos.x >= BOUND_MAX_X:
            self.pos.x = BOUND_MAX_X
            if self.vel.x > 0.0:
                self.vel.x = -self.vel.x * 0.75
                self.spin = -self.spin * 0.8

        # Ground collision at GROUND_Y
        if self.pos.y >= GROUND_Y:
            self.pos.y = GROUND_Y
            if self.vel.y > 0.0:
                # Bounce on pavement
                self.vel.y = -self.vel.y * 0.35
                self.vel.x *= 0.75
                self.spin *= 0.6
                if abs(self.vel.y) < 65.0:
                    self.vel.y = 0.0
                    self.vel.x = 0.0
                    self.spin = 0.0
                    self.is_airborne = False
                    self.is_grounded = True

        # Rotate sipa
        self.angle = (self.angle + (self.spin * dt * 360.0)) % 360.0

    def draw(self, surface: pygame.Surface) -> None:
        """Draws the decaying motion trail, colorful plastic tassels, and lead washer."""
        # 1. Motion Trail
        trail_len = len(self.trail_points)
        for i, (t_pos, t_angle) in enumerate(self.trail_points):
            factor = (i + 1) / (trail_len + 1)
            radius = max(2, int(SIPA_RADIUS * factor * 0.7))
            alpha = int(140 * factor)
            trail_surf = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
            color = self._tassel_colors[i % len(self._tassel_colors)]
            pygame.draw.circle(
                trail_surf,
                (*color, alpha),
                (radius + 1, radius + 1),
                radius
            )
            surface.blit(trail_surf, (t_pos.x - radius - 1, t_pos.y - radius - 1))

        # 2. Plastic Tassels
        cx, cy = int(self.pos.x), int(self.pos.y)
        num_tassels = 6
        tassel_length = 26.0

        for i in range(num_tassels):
            base_angle_deg = self.angle + (i * (360.0 / num_tassels))
            # Fan out backward relative to velocity if airborne
            if self.is_airborne and self.vel.length_squared() > 100.0:
                flight_angle = math.degrees(math.atan2(-self.vel.y, -self.vel.x))
                tassel_deg = (flight_angle + ((i - (num_tassels / 2)) * 14.0))
            else:
                tassel_deg = base_angle_deg

            rad = math.radians(tassel_deg)
            tx = cx + (math.cos(rad) * tassel_length)
            ty = cy + (math.sin(rad) * tassel_length)

            tassel_color = self._tassel_colors[i % len(self._tassel_colors)]
            pygame.draw.line(surface, tassel_color, (cx, cy), (int(tx), int(ty)), 3)

        # 3. Lead Washer (Metal ring with inner hole)
        washer_r = int(SIPA_RADIUS)
        inner_hole_r = int(washer_r * 0.45)

        # Outer rim
        pygame.draw.circle(surface, COLOR_WASHER_EDGE, (cx, cy), washer_r)
        # Metallic face
        pygame.draw.circle(surface, COLOR_WASHER_GRAY, (cx, cy), washer_r - 2)
        # Inner lead core hole
        pygame.draw.circle(surface, COLOR_WASHER_EDGE, (cx, cy), inner_hole_r + 1)
        pygame.draw.circle(surface, (20, 22, 28), (cx, cy), inner_hole_r)

        # Metallic highlight glint
        glint_x = cx - int(washer_r * 0.35)
        glint_y = cy - int(washer_r * 0.35)
        pygame.draw.circle(surface, (250, 252, 255), (glint_x, glint_y), 2)
