"""Чистая игровая модель, не зависящая от Pygame."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class Rect:
    x: float
    y: float
    w: float
    h: float

    def colliderect(self, other: "Rect") -> bool:
        return self.x < other.x + other.w and self.x + self.w > other.x and self.y < other.y + other.h and self.y + self.h > other.y


@dataclass
class Player:
    x: float
    y: float
    color: tuple[int, int, int] = (92, 220, 255)
    score: int = 0
    lives: int = 3
    radius: int = 17
    invulnerable: float = 0.0
    facing: int = 1


@dataclass
class Ghost:
    x: float
    y: float
    speed: float
    phase: float = 0.0
    radius: int = 19


def safe_spawn(width: int, height: int, obstacles: list[Rect], occupied: list[Rect], seed: int | None = None) -> tuple[int, int] | None:
    """Находит свободную точку внутри поля с небольшим отступом."""
    rng = random.Random(seed)
    for _ in range(300):
        x = rng.randint(44, width - 68)
        y = rng.randint(125, height - 56)
        candidate = Rect(x, y, 24, 24)
        if not any(candidate.colliderect(Rect(o.x - 18, o.y - 18, o.w + 36, o.h + 36)) for o in obstacles + occupied):
            return x, y
    return None


class GameModel:
    width = 1280
    height = 720
    arena_top = 112
    target_pumpkins = 8
    level_count = 15
    level_duration = 90.0

    def __init__(self, seed: int | None = None, mode: str = "friend"):
        if mode not in ("solo", "bot", "friend"):
            raise ValueError("mode must be 'solo', 'bot' or 'friend'")
        self.rng = random.Random(seed)
        self.mode = mode
        self.level = 1
        self.paused = False
        self.state = "playing"
        self.time_left = self.level_duration
        self.players = [Player(145, 390, (87, 220, 255)), Player(1135, 390, (255, 116, 198))]
        self.obstacles: list[Rect] = []
        self._make_obstacles()
        self.ghosts: list[Ghost] = []
        self.pumpkins: list[Rect] = []
        self.particles: list[dict] = []
        self.shake = 0.0
        self._make_ghosts()
        self._fill_pumpkins()

    def active_players(self) -> list[Player]:
        """Возвращает игроков, участвующих в текущем режиме."""
        return self.players[:1] if self.mode == "solo" else self.players

    def bot_direction(self) -> tuple[float, float]:
        """Выбирает безопасное направление к ближайшей тыкве для игрока-бота."""
        bot = self.players[1]
        if not self.pumpkins:
            return 0.0, 0.0
        target = min(self.pumpkins, key=lambda p: math.hypot(p.x + p.w / 2 - bot.x, p.y + p.h / 2 - bot.y))
        tx, ty = target.x + target.w / 2, target.y + target.h / 2
        headings = [(tx - bot.x, ty - bot.y)] + [
            (math.cos(angle), math.sin(angle)) for angle in (0, math.pi / 4, math.pi / 2, 3 * math.pi / 4,
                                                              math.pi, 5 * math.pi / 4, 3 * math.pi / 2, 7 * math.pi / 4)
        ]
        best, best_cost = (0.0, 0.0), math.inf
        for dx, dy in headings:
            length = math.hypot(dx, dy)
            if length == 0:
                continue
            dx, dy = dx / length, dy / length
            nx, ny = bot.x + dx * 34, bot.y + dy * 34
            if self._hits_obstacle(nx, ny, bot.radius):
                continue
            cost = math.hypot(tx - nx, ty - ny)
            for ghost in self.ghosts:
                gap = math.hypot(ghost.x - nx, ghost.y - ny)
                if gap < 92:
                    cost += (92 - gap) * 2.5
            if cost < best_cost:
                best, best_cost = (dx, dy), cost
        return best

    def _make_obstacles(self) -> None:
        layouts = [
            [(360, 245, 95, 45), (825, 390, 110, 48), (600, 530, 76, 40)],
            [(300, 350, 120, 48), (560, 220, 95, 44), (890, 310, 115, 44), (680, 540, 88, 45)],
            [(330, 235, 95, 48), (500, 410, 112, 45), (820, 240, 100, 48), (930, 480, 100, 48), (690, 570, 85, 40)],
            [(270, 260, 100, 42), (490, 355, 110, 50), (740, 250, 102, 48), (960, 410, 100, 46)],
            [(285, 475, 115, 44), (465, 230, 88, 46), (695, 390, 125, 48), (930, 250, 92, 44), (870, 555, 95, 42)],
            [(265, 330, 90, 48), (430, 500, 110, 42), (565, 235, 120, 46), (810, 345, 90, 48), (990, 510, 90, 42)],
            [(310, 230, 105, 44), (360, 490, 95, 45), (620, 340, 100, 50), (850, 220, 110, 45), (900, 505, 105, 44)],
            [(280, 400, 120, 45), (495, 260, 88, 44), (550, 540, 100, 45), (770, 390, 118, 48), (965, 250, 95, 44)],
            [(310, 280, 92, 45), (410, 430, 120, 46), (650, 220, 110, 48), (780, 500, 95, 42), (970, 360, 105, 48)],
            [(285, 525, 100, 42), (390, 260, 112, 48), (625, 410, 94, 45), (820, 245, 118, 45), (935, 535, 100, 44)],
            [(300, 350, 115, 45), (465, 215, 92, 46), (515, 530, 105, 44), (760, 335, 112, 48), (950, 220, 95, 45), (900, 510, 94, 42)],
            [(275, 225, 108, 46), (360, 470, 100, 44), (600, 310, 112, 48), (700, 535, 95, 42), (910, 300, 118, 46), (1000, 490, 90, 42)],
            [(300, 420, 105, 44), (420, 230, 95, 46), (575, 510, 116, 44), (680, 260, 108, 46), (850, 410, 100, 48), (970, 230, 94, 42)],
            [(280, 315, 118, 48), (390, 520, 92, 42), (530, 225, 110, 45), (620, 420, 96, 48), (820, 250, 112, 44), (925, 500, 105, 44)],
            [(295, 235, 100, 45), (360, 405, 105, 48), (480, 540, 95, 42), (610, 310, 118, 48), (770, 500, 100, 45), (840, 220, 112, 44), (985, 355, 98, 46)],
        ]
        self.obstacles = [Rect(*item) for item in layouts[min(self.level - 1, len(layouts) - 1)]]

    def _make_ghosts(self) -> None:
        self.ghosts = []
        occupied = [Rect(p.x - 55, p.y - 55, 110, 110) for p in self.players]
        for i in range(3 + self.level):
            point = safe_spawn(self.width, self.height, self.obstacles, occupied, self.rng.randrange(1 << 30))
            x, y = point or (self.rng.randint(230, self.width - 230), self.rng.randint(160, self.height - 140))
            ghost = Ghost(x, y, 62 + self.level * 10 + i * 2, self.rng.random() * math.tau)
            self.ghosts.append(ghost)
            occupied.append(Rect(x - 40, y - 40, 80, 80))

    def _fill_pumpkins(self) -> None:
        self.pumpkins = []
        for _ in range(self.target_pumpkins):
            self.spawn_pumpkin()

    def spawn_pumpkin(self) -> None:
        player_rects = [Rect(p.x - 48, p.y - 48, 96, 96) for p in self.players]
        occupied = self.pumpkins + player_rects
        point = safe_spawn(self.width, self.height, self.obstacles, occupied, self.rng.randrange(1 << 30))
        if point:
            self.pumpkins.append(Rect(point[0], point[1], 24, 24))

    def move_players(self, directions: dict[str, tuple[float, float]], dt: float) -> None:
        dt = min(max(dt, 0.0), 0.05)
        for key, player in zip(("p1", "p2"), self.players):
            dx, dy = directions.get(key, (0.0, 0.0))
            length = math.hypot(dx, dy)
            if length:
                dx, dy = dx / length, dy / length
                player.facing = 1 if dx >= 0 else -1
            speed = 245
            nx = min(max(player.x + dx * speed * dt, player.radius + 6), self.width - player.radius - 6)
            ny = min(max(player.y + dy * speed * dt, self.arena_top + player.radius + 5), self.height - player.radius - 8)
            # Раздельная проверка осей даёт скольжение вдоль препятствий.
            if not self._hits_obstacle(nx, player.y, player.radius):
                player.x = nx
            if not self._hits_obstacle(player.x, ny, player.radius):
                player.y = ny

    def _hits_obstacle(self, x: float, y: float, radius: int) -> bool:
        return any(Rect(x - radius, y - radius, radius * 2, radius * 2).colliderect(o) for o in self.obstacles)

    def update(self, dt: float) -> None:
        if self.state != "playing" or self.paused:
            return
        elapsed = max(dt, 0.0)
        dt = min(elapsed, 0.05)
        self.time_left = max(0.0, self.time_left - elapsed)
        for player in self.players:
            player.invulnerable = max(0.0, player.invulnerable - dt)
        self._update_ghosts(dt)
        self._collect_pumpkins()
        self._update_particles(dt)
        self.shake = max(0.0, self.shake - dt)
        if self.time_left <= 0:
            self.state = "round_over"

    def _update_ghosts(self, dt: float) -> None:
        players = self.active_players()
        for ghost in self.ghosts:
            target = min(players, key=lambda p: math.hypot(p.x - ghost.x, p.y - ghost.y))
            dx, dy = target.x - ghost.x, target.y - ghost.y
            distance = max(1.0, math.hypot(dx, dy))
            ghost.phase += dt * 3.0
            speed = ghost.speed * (0.55 if distance < 65 else 1.0)
            nx = ghost.x + dx / distance * speed * dt + math.sin(ghost.phase) * 9 * dt
            ny = ghost.y + dy / distance * speed * dt + math.cos(ghost.phase * 0.8) * 9 * dt
            if not self._hits_obstacle(nx, ghost.y, ghost.radius):
                ghost.x = min(max(nx, ghost.radius + 8), self.width - ghost.radius - 8)
            if not self._hits_obstacle(ghost.x, ny, ghost.radius):
                ghost.y = min(max(ny, self.arena_top + ghost.radius + 5), self.height - ghost.radius - 8)
            for player in players:
                if player.invulnerable <= 0 and math.hypot(player.x - ghost.x, player.y - ghost.y) < player.radius + ghost.radius - 3:
                    player.lives -= 1
                    player.invulnerable = 1.6
                    self.shake = 0.22
                    self._burst(player.x, player.y, (255, 93, 122), 14)
                    ghost.x, ghost.y = self.rng.choice([(230, 180), (1050, 190), (650, 590), (1040, 570)])
                    if player.lives <= 0:
                        self.state = "round_over"

    def _collect_pumpkins(self) -> None:
        for player in self.active_players():
            for pumpkin in self.pumpkins[:]:
                if math.hypot(player.x - (pumpkin.x + 12), player.y - (pumpkin.y + 12)) < player.radius + 13:
                    player.score += 1
                    self.pumpkins.remove(pumpkin)
                    self._burst(pumpkin.x + 12, pumpkin.y + 12, (255, 174, 57), 12)
                    self.spawn_pumpkin()
                    if player.score >= self.level * self.target_pumpkins:
                        self.state = "level_complete"
                        return

    def _burst(self, x: float, y: float, color: tuple[int, int, int], count: int) -> None:
        for _ in range(count):
            angle = self.rng.random() * math.tau
            speed = self.rng.uniform(25, 150)
            self.particles.append({"x": x, "y": y, "vx": math.cos(angle) * speed, "vy": math.sin(angle) * speed, "life": self.rng.uniform(0.25, 0.75), "max": 0.75, "color": color})

    def _update_particles(self, dt: float) -> None:
        for particle in self.particles:
            particle["x"] += particle["vx"] * dt
            particle["y"] += particle["vy"] * dt
            particle["life"] -= dt
        self.particles = [p for p in self.particles if p["life"] > 0]

    def next_level(self) -> None:
        if self.state != "level_complete":
            return
        if self.level >= self.level_count:
            self.state = "round_over"
            return
        self.level += 1
        self.time_left = self.level_duration
        self._make_obstacles()
        self._make_ghosts()
        self._fill_pumpkins()
        for player, position in zip(self.players, ((145, 390), (1135, 390))):
            player.x, player.y = position
            player.lives = min(3, player.lives + 1)
        self.state = "playing"

    def restart(self) -> None:
        seed = self.rng.randrange(1 << 30)
        self.__init__(seed, self.mode)

    def winner_text(self) -> str:
        if self.mode == "solo":
            return "Отличная охота!"
        if self.players[0].score == self.players[1].score:
            return "Ничья!"
        winner = 1 if self.players[0].score > self.players[1].score else 2
        return f"Победил игрок {winner}!"
