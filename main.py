"""Costa Racing - Retro Racer
Version 0.5: Traffic Variety + Garage
"""

import json
from pathlib import Path

import pyxel


SCREEN_WIDTH = 160
SCREEN_HEIGHT = 120

ROAD_LEFT = 32
ROAD_RIGHT = 128

PLAYER_WIDTH = 9
PLAYER_HEIGHT = 13

SCORES_FILE = Path(__file__).with_name("scores.json")

# Traffic colours deliberately exclude Costa Racing red (8) and road grey (5).
TRAFFIC_COLORS = [6, 9, 10, 11, 12, 13, 14, 15]

TRAFFIC_SPECS = {
    "car": {
        "width": 7,
        "height": 11,
        "weight": 6,
    },
    "truck": {
        "width": 9,
        "height": 15,
        "weight": 2,
    },
    "bus": {
        "width": 9,
        "height": 18,
        "weight": 1,
    },
}

# Global family unlocks are based on the best score saved in scores.json.
GARAGE = [
    {
        "key": "costa_f1",
        "name": "COSTA F1",
        "unlock_score": 0,
    },
    {
        "key": "blue_gt",
        "name": "BLUE GT",
        "unlock_score": 10,
    },
    {
        "key": "gold_arrow",
        "name": "GOLD ARROW",
        "unlock_score": 25,
    },
]


class Game:
    def __init__(self):
        pyxel.init(
            SCREEN_WIDTH,
            SCREEN_HEIGHT,
            title="Costa Racing - Town Track"
        )

        # Load previous family scores.
        self.scores = self.load_scores()

        # Start at driver selection.
        self.state = "select"
        self.driver_name = ""
        self.name_buffer = ""

        # Garage selection.
        self.selected_car_key = "costa_f1"
        self.newly_unlocked = []

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
        """Save the current driver's score and detect new unlocks."""

        previous_best = self.best_score()

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

        # Keep up to 100 historic scores.
        self.scores = self.scores[:100]

        current_best = self.best_score()
        self.newly_unlocked = [
            car["name"]
            for car in GARAGE
            if previous_best < car["unlock_score"] <= current_best
        ]

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

    def best_score(self):
        """Return the highest family score saved so far."""

        if not self.scores:
            return 0

        return max(
            result.get("score", 0)
            for result in self.scores
            if isinstance(result, dict)
        )

    # --------------------------------------------------
    # GARAGE / UNLOCKS
    # --------------------------------------------------

    def unlocked_cars(self):
        """Return cars unlocked by the current family best score."""

        best = self.best_score()

        return [
            car
            for car in GARAGE
            if best >= car["unlock_score"]
        ]

    def selected_car(self):
        """Return the currently selected garage entry."""

        for car in GARAGE:
            if car["key"] == self.selected_car_key:
                return car

        return GARAGE[0]

    def cycle_car(self):
        """Cycle through cars that have already been unlocked."""

        available = self.unlocked_cars()

        if not available:
            self.selected_car_key = GARAGE[0]["key"]
            return

        keys = [car["key"] for car in available]

        try:
            current_index = keys.index(self.selected_car_key)
        except ValueError:
            current_index = 0

        next_index = (current_index + 1) % len(keys)
        self.selected_car_key = keys[next_index]

    def next_unlock(self):
        """Return the next locked car, if there is one."""

        best = self.best_score()

        for car in GARAGE:
            if best < car["unlock_score"]:
                return car

        return None

    # --------------------------------------------------
    # RACE SETUP
    # --------------------------------------------------

    def reset_race(self):
        """Reset Town Track for a new race."""

        # Costa Racing car.
        self.car_x = 75
        self.car_y = 96

        # Moving road.
        self.road_offset = 0

        # Traffic vehicle.
        self.spawn_traffic()

        # Race progress.
        self.score = 0
        self.game_speed = 2.0
        self.newly_unlocked = []

    def start_race(self, driver_name):
        """Start a race for the selected driver."""

        self.driver_name = driver_name
        self.reset_race()
        self.state = "playing"

    def random_traffic_type(self):
        """Choose a weighted traffic vehicle type."""

        roll = pyxel.rndi(
            1,
            sum(spec["weight"] for spec in TRAFFIC_SPECS.values())
        )

        running_total = 0

        for vehicle_type, spec in TRAFFIC_SPECS.items():
            running_total += spec["weight"]

            if roll <= running_total:
                return vehicle_type

        return "car"

    def random_traffic_position(self, width):
        """Choose a random position on Town Track for a vehicle width."""

        return pyxel.rndi(
            ROAD_LEFT + 5,
            ROAD_RIGHT - width - 5
        )

    def spawn_traffic(self):
        """Create one new traffic vehicle."""

        self.traffic_type = self.random_traffic_type()

        spec = TRAFFIC_SPECS[self.traffic_type]
        self.traffic_width = spec["width"]
        self.traffic_height = spec["height"]

        color_index = pyxel.rndi(0, len(TRAFFIC_COLORS) - 1)
        self.traffic_color = TRAFFIC_COLORS[color_index]

        self.traffic_x = self.random_traffic_position(
            self.traffic_width
        )
        self.traffic_y = -self.traffic_height

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
        """Choose who is racing and which unlocked car to use."""

        if pyxel.btnp(pyxel.KEY_C):
            self.cycle_car()

        elif pyxel.btnp(pyxel.KEY_D):
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
                ROAD_RIGHT - PLAYER_WIDTH - 3
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

        # Successfully passed the traffic vehicle.
        if self.traffic_y > SCREEN_HEIGHT:
            self.score += 1
            self.spawn_traffic()

            # Increase speed after each successful dodge.
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
        """Check whether Costa Racing hits the current traffic vehicle."""

        return (
            self.car_x < self.traffic_x + self.traffic_width
            and self.car_x + PLAYER_WIDTH > self.traffic_x
            and self.car_y < self.traffic_y + self.traffic_height
            and self.car_y + PLAYER_HEIGHT > self.traffic_y
        )

    # --------------------------------------------------
    # VEHICLES
    # --------------------------------------------------

    def draw_f1_car(self, x, y, body_color):
        """Draw a small Formula 1 inspired player car."""

        BLACK = 0
        WHITE = 7
        WINDOW = 6

        # Front wing.
        pyxel.rect(x, y, 9, 2, body_color)
        pyxel.rect(x + 2, y + 2, 5, 2, body_color)

        # Narrow nose.
        pyxel.rect(x + 3, y + 3, 3, 4, body_color)

        # Side pods / main body.
        pyxel.rect(x + 1, y + 6, 7, 4, body_color)

        # Cockpit.
        pyxel.rect(x + 3, y + 6, 3, 2, WINDOW)

        # Rear body and wing.
        pyxel.rect(x + 2, y + 9, 5, 2, body_color)
        pyxel.rect(x, y + 11, 9, 2, body_color)

        # Wheels.
        pyxel.rect(x, y + 3, 2, 3, BLACK)
        pyxel.rect(x + 7, y + 3, 2, 3, BLACK)
        pyxel.rect(x, y + 8, 2, 3, BLACK)
        pyxel.rect(x + 7, y + 8, 2, 3, BLACK)

        # Tiny highlight stripe.
        pyxel.pset(x + 4, y + 3, WHITE)

    def draw_gt_car(self, x, y, body_color):
        """Draw a chunkier GT-style unlockable car."""

        BLACK = 0
        WINDOW = 6

        pyxel.rect(x + 1, y + 1, 7, 11, body_color)
        pyxel.rect(x, y + 4, 9, 6, body_color)
        pyxel.rect(x + 2, y + 3, 5, 3, WINDOW)

        pyxel.rect(x, y + 2, 1, 3, BLACK)
        pyxel.rect(x + 8, y + 2, 1, 3, BLACK)
        pyxel.rect(x, y + 9, 1, 3, BLACK)
        pyxel.rect(x + 8, y + 9, 1, 3, BLACK)

    def draw_arrow_car(self, x, y, body_color):
        """Draw a pointed prototype-style unlockable car."""

        BLACK = 0
        WINDOW = 6

        pyxel.rect(x + 4, y, 1, 2, body_color)
        pyxel.rect(x + 3, y + 2, 3, 3, body_color)
        pyxel.rect(x + 1, y + 5, 7, 5, body_color)
        pyxel.rect(x, y + 8, 9, 3, body_color)
        pyxel.rect(x + 2, y + 11, 5, 2, body_color)
        pyxel.rect(x + 3, y + 5, 3, 2, WINDOW)

        pyxel.rect(x, y + 5, 1, 3, BLACK)
        pyxel.rect(x + 8, y + 5, 1, 3, BLACK)
        pyxel.rect(x, y + 10, 1, 3, BLACK)
        pyxel.rect(x + 8, y + 10, 1, 3, BLACK)

    def draw_player_car(self, x, y):
        """Draw whichever unlocked Costa Racing car is selected."""

        selected = self.selected_car_key

        if selected == "blue_gt":
            self.draw_gt_car(x, y, 12)

        elif selected == "gold_arrow":
            self.draw_arrow_car(x, y, 10)

        else:
            # Main Costa Racing car: Ferrari-inspired red F1 silhouette.
            self.draw_f1_car(x, y, 8)

    def draw_traffic_car(self, x, y, body_color):
        """Draw a normal road car."""

        BLACK = 0
        WINDOW = 6

        pyxel.rect(x + 1, y, 5, 11, body_color)
        pyxel.rect(x, y + 3, 7, 6, body_color)
        pyxel.rect(x + 2, y + 2, 3, 3, WINDOW)

        pyxel.rect(x - 1, y + 2, 1, 3, BLACK)
        pyxel.rect(x + 7, y + 2, 1, 3, BLACK)
        pyxel.rect(x - 1, y + 8, 1, 3, BLACK)
        pyxel.rect(x + 7, y + 8, 1, 3, BLACK)

    def draw_truck(self, x, y, body_color):
        """Draw a boxy truck."""

        BLACK = 0
        WINDOW = 6
        WHITE = 7

        # Cab.
        pyxel.rect(x + 1, y, 7, 6, body_color)
        pyxel.rect(x + 2, y + 1, 5, 2, WINDOW)

        # Cargo box.
        pyxel.rect(x, y + 6, 9, 8, body_color)
        pyxel.rectb(x, y + 6, 9, 8, WHITE)

        # Wheels.
        pyxel.rect(x - 1, y + 3, 1, 3, BLACK)
        pyxel.rect(x + 9, y + 3, 1, 3, BLACK)
        pyxel.rect(x - 1, y + 11, 1, 3, BLACK)
        pyxel.rect(x + 9, y + 11, 1, 3, BLACK)

    def draw_bus(self, x, y, body_color):
        """Draw a long bus."""

        BLACK = 0
        WINDOW = 6

        pyxel.rect(x, y, 9, 18, body_color)

        # Windscreen.
        pyxel.rect(x + 1, y + 1, 7, 3, WINDOW)

        # Side/rear windows.
        pyxel.rect(x + 1, y + 6, 2, 3, WINDOW)
        pyxel.rect(x + 4, y + 6, 2, 3, WINDOW)
        pyxel.rect(x + 7, y + 6, 1, 3, WINDOW)

        # Bumpers.
        pyxel.rect(x + 1, y + 16, 7, 1, BLACK)

        # Wheels.
        pyxel.rect(x - 1, y + 4, 1, 4, BLACK)
        pyxel.rect(x + 9, y + 4, 1, 4, BLACK)
        pyxel.rect(x - 1, y + 13, 1, 4, BLACK)
        pyxel.rect(x + 9, y + 13, 1, 4, BLACK)

    def draw_traffic(self):
        """Draw the current traffic vehicle."""

        x = self.traffic_x
        y = int(self.traffic_y)

        if self.traffic_type == "truck":
            self.draw_truck(x, y, self.traffic_color)

        elif self.traffic_type == "bus":
            self.draw_bus(x, y, self.traffic_color)

        else:
            self.draw_traffic_car(x, y, self.traffic_color)

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
        """Draw driver selection, leaderboard and garage."""

        BLACK = 0
        WHITE = 7
        RED = 8
        YELLOW = 10
        CYAN = 12

        pyxel.cls(BLACK)

        pyxel.text(
            48,
            4,
            "COSTA RACING",
            RED
        )

        pyxel.text(
            50,
            12,
            "TOWN TRACK",
            WHITE
        )

        # Leaderboard.
        pyxel.text(
            55,
            24,
            "TOP 5",
            YELLOW
        )

        top_scores = self.top_five_scores()

        if not top_scores:
            pyxel.text(
                48,
                35,
                "NO SCORES YET",
                WHITE
            )

        else:
            for position, result in enumerate(top_scores, start=1):
                y = 30 + (position * 8)

                name = result["name"][:10]
                score = result["score"]

                pyxel.text(
                    38,
                    y,
                    f"{position}. {name:<10} {score}",
                    WHITE
                )

        # Garage.
        selected = self.selected_car()
        pyxel.text(
            5,
            77,
            f"CAR: {selected['name']}",
            CYAN
        )

        next_car = self.next_unlock()

        if next_car:
            pyxel.text(
                5,
                85,
                f"C: CHANGE  NEXT {next_car['unlock_score']}",
                WHITE
            )
        else:
            pyxel.text(
                5,
                85,
                "C: CHANGE  ALL UNLOCKED",
                WHITE
            )

        # Driver selection.
        pyxel.text(
            47,
            94,
            "WHO IS RACING?",
            YELLOW
        )

        pyxel.text(
            20,
            103,
            "D: DADDY",
            WHITE
        )

        pyxel.text(
            70,
            103,
            "M: MAX",
            WHITE
        )

        pyxel.text(
            112,
            103,
            "O: OTHER",
            WHITE
        )

        pyxel.text(
            4,
            113,
            "Q: QUIT",
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
        self.draw_player_car(
            self.car_x,
            self.car_y
        )

        # Traffic vehicle.
        self.draw_traffic()

        # -------------------------
        # LEFT GRASS HUD
        # -------------------------

        # Costa Racing branding.
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

        # Score block.
        pyxel.text(
            4,
            35,
            "SCORE",
            WHITE
        )

        pyxel.text(
            4,
            43,
            str(self.score),
            WHITE
        )

        # Speed block.
        pyxel.text(
            4,
            57,
            "SPEED",
            WHITE
        )

        pyxel.text(
            4,
            65,
            f"{self.game_speed:.1f}",
            WHITE
        )

        # Quit control.
        pyxel.text(
            4,
            108,
            "Q: QUIT",
            WHITE
        )

        # -------------------------
        # RIGHT GRASS HUD
        # -------------------------

        # Town Track branding.
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

        # Current driver.
        pyxel.text(
            132,
            35,
            self.driver_name[:6].upper(),
            WHITE
        )

        # Current vehicle shorthand.
        car_label = self.selected_car()["name"][:6]
        pyxel.text(
            132,
            47,
            car_label,
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
        CYAN = 12

        panel_height = 58 if self.newly_unlocked else 48
        panel_y = 32 if self.newly_unlocked else 37

        pyxel.rect(
            35,
            panel_y,
            90,
            panel_height,
            BLACK
        )

        pyxel.rectb(
            35,
            panel_y,
            90,
            panel_height,
            RED
        )

        pyxel.text(
            66,
            panel_y + 6,
            "CRASH!",
            RED
        )

        pyxel.text(
            52,
            panel_y + 16,
            self.driver_name[:10].upper(),
            YELLOW
        )

        pyxel.text(
            54,
            panel_y + 25,
            f"SCORE: {self.score}",
            WHITE
        )

        if self.newly_unlocked:
            unlock_name = self.newly_unlocked[0][:12]
            pyxel.text(
                42,
                panel_y + 34,
                "NEW CAR UNLOCKED!",
                CYAN
            )
            pyxel.text(
                52,
                panel_y + 42,
                unlock_name,
                YELLOW
            )

            controls_y = panel_y + 50
        else:
            controls_y = panel_y + 35

        pyxel.text(
            43,
            controls_y,
            "R: AGAIN  P: PLAYERS",
            WHITE
        )


Game()
