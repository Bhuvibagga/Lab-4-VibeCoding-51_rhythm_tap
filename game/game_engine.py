import pygame
import random
import math
import struct

from game.beat import (
    Note,
    LANES,
    LANE_KEYS,
    LANE_LABELS,
    LANE_COLORS
)

WIDTH, HEIGHT = 480, 640
FPS = 60
HIT_Y = HEIGHT - 80
HIT_WINDOW = 30
BG = (15, 10, 25)
LANE_W = WIDTH // LANES

# Task 3: BPM settings
BPM = 120
BEAT_INTERVAL = 60.0 / BPM


class GameEngine:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()

        # Task 1: Sound effects
        self.hit_sounds = {
            "PERFECT": self.create_tone(880, 0.08),
            "GREAT": self.create_tone(660, 0.08),
            "OK": self.create_tone(440, 0.08),
        }

        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Rhythm Tap")
        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont(
            "monospace",
            26,
            bold=True
        )

        self.big_font = pygame.font.SysFont(
            "monospace",
            44,
            bold=True
        )

        self.reset()

    def create_tone(self, frequency, duration):
        sample_rate = 44100
        samples = int(sample_rate * duration)
        buffer = bytearray()

        for i in range(samples):
            value = int(
                32767
                * 0.25
                * math.sin(
                    2 * math.pi * frequency * i / sample_rate
                )
            )

            buffer.extend(
                struct.pack("<h", value)
            )

        return pygame.mixer.Sound(
            buffer=bytes(buffer)
        )

    def reset(self):
        self.notes = []
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.misses = 0

        # Task 4: Grade counters
        self.perfect_count = 0
        self.great_count = 0
        self.ok_count = 0
        self.miss_count = 0

        # Task 3: BPM timing
        self.song_start_time = pygame.time.get_ticks()
        self.last_beat = -1

        self.speed = 5
        self.frame = 0
        self.feedback = []
        self.game_over = False

    def spawn_note(self):
        lane = random.randint(0, LANES - 1)

        # Task 2: Occasionally create a hold note
        is_hold = random.random() < 0.25

        self.notes.append(
            Note(
                lane,
                y=-30,
                speed=self.speed,
                is_hold=is_hold
            )
        )

    def handle_events(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_r:
                    self.reset()

                elif not self.game_over:

                    for i, key in enumerate(LANE_KEYS):

                        if event.key == key:
                            self.process_tap(i)

        return True

    def process_tap(self, lane):

        best = None
        best_dist = 9999

        for note in self.notes:

            if (
                note.lane == lane
                and not note.hit
                and not note.missed
            ):

                dist = abs(
                    note.y
                    + Note.HEIGHT // 2
                    - HIT_Y
                )

                if dist < best_dist:
                    best_dist = dist
                    best = note

        lane_x = (
            lane * LANE_W
            + LANE_W // 2
        )

        if best and best_dist <= HIT_WINDOW:

            # Task 2: Start hold note
            if best.is_hold:

                best.hold_started = True
                best.hold_start_time = pygame.time.get_ticks()

                self.feedback.append(
                    [
                        "HOLD...",
                        (150, 220, 255),
                        40,
                        lane_x,
                        HIT_Y - 30
                    ]
                )

            else:

                best.hit = True

                # Determine grade
                if best_dist < 8:
                    grade, pts = "PERFECT", 300
                    col = (255, 220, 0)

                elif best_dist < 18:
                    grade, pts = "GREAT", 200
                    col = (100, 220, 100)

                else:
                    grade, pts = "OK", 100
                    col = (180, 180, 255)

                # Task 4: Count grades
                if grade == "PERFECT":
                    self.perfect_count += 1

                elif grade == "GREAT":
                    self.great_count += 1

                else:
                    self.ok_count += 1

                # Task 1: Play sound
                self.hit_sounds[grade].play()

                self.combo += 1

                self.max_combo = max(
                    self.max_combo,
                    self.combo
                )

                self.score += (
                    pts
                    * max(1, self.combo // 5)
                )

                self.feedback.append(
                    [
                        grade,
                        col,
                        40,
                        lane_x,
                        HIT_Y - 30
                    ]
                )

        else:

            # Wrong key / missed tap
            self.combo = 0
            self.misses += 1
            self.miss_count += 1

            self.feedback.append(
                [
                    "MISS",
                    (220, 60, 60),
                    40,
                    lane_x,
                    HIT_Y - 30
                ]
            )

    def update(self):

        if self.game_over:
            return

        self.frame += 1

        # ==========================================
        # Task 3: BPM-synchronized spawning
        # ==========================================

        current_time = pygame.time.get_ticks()

        elapsed = (
            current_time - self.song_start_time
        ) / 1000.0

        current_beat = int(
            elapsed / BEAT_INTERVAL
        )

        if current_beat > self.last_beat:

            for beat in range(
                self.last_beat + 1,
                current_beat + 1
            ):
                self.spawn_note()

            self.last_beat = current_beat

        # Increase speed without changing BPM
        if self.frame % 600 == 0:

            self.speed = min(
                10,
                self.speed + 0.5
            )

        keys = pygame.key.get_pressed()

        for note in self.notes:

            note.update()

            # ==========================================
            # Task 2: Hold note handling
            # ==========================================

            if note.is_hold and note.hold_started:

                key = LANE_KEYS[note.lane]

                if not keys[key]:

                    note.missed = True
                    self.combo = 0
                    self.misses += 1
                    self.miss_count += 1

                    self.feedback.append(
                        [
                            "MISS",
                            (220, 60, 60),
                            40,
                            note.lane * LANE_W
                            + LANE_W // 2,
                            HIT_Y - 30
                        ]
                    )

                else:

                    elapsed_hold = (
                        pygame.time.get_ticks()
                        - note.hold_start_time
                    ) / 1000.0

                    if elapsed_hold >= note.hold_duration:

                        note.hit = True

                        self.hit_sounds[
                            "PERFECT"
                        ].play()

                        self.perfect_count += 1

                        self.combo += 1

                        self.max_combo = max(
                            self.max_combo,
                            self.combo
                        )

                        self.score += (
                            300
                            * max(
                                1,
                                self.combo // 5
                            )
                        )

                        self.feedback.append(
                            [
                                "HOLD PERFECT",
                                (255, 220, 0),
                                40,
                                note.lane * LANE_W
                                + LANE_W // 2,
                                HIT_Y - 30
                            ]
                        )

            # ==========================================
            # Normal note missed
            # ==========================================

            if (
                not note.hit
                and not note.missed
                and not note.is_hold
                and note.y
                > HIT_Y
                + HIT_WINDOW
                + Note.HEIGHT
            ):

                note.missed = True
                self.misses += 1
                self.miss_count += 1
                self.combo = 0

            # ==========================================
            # Hold note missed before being started
            # ==========================================

            if (
                note.is_hold
                and not note.hit
                and not note.missed
                and not note.hold_started
                and note.y
                > HIT_Y
                + HIT_WINDOW
                + Note.HEIGHT
            ):

                note.missed = True
                self.misses += 1
                self.miss_count += 1
                self.combo = 0

        self.notes = [
            n
            for n in self.notes
            if not (
                n.hit
                or (
                    n.missed
                    and n.y > HEIGHT + 10
                )
            )
        ]

        self.feedback = [
            [t, c, ttl - 1, x, y]
            for t, c, ttl, x, y in self.feedback
            if ttl > 1
        ]

        if self.misses >= 15:
            self.game_over = True

    def draw(self):

        self.screen.fill(BG)

        # Lane dividers
        for i in range(LANES + 1):

            pygame.draw.line(
                self.screen,
                (40, 40, 60),
                (i * LANE_W, 0),
                (i * LANE_W, HEIGHT),
                1
            )

        # Hit line
        pygame.draw.line(
            self.screen,
            (80, 80, 100),
            (0, HIT_Y),
            (WIDTH, HIT_Y),
            2
        )

        for i in range(LANES):

            lx = (
                i * LANE_W
                + LANE_W // 2
            )

            pygame.draw.rect(
                self.screen,
                LANE_COLORS[i],
                pygame.Rect(
                    lx - Note.WIDTH // 2,
                    HIT_Y - 12,
                    Note.WIDTH,
                    24
                ),
                border_radius=6
            )

            lbl = self.font.render(
                LANE_LABELS[i],
                True,
                (20, 20, 20)
            )

            self.screen.blit(
                lbl,
                (
                    lx - lbl.get_width() // 2,
                    HIT_Y - 10
                )
            )

        # Notes
        for note in self.notes:

            if note.hit:
                continue

            lx = (
                note.lane * LANE_W
                + LANE_W // 2
            )

            rect = note.get_rect(lx)

            pygame.draw.rect(
                self.screen,
                LANE_COLORS[note.lane],
                rect,
                border_radius=5
            )

        # Feedback
        for text, color, ttl, x, y in self.feedback:

            surf = self.font.render(
                text,
                True,
                color
            )

            alpha = min(
                255,
                ttl * 7
            )

            surf.set_alpha(alpha)

            self.screen.blit(
                surf,
                (
                    x - surf.get_width() // 2,
                    y
                )
            )

        # HUD
        sc = self.font.render(
            f"Score: {self.score}",
            True,
            (220, 220, 220)
        )

        co = self.font.render(
            f"Combo: {self.combo}x",
            True,
            (255, 220, 80)
        )

        mi = self.font.render(
            f"Misses: {self.misses}/15",
            True,
            (220, 100, 100)
        )

        self.screen.blit(sc, (10, 10))
        self.screen.blit(co, (10, 40))
        self.screen.blit(
            mi,
            (WIDTH - 170, 10)
        )

        # ==========================================
        # Task 4: Grade Summary Screen
        # ==========================================

        if self.game_over:

            total_judged = (
                self.perfect_count
                + self.great_count
                + self.ok_count
                + self.miss_count
            )

            accuracy = (
                (
                    self.perfect_count * 1.0
                    + self.great_count * 0.75
                    + self.ok_count * 0.5
                )
                / total_judged
                * 100
                if total_judged > 0
                else 0
            )

            # Dark overlay
            ov = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA
            )

            ov.fill(
                (0, 0, 0, 200)
            )

            self.screen.blit(
                ov,
                (0, 0)
            )

            # Game Over
            msg = self.big_font.render(
                "GAME OVER",
                True,
                (220, 60, 60)
            )

            self.screen.blit(
                msg,
                (
                    WIDTH // 2
                    - msg.get_width() // 2,
                    55
                )
            )

            # Summary title
            summary_title = self.font.render(
                "GRADE SUMMARY",
                True,
                (255, 255, 255)
            )

            self.screen.blit(
                summary_title,
                (
                    WIDTH // 2
                    - summary_title.get_width() // 2,
                    115
                )
            )

            # Grade counts
            perfect = self.font.render(
                f"PERFECT: {self.perfect_count}",
                True,
                (255, 220, 0)
            )

            great = self.font.render(
                f"GREAT: {self.great_count}",
                True,
                (100, 220, 100)
            )

            ok = self.font.render(
                f"OK: {self.ok_count}",
                True,
                (180, 180, 255)
            )

            miss = self.font.render(
                f"MISS: {self.miss_count}",
                True,
                (220, 60, 60)
            )

            accuracy_text = self.font.render(
                f"Accuracy: {accuracy:.1f}%",
                True,
                (255, 255, 255)
            )

            self.screen.blit(
                perfect,
                (
                    WIDTH // 2
                    - perfect.get_width() // 2,
                    165
                )
            )

            self.screen.blit(
                great,
                (
                    WIDTH // 2
                    - great.get_width() // 2,
                    205
                )
            )

            self.screen.blit(
                ok,
                (
                    WIDTH // 2
                    - ok.get_width() // 2,
                    245
                )
            )

            self.screen.blit(
                miss,
                (
                    WIDTH // 2
                    - miss.get_width() // 2,
                    285
                )
            )

            self.screen.blit(
                accuracy_text,
                (
                    WIDTH // 2
                    - accuracy_text.get_width() // 2,
                    345
                )
            )

            # Final score
            sc_msg = self.font.render(
                f"Final Score: {self.score}",
                True,
                (200, 200, 200)
            )

            self.screen.blit(
                sc_msg,
                (
                    WIDTH // 2
                    - sc_msg.get_width() // 2,
                    400
                )
            )

            # Max combo
            max_combo_msg = self.font.render(
                f"Max Combo: {self.max_combo}x",
                True,
                (200, 200, 200)
            )

            self.screen.blit(
                max_combo_msg,
                (
                    WIDTH // 2
                    - max_combo_msg.get_width() // 2,
                    435
                )
            )

            # Restart
            restart = self.font.render(
                "Press R to Restart",
                True,
                (160, 160, 160)
            )

            self.screen.blit(
                restart,
                (
                    WIDTH // 2
                    - restart.get_width() // 2,
                    500
                )
            )

        pygame.display.flip()

    def run(self):

        running = True

        while running:

            running = self.handle_events()
            self.update()
            self.draw()

            self.clock.tick(FPS)

        pygame.quit()