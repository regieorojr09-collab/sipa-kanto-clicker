"""Procedural street scenery and parallax background renderer for Sipa: Kanto Clicker.

Generates a stylized Filipino streetscape (eskinita) featuring:
- Dynamic dusk sky gradient that shifts to intense amber/orange during Taya rage (Pikon >= 80%)
- Drifting procedural clouds with wrapping motion
- Distant rooftop silhouettes and Meralco utility poles with sagging electrical wires
- Mid-ground stylized Sari-Sari Store with corrugated tin roof, hanging snack packets (chichirya), and signboard
- Mid-ground parked Philippine tricycle silhouette
- Foreground cracked asphalt street with chalk boundaries (guhit ng kanto) at GROUND_Y = 610
"""

import math
import random
from typing import List, Optional, Tuple
import pygame
from pygame.math import Vector2

from core.settings import (
    LOGICAL_W,
    LOGICAL_H,
    LOGICAL_CENTER_X,
    GROUND_Y,
    COLOR_ASPHALT,
    COLOR_CHALK,
    COLOR_SUNSHINE,
    COLOR_BRICK_RED,
    COLOR_TASSEL_GOLD,
    COLOR_TASSEL_GREEN,
    COLOR_RETRO_CYAN,
)


class ProceduralCloud:
    """Drifting procedural cloud composed of layered soft pill/circle shapes."""

    def __init__(self, x: float, y: float, width: float, height: float, speed: float, alpha: int = 70) -> None:
        self.x: float = x
        self.y: float = y
        self.width: float = width
        self.height: float = height
        self.speed: float = speed
        self.alpha: int = alpha
        self._surface: Optional[pygame.Surface] = None
        self._generate_surface()

    def _generate_surface(self) -> None:
        """Draws soft fluffy cloud puff circles onto a dedicated transparent surface."""
        w, h = int(self.width), int(self.height)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        color = (230, 235, 250, self.alpha)

        # Puff cluster
        num_puffs = 5
        for i in range(num_puffs):
            px = int((w * 0.2) + (i * (w * 0.6 / (num_puffs - 1))))
            py = int(h * 0.55 - (math.sin(i / (num_puffs - 1) * math.pi) * (h * 0.25)))
            radius = int(h * 0.38)
            pygame.draw.circle(surf, color, (px, py), radius)

        # Flat cloud base
        base_rect = pygame.Rect(int(w * 0.15), int(h * 0.45), int(w * 0.7), int(h * 0.35))
        pygame.draw.rect(surf, color, base_rect, border_radius=int(h * 0.15))

        self._surface = surf

    def update(self, dt: float) -> None:
        """Drifts cloud horizontally and wraps seamlessly when exiting the viewport."""
        self.x += self.speed * dt
        if self.x > LOGICAL_W + 80:
            self.x = -self.width - 60
            self.y = random.uniform(30.0, 210.0)

    def draw(self, surface: pygame.Surface, offset: Vector2 = Vector2(0, 0)) -> None:
        if self._surface:
            surface.blit(self._surface, (self.x + (offset.x * 0.25), self.y + (offset.y * 0.25)))


class StreetScenery:
    """
    Procedural Filipino street environment renderer.
    Provides complete zero-asset background layers with dynamic Pikon rage lighting.
    """

    def __init__(self) -> None:
        self.pikon_meter: float = 0.0
        self.time_elapsed: float = 0.0

        # Cached procedural surfaces
        self.sky_surface: pygame.Surface = pygame.Surface((LOGICAL_W, int(GROUND_Y) + 20))
        self.city_silhouette: pygame.Surface = pygame.Surface((LOGICAL_W, int(GROUND_Y)), pygame.SRCALPHA)
        self.sari_sari_surface: pygame.Surface = pygame.Surface((400, 260), pygame.SRCALPHA)
        self.tricycle_surface: pygame.Surface = pygame.Surface((220, 160), pygame.SRCALPHA)
        self.asphalt_surface: pygame.Surface = pygame.Surface((LOGICAL_W, LOGICAL_H - int(GROUND_Y) + 50))

        # Fonts
        self.font_sign: Optional[pygame.font.Font] = None

        # Clouds
        self.clouds: List[ProceduralCloud] = [
            ProceduralCloud(x=60.0, y=45.0, width=160.0, height=52.0, speed=14.0, alpha=65),
            ProceduralCloud(x=340.0, y=110.0, width=220.0, height=68.0, speed=20.0, alpha=80),
            ProceduralCloud(x=680.0, y=60.0, width=190.0, height=58.0, speed=16.0, alpha=70),
            ProceduralCloud(x=950.0, y=130.0, width=240.0, height=72.0, speed=22.0, alpha=85),
            ProceduralCloud(x=-120.0, y=85.0, width=180.0, height=55.0, speed=18.0, alpha=60),
        ]

        # Procedural Asphalt Cracks
        self.cracks: List[List[Tuple[int, int]]] = [
            [(160, 630), (185, 642), (210, 640), (228, 655)],
            [(420, 625), (445, 638), (475, 635), (490, 648), (510, 645)],
            [(740, 632), (765, 645), (785, 640), (815, 658)],
            [(1020, 628), (1048, 640), (1072, 636), (1100, 652)],
        ]

        # Initialize surfaces
        self._init_static_layers()

    def _init_fonts(self) -> None:
        if self.font_sign is None:
            self.font_sign = pygame.font.Font(None, 20)

    def _init_static_layers(self) -> None:
        """Pre-renders static procedural visual components."""
        self._init_fonts()
        self._render_distant_silhouette()
        self._render_sari_sari_store()
        self._render_tricycle()
        self._render_asphalt()
        self._update_sky_gradient(0.0)

    def _update_sky_gradient(self, rage_factor: float) -> None:
        """
        Renders sky gradient vertically.
        Shifts from deep twilight navy/blue to intense sunset amber/orange when rage_factor > 0.
        """
        h = self.sky_surface.get_height()

        # Base dusk sky colors
        base_top = (16, 20, 36)
        base_mid = (28, 38, 60)
        base_bottom = (44, 58, 86)

        # High Pikon rage sky colors (warm amber / sunset fire)
        rage_top = (48, 20, 30)
        rage_mid = (110, 42, 28)
        rage_bottom = (160, 65, 30)

        # Lerp current colors based on rage_factor (0.0 to 1.0)
        cur_top = tuple(int(base_top[i] + (rage_top[i] - base_top[i]) * rage_factor) for i in range(3))
        cur_mid = tuple(int(base_mid[i] + (rage_mid[i] - base_mid[i]) * rage_factor) for i in range(3))
        cur_bottom = tuple(int(base_bottom[i] + (rage_bottom[i] - base_bottom[i]) * rage_factor) for i in range(3))

        mid_y = int(h * 0.55)

        # Draw line-by-line smooth vertical gradient
        for y in range(h):
            if y < mid_y:
                t = y / max(1, mid_y)
                col = (
                    int(cur_top[0] + (cur_mid[0] - cur_top[0]) * t),
                    int(cur_top[1] + (cur_mid[1] - cur_top[1]) * t),
                    int(cur_top[2] + (cur_mid[2] - cur_top[2]) * t),
                )
            else:
                t = (y - mid_y) / max(1, (h - mid_y))
                col = (
                    int(cur_mid[0] + (cur_bottom[0] - cur_mid[0]) * t),
                    int(cur_mid[1] + (cur_bottom[1] - cur_mid[1]) * t),
                    int(cur_mid[2] + (cur_bottom[2] - cur_mid[2]) * t),
                )
            pygame.draw.line(self.sky_surface, col, (0, y), (LOGICAL_W, y))

    def _render_distant_silhouette(self) -> None:
        """Draws Manila kanto skyline with corrugated rooftops, TV antennas, and Meralco poles."""
        self.city_silhouette.fill((0, 0, 0, 0))
        h = int(GROUND_Y)
        silhouette_col = (20, 24, 38)
        wire_col = (30, 34, 48)

        # 1. Rooftop skyline buildings
        roof_points = [
            (0, h),
            (0, 440),
            (60, 420),
            (110, 440),
            (160, 430),
            (210, 450),
            (280, 410),
            (350, 410),
            (410, 435),
            (470, 415),
            (540, 445),
            (620, 425),
            (700, 425),
            (780, 395),
            (850, 435),
            (930, 405),
            (1020, 420),
            (1100, 390),
            (1180, 430),
            (LOGICAL_W, 410),
            (LOGICAL_W, h),
        ]
        pygame.draw.polygon(self.city_silhouette, silhouette_col, roof_points)

        # 2. TV Antennas on rooftops
        antennas = [(85, 420), (320, 410), (660, 425), (960, 405), (1140, 390)]
        for ax, ay in antennas:
            pygame.draw.line(self.city_silhouette, silhouette_col, (ax, ay), (ax, ay - 35), 2)
            pygame.draw.line(self.city_silhouette, silhouette_col, (ax - 12, ay - 26), (ax + 12, ay - 26), 2)
            pygame.draw.line(self.city_silhouette, silhouette_col, (ax - 8, ay - 14), (ax + 8, ay - 14), 2)

        # 3. Meralco Utility Poles (Poles with crossarms & transformer)
        poles_x = [240, 940]
        for px in poles_x:
            # Main pole post
            pygame.draw.rect(self.city_silhouette, (16, 20, 32), (px - 5, 230, 10, h - 230))
            # Crossarms
            pygame.draw.rect(self.city_silhouette, (16, 20, 32), (px - 32, 250, 64, 5))
            pygame.draw.rect(self.city_silhouette, (16, 20, 32), (px - 26, 272, 52, 4))
            # Insulator pins
            for ix in [-28, -12, 12, 28]:
                pygame.draw.rect(self.city_silhouette, (45, 52, 70), (px + ix - 2, 244, 4, 6))
            # Cylindrical transformer can
            pygame.draw.rect(self.city_silhouette, (24, 28, 42), (px + 8, 285, 18, 28), border_radius=3)

        # 4. Sagging Catenary Electric Wires
        wire_spans = [
            ((0, 245), (240, 250), 20),
            ((240, 250), (940, 250), 38),
            ((940, 250), (LOGICAL_W, 245), 22),
            ((0, 268), (240, 272), 16),
            ((240, 272), (940, 272), 34),
            ((940, 272), (LOGICAL_W, 268), 18),
        ]
        for p1, p2, sag in wire_spans:
            steps = 24
            pts = []
            for s in range(steps + 1):
                t = s / steps
                wx = p1[0] + (p2[0] - p1[0]) * t
                # Parabolic sag
                wy = (p1[1] + (p2[1] - p1[1]) * t) + (4.0 * sag * t * (1.0 - t))
                pts.append((int(wx), int(wy)))
            if len(pts) > 1:
                pygame.draw.lines(self.city_silhouette, wire_col, False, pts, 2)

    def _render_sari_sari_store(self) -> None:
        """Renders stylized Sari-Sari Store with corrugated roof, iron grill, and hanging snack packets."""
        self.sari_sari_surface.fill((0, 0, 0, 0))
        w, h = 400, 260

        # Store walls (weathered turquoise cinderblock / wood)
        wall_rect = pygame.Rect(40, 50, 340, 210)
        pygame.draw.rect(self.sari_sari_surface, (36, 52, 58), wall_rect)
        pygame.draw.rect(self.sari_sari_surface, (28, 40, 46), wall_rect, width=3)

        # Warm interior light opening (store window counter)
        counter_rect = pygame.Rect(70, 95, 230, 115)
        pygame.draw.rect(self.sari_sari_surface, (60, 45, 26), counter_rect)
        pygame.draw.rect(self.sari_sari_surface, (255, 200, 90, 40), counter_rect)  # Warm glow

        # Shelves inside counter with canned goods
        for sy in [120, 155, 185]:
            pygame.draw.line(self.sari_sari_surface, (45, 34, 20), (70, sy), (300, sy), 3)
            for cx in range(80, 290, 22):
                can_col = random.choice([COLOR_BRICK_RED, COLOR_SUNSHINE, (190, 195, 210)])
                pygame.draw.rect(self.sari_sari_surface, can_col, (cx, sy - 14, 14, 14), border_radius=2)

        # Iron window security grill (rehas)
        for gx in range(75, 300, 18):
            pygame.draw.line(self.sari_sari_surface, (18, 22, 28), (gx, 95), (gx, 210), 2)
        pygame.draw.line(self.sari_sari_surface, (18, 22, 28), (70, 145), (300, 145), 2)
        pygame.draw.line(self.sari_sari_surface, (18, 22, 28), (70, 180), (300, 180), 2)

        # Counter wooden ledge
        ledge_rect = pygame.Rect(60, 208, 250, 12)
        pygame.draw.rect(self.sari_sari_surface, (80, 56, 36), ledge_rect, border_radius=3)

        # Hanging snack packets (chichirya / chips in plastic strips)
        snack_colors = [COLOR_BRICK_RED, COLOR_SUNSHINE, COLOR_TASSEL_GREEN, COLOR_RETRO_CYAN, COLOR_TASSEL_GOLD]
        for sx in [85, 125, 165, 205, 245, 280]:
            # Hanging nylon cord
            pygame.draw.line(self.sari_sari_surface, (200, 210, 220), (sx, 90), (sx, 175), 1)
            for sy in range(100, 170, 15):
                scol = random.choice(snack_colors)
                pkt_rect = pygame.Rect(sx - 5, sy, 11, 13)
                pygame.draw.rect(self.sari_sari_surface, scol, pkt_rect, border_radius=2)
                pygame.draw.rect(self.sari_sari_surface, (20, 24, 30), pkt_rect, width=1, border_radius=2)

        # Corrugated Galvanized Iron (Yero) Slanted Awning Roof
        roof_pts = [(15, 60), (380, 40), (395, 75), (0, 95)]
        pygame.draw.polygon(self.sari_sari_surface, (65, 72, 85), roof_pts)
        pygame.draw.polygon(self.sari_sari_surface, (40, 45, 55), roof_pts, width=2)
        # Corrugation ridges
        for rx in range(25, 380, 14):
            t = (rx - 25) / 355.0
            ry1 = int(60 + (40 - 60) * t)
            ry2 = int(95 + (75 - 95) * t)
            pygame.draw.line(self.sari_sari_surface, (88, 98, 115), (rx, ry1), (rx - 15, ry2), 2)

        # Hand-painted Store Signboard
        sign_rect = pygame.Rect(90, 12, 220, 36)
        pygame.draw.rect(self.sari_sari_surface, (18, 22, 30), sign_rect.move(2, 2), border_radius=5)
        pygame.draw.rect(self.sari_sari_surface, COLOR_TASSEL_GOLD, sign_rect, border_radius=5)
        pygame.draw.rect(self.sari_sari_surface, COLOR_BRICK_RED, sign_rect, width=2, border_radius=5)

        assert self.font_sign
        surf_txt = self.font_sign.render("ALING NENA'S STORE", True, (25, 20, 15))
        self.sari_sari_surface.blit(surf_txt, surf_txt.get_rect(center=sign_rect.center))

    def _render_tricycle(self) -> None:
        """Renders stylized parked Philippine tricycle silhouette with sidecar."""
        self.tricycle_surface.fill((0, 0, 0, 0))
        col_body = (24, 28, 40)
        col_roof = (42, 48, 64)
        col_wheel = (16, 18, 26)
        col_accent = COLOR_SUNSHINE

        # 1. Wheels (Motorcycle rear wheel, front wheel, sidecar wheel)
        wheels = [(45, 130, 24), (115, 130, 24), (185, 132, 22)]
        for wx, wy, r in wheels:
            pygame.draw.circle(self.tricycle_surface, col_wheel, (wx, wy), r)
            pygame.draw.circle(self.tricycle_surface, (55, 62, 78), (wx, wy), r - 6, width=2)
            pygame.draw.circle(self.tricycle_surface, (70, 78, 95), (wx, wy), 5)

        # 2. Motorcycle chassis and gas tank
        pygame.draw.polygon(self.tricycle_surface, col_body, [(35, 115), (60, 95), (95, 95), (115, 115), (80, 128)])
        pygame.draw.rect(self.tricycle_surface, col_accent, (65, 92, 26, 10), border_radius=3)  # Gas tank
        # Motorcycle seat
        pygame.draw.rect(self.tricycle_surface, (18, 20, 28), (40, 92, 24, 8), border_radius=2)
        # Handlebars and headlight
        pygame.draw.line(self.tricycle_surface, (70, 78, 95), (105, 95), (112, 78), 3)
        pygame.draw.line(self.tricycle_surface, (70, 78, 95), (106, 78), (118, 78), 3)
        pygame.draw.circle(self.tricycle_surface, (255, 240, 160), (120, 85), 6)  # Headlamp

        # 3. Sidecar Cabin (Passenger tub + curved stainless roof)
        tub_pts = [(135, 128), (135, 95), (170, 95), (205, 108), (205, 128)]
        pygame.draw.polygon(self.tricycle_surface, col_body, tub_pts)
        pygame.draw.line(self.tricycle_surface, col_accent, (136, 110), (204, 110), 2)  # Stripe

        # Passenger opening
        pygame.draw.rect(self.tricycle_surface, (12, 14, 20), (142, 75, 42, 35), border_radius=4)

        # Roof support stanchions
        pygame.draw.line(self.tricycle_surface, (70, 78, 95), (138, 95), (138, 55), 3)
        pygame.draw.line(self.tricycle_surface, (70, 78, 95), (198, 95), (198, 55), 3)

        # Curved stainless steel passenger roof
        roof_rect = pygame.Rect(128, 48, 82, 14)
        pygame.draw.rect(self.tricycle_surface, col_roof, roof_rect, border_radius=6)
        pygame.draw.line(self.tricycle_surface, (140, 150, 175), (132, 52), (204, 52), 2)  # Chrome shine

    def _render_asphalt(self) -> None:
        """Renders dark asphalt street surface with subtle texture grain."""
        self.asphalt_surface.fill(COLOR_ASPHALT)
        w, h = self.asphalt_surface.get_size()

        # Add speckles / texture grain
        for _ in range(400):
            sx = random.randint(0, w - 1)
            sy = random.randint(0, h - 1)
            shade = random.randint(22, 45)
            self.asphalt_surface.set_at((sx, sy), (shade, shade, shade + 4))

    def update(self, dt: float, pikon_meter: float = 0.0) -> None:
        """Updates drifting clouds and smooth sky rage transition."""
        self.time_elapsed += dt
        self.pikon_meter = max(0.0, min(100.0, pikon_meter))

        # Update clouds
        for cloud in self.clouds:
            cloud.update(dt)

        # Rage lighting factor (active only when Pikon Meter >= 80%)
        rage_factor = max(0.0, min(1.0, (self.pikon_meter - 80.0) / 20.0))
        self._update_sky_gradient(rage_factor)

    def draw(self, surface: pygame.Surface, offset: Vector2 = Vector2(0, 0)) -> None:
        """
        Renders complete street scenery with screen shake offset.
        Visual hierarchy: Sky -> Clouds -> Distant Skyline/Poles -> Mid-ground Store & Tricycle -> Foreground Road & Chalk.
        """
        ox, oy = int(offset.x), int(offset.y)

        # 1. Sky Gradient
        surface.blit(self.sky_surface, (0, oy))

        # 2. Clouds (subtle parallax)
        for cloud in self.clouds:
            cloud.draw(surface, offset)

        # 3. Distant City Skyline & Utility Poles
        surface.blit(self.city_silhouette, (int(ox * 0.4), int(oy * 0.4)))

        # 4. Mid-ground Sari-Sari Store (Right Sideline)
        store_x = LOGICAL_W - 420 + int(ox * 0.8)
        store_y = int(GROUND_Y) - 250 + int(oy * 0.8)
        surface.blit(self.sari_sari_surface, (store_x, store_y))

        # 5. Mid-ground Parked Tricycle (Left Sideline)
        trike_x = 35 + int(ox * 0.8)
        trike_y = int(GROUND_Y) - 150 + int(oy * 0.8)
        surface.blit(self.tricycle_surface, (trike_x, trike_y))

        # 6. Foreground Asphalt Road
        road_y = int(GROUND_Y) - 50 + oy
        surface.blit(self.asphalt_surface, (0, road_y))

        # 7. Procedural Road Cracks
        for crack in self.cracks:
            pts = [(px + ox, py + oy) for px, py in crack]
            pygame.draw.lines(surface, (18, 20, 26), False, pts, 2)

        # 8. White Chalk Boundary Lines (Guhit ng Kanto)
        gy = int(GROUND_Y) + oy
        # Main baseline across court
        pygame.draw.line(surface, COLOR_CHALK, (0, gy), (LOGICAL_W, gy), 3)

        # Court perspective depth guidelines
        pygame.draw.line(surface, COLOR_CHALK, (220 + ox, gy), (340 + ox, LOGICAL_H), 2)
        pygame.draw.line(surface, COLOR_CHALK, (LOGICAL_W - 220 + ox, gy), (LOGICAL_W - 340 + ox, LOGICAL_H), 2)
        pygame.draw.line(surface, COLOR_CHALK, (LOGICAL_CENTER_X + ox, gy), (LOGICAL_CENTER_X + ox, LOGICAL_H), 2)
