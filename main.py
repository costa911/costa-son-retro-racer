"""Costa Racing - Retro Racer
Version 0.1: First Drive
"""

import pyxel


SCREEN_WIDTH = 160
SCREEN_HEIGHT = 120

ROAD_LEFT = 32
ROAD_RIGHT = 128

CAR_WIDTH = 7
CAR_HEIGHT = 11


class Game:
    def __init__(self):
        # Create our game window.
        pyxel.init(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            title="Costa Racing - Town Track"
        )

        # Starting position of our car.
        self.car_x = 76
        self.car_y = 98

        # Start the Pyxel game loop.
        pyxel.run(self.update, self.draw)

    def update(self):
        """Update the game once every frame."""

        # Move left.
        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A):
            self.car_x -= 2

        # Move right.
        if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
            self.car_x += 2

        # Keep Costa Racing on the track!
        self.car_x = max(
            ROAD_LEFT + 3,
            min(self.car_x, ROAD_RIGHT - CAR_WIDTH - 3)
        )

        # Q quits the game.
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

    def draw_car(self, x, y):
        """Draw the Costa Racing car."""

        RED = 8
        BLACK = 0
        WINDOW = 6

        # Main body.
        pyxel.rect(x + 1, y, 5, 11, RED)
        pyxel.rect(x, y + 3, 7, 6, RED)

        # Cockpit.
        pyxel.rect(x + 2, y + 2, 3, 3, WINDOW)

        # Wheels.
        pyxel.rect(x - 1, y + 2, 1, 3, BLACK)
        pyxel.rect(x + 7, y + 2, 1, 3, BLACK)
        pyxel.rect(x - 1, y + 8, 1, 3, BLACK)
        pyxel.rect(x + 7, y + 8, 1, 3, BLACK)

    def draw(self):
        """Draw Town Track once every frame."""

        GRASS = 3
        ROAD = 5
        WHITE = 7

        # Background.
        pyxel.cls(GRASS)

        # Town Track.
        pyxel.rect(
            ROAD_LEFT,
            0,
            ROAD_RIGHT - ROAD_LEFT,
            SCREEN_HEIGHT,
            ROAD
        )

        # Track edges.
        pyxel.rect(ROAD_LEFT, 0, 2, SCREEN_HEIGHT, WHITE)
        pyxel.rect(ROAD_RIGHT - 2, 0, 2, SCREEN_HEIGHT, WHITE)

        # Lane markings.
        for y in range(0, SCREEN_HEIGHT, 16):
            pyxel.rect(63, y, 2, 8, WHITE)
            pyxel.rect(95, y, 2, 8, WHITE)

        # Our car.
        self.draw_car(self.car_x, self.car_y)

        # Track branding.
        pyxel.text(4, 4, "COSTA RACING", WHITE)
        pyxel.text(4, 12, "TOWN TRACK", WHITE)
        pyxel.text(4, 108, "Q: QUIT", WHITE)


Game()