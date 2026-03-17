"""Bouncing ball simulation.

A 600x600 pixel window containing a ball that can be picked up with the
left mouse button and dropped on release.  The ball then bounces under
simulated Earth gravity and gradually comes to rest due to energy loss on
each bounce and light air-resistance damping.
"""

import pygame
import sys
import collections

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
WINDOW_WIDTH = 600
WINDOW_HEIGHT = 600
FPS = 60
TITLE = "Bouncing Ball"

BALL_RADIUS = 22
BALL_COLOR = (220, 60, 60)       # red
BALL_OUTLINE_COLOR = (140, 20, 20)
BALL_HELD_COLOR = (240, 140, 60) # orange tint while dragging
BACKGROUND_COLOR = (245, 245, 245)
BORDER_COLOR = (60, 60, 60)

# Physics
GRAVITY = 800.0          # pixels / s²  (≈ 9.8 m/s² at ~80 px/m)
RESTITUTION = 0.72       # fraction of speed retained after bouncing off a wall
AIR_DRAG = 0.995         # velocity multiplier per frame (simulates air resistance)
FLOOR_FRICTION = 0.88    # horizontal speed multiplier on ground contact
REST_THRESHOLD = 1.5     # px/s — below this we consider the ball at rest

# Mouse velocity tracking: sample window
VELOCITY_SAMPLES = 6     # number of recent positions used to estimate throw velocity


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def clamp(value, lo, hi):
    """Return *value* clamped to [lo, hi]."""
    return max(lo, min(hi, value))


# ---------------------------------------------------------------------------
# Main simulation class
# ---------------------------------------------------------------------------
class BouncingBallApp:
    """Pygame application that runs the bouncing ball simulation."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        # Ball state
        self.ball_x = float(WINDOW_WIDTH) / 2
        self.ball_y = float(WINDOW_HEIGHT) / 2
        self.vel_x = 0.0
        self.vel_y = 0.0

        # Drag state
        self.dragging = False
        self.drag_offset_x = 0.0
        self.drag_offset_y = 0.0

        # Rolling deque of (time_ms, mouse_x, mouse_y) for release-velocity estimation
        self.mouse_history = collections.deque(maxlen=VELOCITY_SAMPLES)

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------
    def run(self):
        """Start the application event / render loop."""
        while True:
            dt = self.clock.tick(FPS) / 1000.0  # seconds elapsed this frame
            # Cap dt so a paused/laggy frame doesn't send the ball flying
            dt = min(dt, 0.05)

            self._handle_events()
            self._update_physics(dt)
            self._draw()

        # Never reached, but satisfies linters
        pygame.quit()

    # ------------------------------------------------------------------
    # Event handling
    # ------------------------------------------------------------------
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if self._cursor_on_ball(mx, my):
                    self.dragging = True
                    self.vel_x = 0.0
                    self.vel_y = 0.0
                    self.drag_offset_x = self.ball_x - mx
                    self.drag_offset_y = self.ball_y - my
                    self.mouse_history.clear()
                    self.mouse_history.append((pygame.time.get_ticks(), mx, my))

            elif event.type == pygame.MOUSEMOTION and self.dragging:
                mx, my = event.pos
                self.mouse_history.append((pygame.time.get_ticks(), mx, my))
                self.ball_x = clamp(
                    mx + self.drag_offset_x,
                    BALL_RADIUS,
                    WINDOW_WIDTH - BALL_RADIUS,
                )
                self.ball_y = clamp(
                    my + self.drag_offset_y,
                    BALL_RADIUS,
                    WINDOW_HEIGHT - BALL_RADIUS,
                )

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.dragging:
                    self.dragging = False
                    self.vel_x, self.vel_y = self._estimate_release_velocity()

    # ------------------------------------------------------------------
    # Physics update
    # ------------------------------------------------------------------
    def _update_physics(self, dt):
        if self.dragging:
            return

        # Apply gravity
        self.vel_y += GRAVITY * dt

        # Apply air resistance
        self.vel_x *= AIR_DRAG
        self.vel_y *= AIR_DRAG

        # Move ball
        self.ball_x += self.vel_x * dt
        self.ball_y += self.vel_y * dt

        # --- Boundary collisions ---

        # Left wall
        if self.ball_x - BALL_RADIUS < 0:
            self.ball_x = BALL_RADIUS
            self.vel_x = abs(self.vel_x) * RESTITUTION

        # Right wall
        if self.ball_x + BALL_RADIUS > WINDOW_WIDTH:
            self.ball_x = WINDOW_WIDTH - BALL_RADIUS
            self.vel_x = -abs(self.vel_x) * RESTITUTION

        # Ceiling
        if self.ball_y - BALL_RADIUS < 0:
            self.ball_y = BALL_RADIUS
            self.vel_y = abs(self.vel_y) * RESTITUTION

        # Floor
        if self.ball_y + BALL_RADIUS > WINDOW_HEIGHT:
            self.ball_y = WINDOW_HEIGHT - BALL_RADIUS
            self.vel_y = -abs(self.vel_y) * RESTITUTION
            # Rolling / sliding friction on the floor
            self.vel_x *= FLOOR_FRICTION

        # Snap to rest once effectively stationary on the floor
        on_floor = self.ball_y + BALL_RADIUS >= WINDOW_HEIGHT - 1
        if on_floor and abs(self.vel_y) < REST_THRESHOLD:
            self.vel_y = 0.0
            self.ball_y = WINDOW_HEIGHT - BALL_RADIUS
        if abs(self.vel_x) < REST_THRESHOLD and abs(self.vel_y) == 0.0:
            self.vel_x = 0.0

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def _draw(self):
        self.screen.fill(BACKGROUND_COLOR)

        # Border to make the 600×600 box visible
        pygame.draw.rect(
            self.screen,
            BORDER_COLOR,
            pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT),
            3,
        )

        # Ball fill
        color = BALL_HELD_COLOR if self.dragging else BALL_COLOR
        pos = (int(self.ball_x), int(self.ball_y))
        pygame.draw.circle(self.screen, color, pos, BALL_RADIUS)
        # Ball outline
        pygame.draw.circle(self.screen, BALL_OUTLINE_COLOR, pos, BALL_RADIUS, 2)

        pygame.display.flip()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _cursor_on_ball(self, mx, my):
        """Return True if the cursor (mx, my) is within the ball's radius."""
        dx = mx - self.ball_x
        dy = my - self.ball_y
        return dx * dx + dy * dy <= BALL_RADIUS * BALL_RADIUS

    def _estimate_release_velocity(self):
        """Estimate throw velocity from the most recent mouse-movement history.

        Uses the oldest and newest samples in the history window so that brief
        acceleration at the very end of a throw is captured accurately.
        """
        if len(self.mouse_history) < 2:
            return 0.0, 0.0

        t0, x0, y0 = self.mouse_history[0]
        t1, x1, y1 = self.mouse_history[-1]
        dt_ms = t1 - t0
        if dt_ms <= 0:
            return 0.0, 0.0

        dt_s = dt_ms / 1000.0
        return (x1 - x0) / dt_s, (y1 - y0) / dt_s


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    app = BouncingBallApp()
    app.run()
