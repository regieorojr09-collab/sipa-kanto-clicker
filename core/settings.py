"""Core settings and game constants for Sipa: Kanto Clicker."""

from typing import Final

# -----------------------------------------------------------------------------
# Display & Canvas Dimensions
# -----------------------------------------------------------------------------
LOGICAL_W: Final[int] = 1280
LOGICAL_H: Final[int] = 720
LOGICAL_SIZE: Final[tuple[int, int]] = (LOGICAL_W, LOGICAL_H)
LOGICAL_CENTER_X: Final[int] = LOGICAL_W // 2
LOGICAL_CENTER_Y: Final[int] = LOGICAL_H // 2
ASPECT_RATIO: Final[float] = LOGICAL_W / LOGICAL_H

TARGET_FPS: Final[int] = 60
MAX_DELTA_TIME: Final[float] = 0.1  # Clamped to prevent physics blow-ups on tab pause
WINDOW_TITLE: Final[str] = "Sipa: Kanto Clicker"

# -----------------------------------------------------------------------------
# Filipino Street Arcade Color Palette
# -----------------------------------------------------------------------------
# Atmosphere & Backgrounds
COLOR_BG_DARK: Final[tuple[int, int, int]] = (18, 20, 28)
COLOR_ASPHALT: Final[tuple[int, int, int]] = (34, 38, 48)
COLOR_CONCRETE: Final[tuple[int, int, int]] = (120, 126, 138)
COLOR_CHALK: Final[tuple[int, int, int]] = (245, 244, 236)

# Vibrant Sari-Sari Store & Manila Sun Accents
COLOR_SUNSHINE: Final[tuple[int, int, int]] = (255, 204, 0)
COLOR_BRICK_RED: Final[tuple[int, int, int]] = (217, 68, 64)
COLOR_NEON_YELLOW: Final[tuple[int, int, int]] = (255, 240, 60)
COLOR_RETRO_CYAN: Final[tuple[int, int, int]] = (0, 225, 245)
COLOR_RETRO_MAGENTA: Final[tuple[int, int, int]] = (240, 45, 135)
COLOR_NEON_GREEN: Final[tuple[int, int, int]] = (40, 220, 110)

# Sipa Metallic Washer & Colored Plastic Tassels
COLOR_WASHER_GRAY: Final[tuple[int, int, int]] = (185, 190, 200)
COLOR_WASHER_EDGE: Final[tuple[int, int, int]] = (95, 100, 112)
COLOR_TASSEL_CYAN: Final[tuple[int, int, int]] = (0, 230, 255)
COLOR_TASSEL_MAGENTA: Final[tuple[int, int, int]] = (255, 40, 140)
COLOR_TASSEL_GOLD: Final[tuple[int, int, int]] = (255, 195, 20)
COLOR_TASSEL_GREEN: Final[tuple[int, int, int]] = (50, 225, 120)

# Typography & Interface
COLOR_TEXT_PRIMARY: Final[tuple[int, int, int]] = (248, 249, 252)
COLOR_TEXT_MUTED: Final[tuple[int, int, int]] = (145, 152, 168)
COLOR_CARD_BG: Final[tuple[int, int, int]] = (26, 30, 42)
COLOR_CARD_BORDER: Final[tuple[int, int, int]] = (52, 58, 76)
COLOR_ACCENT: Final[tuple[int, int, int]] = (255, 195, 18)
COLOR_ACCENT_HOVER: Final[tuple[int, int, int]] = (255, 220, 65)

# -----------------------------------------------------------------------------
# Physics & Kinematic Parameters
# -----------------------------------------------------------------------------
GRAVITY: Final[float] = 980.0  # Pixels per second squared (arcade tuning)
GROUND_Y: Final[float] = 610.0  # Pixel coordinate of street pavement line
BASE_KICK_VELOCITY: Final[float] = 860.0  # Initial launch speed in px/s
SIPA_RADIUS: Final[float] = 14.0  # Sipa visual collision radius

# -----------------------------------------------------------------------------
# Precision Rhythm & Hit Judgments (Osu!-style Timing Windows in milliseconds)
# -----------------------------------------------------------------------------
TIMING_SWAK_MS: Final[float] = 25.0    # Perfect (±25 ms) -> 300 pts
TIMING_PUWEDE_MS: Final[float] = 70.0  # Good    (±70 ms) -> 100 pts
TIMING_DAPLIS_MS: Final[float] = 120.0 # OK      (±120 ms) -> 50 pts

# Visual Target Defaults
HIT_CIRCLE_RADIUS: Final[float] = 36.0     # Clickable core circle
APPROACH_RING_MAX_R: Final[float] = 130.0  # Starting radius of approach ring
DEFAULT_APPROACH_RATE: Final[float] = 6.0  # Approach Rate (AR)
