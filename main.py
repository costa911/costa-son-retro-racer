"""Costa Racing - Retro Racer
Version 0.4: Family Leaderboard
"""

import json
from pathlib import Path

import pyxel


SCREEN_WIDTH = 160
SCREEN_HEIGHT = 120

ROAD_LEFT = 32
ROAD_RIGHT = 128

CAR_WIDTH = 7
CAR_HEIGHT = 11

SCORES_FILE = Path(__file__).with_name("scores.json")


class Game:
    def __init__(self):
        pyxel.init(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            title="Costa Racing - Town Track"
        )

        # Load previous family scores.
        self.scores = self.load_scores()

        # Game starts at the driver-selection screen.
        self.state = "select"
        self.driver_name = ""
        self.name_buffer = ""

        self.reset_race()

        pyxel.run(self.update, self.draw)

    # --------------------------------------------------
    # SCORE / LEADERBOARD
    # --------------------------------------------------

    def load_scores(self):
        """Load previous scores from scores.json."""

        try:
            with open(SCORES_FILE, "r", encoding="utf-8") as file:
                scores = json.load(file)

            if isinstance(scores, list):
                return scores

        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass

        return []

    def save_score(self):
        """Save the current driver's score."""

        self.scores.append(
            {
                "name": self.driver_name,
                "score": self.score
            }
        )

        # Highest scores first.
        self.scores.sort(
            key=lambda result: result["score"],
            reverse=True
        )

        # We only need to keep a sensible history.
        self.scores = self.scores[:100]

        try:
            with open(SCORES_FILE, "w", encoding="utf-8") as file:
                json.dump(
                    self.scores,
                    file,
                    indent=2
                )

        except OSError:
            pass

    def top_five_scores(self):
        """Return the five best scores."""

        return self.scores[:5]

    # --------------------------------------------------
    # RACE SETUP
    # --------------------------------------------------

    def reset_race(self):
        """Reset Town Track for a new race."""

        # Costa Racing car.
        self.car_x = 76
        self.car_y = 98

        # Road animation.
        self.road_offset = 0

        # Traffic.
        self.traffic_x = self.random_traffic_position()
        self.traffic_y = -CAR_HEIGHT

        # Race progress.
        self.score = 0
        self.game_speed = 2.0

    def start_race(self, driver_name):
        """Start a race for the selected driver."""

        self.driver_name = driver_name
        self.reset_race()
        self.state = "playing"

    def random_traffic_position(self):
        """Choose a random position on Town Track."""

        return pyxel.rndi(
            ROAD_LEFT + 5,
            ROAD_RIGHT - CAR_WIDTH - 5
        )

    # --------------------------------------------------
    # UPDATE
    # --------------------------------------------------

    def update(self):
        """Update the current game state."""

        if self.state == "select":
            self.update_driver_select()

        elif self.state == "name_entry":
            self.update_name_entry()

        elif self.state == "playing":
            self.update_race()

        elif self.state == "game_over":
            self.update_game_over()

    def update_driver_select(self):
        """Choose who is racing."""

        if pyxel.btnp(pyxel.KEY_D):
            self.start_race("Daddy")

        elif pyxel.btnp(pyxel.KEY_M):
            self.start_race("Max")

        elif pyxel.btnp(pyxel.KEY_O):
            self.name_buffer = ""
            self.state = "name_entry"

        elif pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

    def update_name_entry(self):
        """Allow another player to type their name."""

        # Read letters A-Z.
        for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
            key = getattr(pyxel, f"KEY_{letter}")

            if pyxel.btnp(key):
                if len(self.name_buffer) < 10:
                    self.name_buffer += letter

        # Allow spaces.
        if pyxel.btnp(pyxel.KEY_SPACE):
            if self.name_buffer and len(self.name_buffer) < 10:
                self.name_buffer += " "

        # Remove the last character.
        if pyxel.btnp(pyxel.KEY_BACKSPACE):
            if self.name_buffer:
                self.name_buffer = self.name_buffer[:-1]
            else:
                # Backspace on an empty name goes back.
                self.state = "select"

        # Start when Enter is pressed.
        if pyxel.btnp(pyxel.KEY_RETURN):
            clean_name = self.name_buffer.strip()

            if clean_name:
                self.start_race(clean_name.title())

    def update_race(self):
        """Update gameplay."""

        # Q quits during a race.
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

        # -------------------------
        # PLAYER MOVEMENT
        # -------------------------

        if pyxel.btn(pyxel.KEY_LEFT) or pyxel.btn(pyxel.KEY_A):
            self.car_x -= 2

        if pyxel.btn(pyxel.KEY_RIGHT) or pyxel.btn(pyxel.KEY_D):
            self.car_x += 2

        # Keep Costa Racing on Town Track.
        self.car_x = max(
            ROAD_LEFT + 3,
            min(
                self.car_x,
                ROAD_RIGHT - CAR_WIDTH - 3
            )
        )

        # -------------------------
        # ROAD MOVEMENT
        # -------------------------

        self.road_offset += self.game_speed
        self.road_offset %= 16

        # -------------------------
        # TRAFFIC
        # -------------------------

        self.traffic_y += self.game_speed

        # Successfully passed the traffic car.
        if self.traffic_y > SCREEN_HEIGHT:
            self.score += 1

            # Spawn one new traffic car.
            self.traffic_y = -CAR_HEIGHT
            self.traffic_x = self.random_traffic_position()

            # Dino-style difficulty:
            # every successful dodge makes the game faster.
            self.game_speed = min(
                6.0,
                2.0 + self.score * 0.20
            )

        # -------------------------
        # COLLISION
        # -------------------------

        if self.has_collided():
            self.save_score()
            self.state = "game_over"

    def update_game_over(self):
        """Wait for restart or another player."""

        # Same driver races again.
        if pyxel.btnp(pyxel.KEY_R):
            self.reset_race()
            self.state = "playing"

        # Return to player selection.
        elif pyxel.btnp(pyxel.KEY_P):
            self.state = "select"

        elif pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

    # --------------------------------------------------
    # COLLISION
    # --------------------------------------------------

    def has_collided(self):
        """Check whether Costa Racing hits traffic."""

        return (
            self.car_x < self.traffic_x + CAR_WIDTH
            and self.car_x + CAR_WIDTH > self.traffic_x
            and self.car_y < self.traffic_y + CAR_HEIGHT
            and self.car_y + CAR_HEIGHT > self.traffic_y
        )

    # --------------------------------------------------
    # DRAW CARS
    # --------------------------------------------------

    def draw_car(self, x, y, body_color):
        """Draw a small racing car."""

        BLACK = 0
        WINDOW = 6

        # Main body.
        pyxel.rect(
            x + 1,
            y,
            5,
            11,
            body_color
        )

        pyxel.rect(
            x,
            y + 3,
            7,
            6,
            body_color
        )

        # Cockpit.
        pyxel.rect(
            x + 2,
            y + 2,
            3,
            3,
            WINDOW
        )

        # Wheels.
        pyxel.rect(x - 1, y + 2, 1, 3, BLACK)
        pyxel.rect(x + 7, y + 2, 1, 3, BLACK)

        pyxel.rect(x - 1, y + 8, 1, 3, BLACK)
        pyxel.rect(x + 7, y + 8, 1, 3, BLACK)

    # --------------------------------------------------
    # DRAW
    # --------------------------------------------------

    def draw(self):
        """Draw the correct screen."""

        if self.state == "select":
            self.draw_driver_select()

        elif self.state == "name_entry":
            self.draw_name_entry()

        elif self.state == "playing":
            self.draw_race()

        elif self.state == "game_over":
            self.draw_race()
            self.draw_game_over()

    # --------------------------------------------------
    # DRIVER SELECT
    # --------------------------------------------------

    def draw_driver_select(self):
        """Draw driver selection and leaderboard."""

        BLACK = 0
        WHITE = 7
        RED = 8
        YELLOW = 10

        pyxel.cls(BLACK)

        pyxel.text(
            48,
            5,
            "COSTA RACING",
            RED
        )

        pyxel.text(
            50,
            14,
            "TOWN TRACK",
            WHITE
        )

        # Leaderboard.
        pyxel.text(
            55,
            28,
            "TOP 5",
            YELLOW
        )

        top_scores = self.top_five_scores()

        if not top_scores:
            pyxel.text(
                48,
                39,
                "NO SCORES YET",
                WHITE
            )

        else:
            for position, result in enumerate(top_scores, start=1):
                y = 36 + (position * 8)

                name = result["name"][:10]
                score = result["score"]

                pyxel.text(
                    38,
                    y,
                    f"{position}. {name:<10} {score}",
                    WHITE
                )

        # Driver selection.
        pyxel.text(
            46,
            88,
            "WHO IS RACING?",
            YELLOW
        )

        pyxel.text(
            42,
            98,
            "D: DADDY",
            WHITE
        )

        pyxel.text(
            92,
            98,
            "M: MAX",
            WHITE
        )

        pyxel.text(
            42,
            108,
            "O: SOMEONE ELSE",
            WHITE
        )

        pyxel.text(
            120,
            108,
            "Q",
            5
        )

    # --------------------------------------------------
    # NAME ENTRY
    # --------------------------------------------------

    def draw_name_entry(self):
        """Draw custom driver name entry."""

        BLACK = 0
        WHITE = 7
        RED = 8
        YELLOW = 10

        pyxel.cls(BLACK)

        pyxel.text(
            45,
            25,
            "NEW DRIVER",
            RED
        )

        pyxel.text(
            35,
            43,
            "TYPE YOUR NAME:",
            WHITE
        )

        # Name-entry box.
        pyxel.rect(
            34,
            55,
            92,
            16,
            5
        )

        pyxel.rectb(
            34,
            55,
            92,
            16,
            WHITE
        )

        display_name = self.name_buffer

        # Blinking cursor.
        if (pyxel.frame_count // 15) % 2 == 0:
            display_name += "_"

        pyxel.text(
            40,
            61,
            display_name,
            YELLOW
        )

        pyxel.text(
            42,
            82,
            "ENTER: START",
            WHITE
        )

        pyxel.text(
            29,
            92,
            "BACKSPACE: DELETE",
            WHITE
        )

        pyxel.text(
            22,
            102,
            "EMPTY + BACKSPACE: BACK",
            6
        )

    # --------------------------------------------------
    # RACE
    # --------------------------------------------------

    def draw_race(self):
        """Draw Town Track."""

        GRASS = 3
        ROAD = 5
        WHITE = 7

        COSTA_RED = 8
        TRAFFIC_YELLOW = 10

        # Background.
        pyxel.cls(GRASS)

        # Road.
        pyxel.rect(
            ROAD_LEFT,
            0,
            ROAD_RIGHT - ROAD_LEFT,
            SCREEN_HEIGHT,
            ROAD
        )

        # Road edges.
        pyxel.rect(
            ROAD_LEFT,
            0,
            2,
            SCREEN_HEIGHT,
            WHITE
        )

        pyxel.rect(
            ROAD_RIGHT - 2,
            0,
            2,
            SCREEN_HEIGHT,
            WHITE
        )

        # Single moving centre line.
        for y in range(-16, SCREEN_HEIGHT + 16, 16):
            marker_y = int(
                y + self.road_offset
            )

            pyxel.rect(
                79,
                marker_y,
                2,
                8,
                WHITE
            )

        # Costa Racing car.
        self.draw_car(
            self.car_x,
            self.car_y,
            COSTA_RED
        )

        # Traffic car.
        self.draw_car(
            self.traffic_x,
            int(self.traffic_y),
            TRAFFIC_YELLOW
        )

        # Left branding.
        pyxel.text(
            4,
            4,
            "COSTA",
            WHITE
        )

        pyxel.text(
            4,
            12,
            "RACING",
            WHITE
        )

        # Right branding.
        pyxel.text(
            134,
            4,
            "TOWN",
            WHITE
        )

        pyxel.text(
            132,
            12,
            "TRACK",
            WHITE
        )

        # Score.
        pyxel.text(
            4,
            35,
            f"SCORE {self.score}",
            WHITE
        )

        # Speed.
        pyxel.text(
            4,
            45,
            f"SPD {self.game_speed:.1f}",
            WHITE
        )

        # Driver.
        pyxel.text(
            132,
            35,
            self.driver_name[:6].upper(),
            WHITE
        )

        pyxel.text(
            4,
            108,
            "Q: QUIT",
            WHITE
        )

    # --------------------------------------------------
    # GAME OVER
    # --------------------------------------------------

    def draw_game_over(self):
        """Draw the crash screen."""

        BLACK = 0
        WHITE = 7
        RED = 8
        YELLOW = 10

        pyxel.rect(
            39,
            37,
            82,
            48,
            BLACK
        )

        pyxel.rectb(
            39,
            37,
            82,
            48,
            RED
        )

        pyxel.text(
            66,
            43,
            "CRASH!",
            RED
        )

        pyxel.text(
            52,
            53,
            self.driver_name[:10].upper(),
            YELLOW
        )

        pyxel.text(
            54,
            62,
            f"SCORE: {self.score}",
            WHITE
        )

        pyxel.text(
            47,
            72,
            "R: RACE AGAIN",
            WHITE
        )

        pyxel.text(
            47,
            79,
            "P: NEW PLAYER",
            WHITE
        )


Game()