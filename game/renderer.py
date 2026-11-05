"""Процедурная Pygame-графика ночной лесной поляны."""

import math
import random
import pygame
from pygame import gfxdraw


WIDTH, HEIGHT = 1280, 720
NIGHT = (10, 13, 34)


def _aa_circle(surface, color, center, radius):
    """Рисует заполненный круг с сглаженным контуром."""
    x, y = round(center[0]), round(center[1])
    radius = max(1, round(radius))
    gfxdraw.filled_circle(surface, x, y, radius, color)
    gfxdraw.aacircle(surface, x, y, radius, color)


def _aa_ellipse(surface, color, rect):
    """Сглаженная залитая эллиптическая форма."""
    x, y, width, height = (round(value) for value in rect)
    width, height = max(1, width), max(1, height)
    cx, cy = x + width // 2, y + height // 2
    rx, ry = max(1, width // 2), max(1, height // 2)
    gfxdraw.filled_ellipse(surface, cx, cy, rx, ry, color)
    gfxdraw.aaellipse(surface, cx, cy, rx, ry, color)


def _aa_polygon(surface, color, points):
    """Сглаженный многоугольник для силуэтов и деталей."""
    vertices = [(round(x), round(y)) for x, y in points]
    gfxdraw.filled_polygon(surface, vertices, color)
    gfxdraw.aapolygon(surface, vertices, color)


class Renderer:
    def __init__(self, surface: pygame.Surface):
        self.surface = surface
        self.font = pygame.font.SysFont("arial", 23, bold=True)
        self.small = pygame.font.SysFont("arial", 17)
        self.medium = pygame.font.SysFont("arial", 32, bold=True)
        self.title = pygame.font.SysFont("arial", 56, bold=True)
        rng = random.Random(29)
        self.stars = [(rng.randrange(WIDTH), rng.randrange(35, 500), rng.randrange(1, 3), rng.random() * 6.28) for _ in range(100)]
        self.tree_line = [(x, rng.randrange(35, 95), rng.randrange(40, 76)) for x in range(-20, WIDTH + 100, 74)]
        self.clouds = [(rng.randrange(WIDTH), rng.randrange(180, 560), rng.randrange(30, 130)) for _ in range(13)]

    def text(self, value: str, font: pygame.font.Font, color: tuple, center: tuple[int, int], shadow=True):
        if shadow:
            img = font.render(value, True, (5, 7, 18))
            self.surface.blit(img, img.get_rect(center=(center[0] + 2, center[1] + 3)))
        img = font.render(value, True, color)
        self.surface.blit(img, img.get_rect(center=center))

    def draw(self, model, screen: str, elapsed: float, menu_mode_index: int = 0):
        self._background(elapsed)
        if screen == "menu":
            self._menu(elapsed, menu_mode_index)
            return
        self._field(model, elapsed)
        self._hud(model)
        for pumpkin in model.pumpkins:
            self._pumpkin(pumpkin.x + 12, pumpkin.y + 12, elapsed)
        for ghost in model.ghosts:
            self._ghost(ghost.x, ghost.y + math.sin(ghost.phase) * 4, elapsed, ghost.phase)
        for player in model.active_players():
            self._player(player, elapsed)
        self._particles(model)
        if screen == "paused":
            self._overlay("Пауза", "P или Enter — продолжить    •    R — новый раунд", (157, 195, 255))
        elif screen == "level_complete":
            self._level_complete(model)
        elif screen == "round_over":
            self._round_over(model)

    def _background(self, elapsed):
        self.surface.fill(NIGHT)
        # Полосы цвета имитируют глубокий фиолетовый градиент ночного неба.
        for y in range(0, HEIGHT, 4):
            t = y / HEIGHT
            color = (int(10 + 12 * t), int(13 + 8 * t), int(34 + 20 * t))
            pygame.draw.rect(self.surface, color, (0, y, WIDTH, 4))
        for x, y, radius, phase in self.stars:
            glow = 110 + int(90 * (0.5 + 0.5 * math.sin(elapsed * 1.4 + phase)))
            _aa_circle(self.surface, (glow, glow, min(255, glow + 25)), (x, y), radius)
        # Луна и мягкий ореол.
        for radius, alpha in ((73, 14), (58, 20), (44, 255)):
            layer = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
            _aa_circle(layer, (255, 232, 173, alpha), (radius + 2, radius + 2), radius)
            self.surface.blit(layer, (1015 - radius, 105 - radius))
        _aa_circle(self.surface, (255, 240, 195), (1015, 105), 39)
        for cx, cy, width in self.clouds:
            color = (22, 27, 55)
            _aa_ellipse(self.surface, color, (cx, cy, width, 20))
            _aa_circle(self.surface, color, (cx + width // 3, cy), 14)
            _aa_circle(self.surface, color, (cx + width * 2 // 3, cy - 2), 18)
        # Силуэты елей и крыши домика.
        for x, top, height in self.tree_line:
            pygame.draw.rect(self.surface, (12, 18, 34), (x + 28, 90 - top + height, 10, 70))
            for tier in range(3):
                yy = 80 - top + tier * 28
                _aa_polygon(self.surface, (13, 20, 39), [(x, yy + 42), (x + 34, yy), (x + 68, yy + 42)])
        _aa_polygon(self.surface, (12, 17, 34), [(104, 300), (155, 255), (207, 300), (207, 356), (104, 356)])
        pygame.draw.rect(self.surface, (12, 17, 34), (121, 300, 70, 57))
        pygame.draw.rect(self.surface, (73, 60, 74), (145, 316, 15, 40))
        pygame.draw.rect(self.surface, (99, 83, 89), (119, 311, 14, 15))

    def _field(self, model, elapsed):
        pygame.draw.rect(self.surface, (18, 28, 48), (0, model.arena_top, WIDTH, HEIGHT - model.arena_top))
        _aa_ellipse(self.surface, (25, 39, 53), (-110, 300, 1500, 650))
        _aa_ellipse(self.surface, (27, 46, 55), (-30, 350, 1350, 620))
        pygame.draw.line(self.surface, (62, 74, 87), (0, model.arena_top), (WIDTH, model.arena_top), 2)
        for i, obstacle in enumerate(model.obstacles):
            shade = (43, 55, 62) if i % 2 else (39, 52, 61)
            _aa_ellipse(self.surface, (15, 23, 37), (obstacle.x - 12, obstacle.y + 20, obstacle.w + 24, 19))
            _aa_ellipse(self.surface, shade, (obstacle.x, obstacle.y, obstacle.w, obstacle.h))
            pygame.draw.arc(self.surface, (76, 87, 88), (obstacle.x + 8, obstacle.y + 5, obstacle.w - 16, obstacle.h - 8), 0.15, 2.6, 2)
        # Маленькие светлячки на поляне.
        for i in range(15):
            x = (i * 97 + int(elapsed * (8 + i % 5))) % WIDTH
            y = 190 + (i * 53) % 480 + int(math.sin(elapsed * 1.6 + i) * 8)
            _aa_circle(self.surface, (121, 204, 152), (x, y), 2)

    def _hud(self, model):
        panel = pygame.Surface((WIDTH, 102), pygame.SRCALPHA)
        panel.fill((5, 8, 24, 228))
        self.surface.blit(panel, (0, 0))
        pygame.draw.line(self.surface, (75, 92, 133), (0, 101), (WIDTH, 101), 2)
        self.text(f"ИГРОК 1   {model.players[0].score:02d}  тыкв", self.font, model.players[0].color, (205, 32))
        self.text("♥ " * model.players[0].lives, self.small, (255, 124, 151), (215, 72), False)
        self.text(f"УРОВЕНЬ {model.level}", self.medium, (255, 218, 145), (640, 30))
        seconds = int(math.ceil(model.time_left))
        timer_color = (255, 112, 121) if seconds <= 15 else (246, 239, 222)
        self.text(f"{seconds // 60:02d}:{seconds % 60:02d}", self.medium, timer_color, (640, 73))
        if model.mode == "solo":
            self.text("ОДИН ИГРОК", self.font, (190, 201, 225), (1065, 32))
            self.text("собирай и выживай", self.small, (145, 160, 191), (1065, 72), False)
        else:
            label = "БОТ" if model.mode == "bot" else "ИГРОК 2"
            self.text(f"{label}   {model.players[1].score:02d}  тыкв", self.font, model.players[1].color, (1065, 32))
            self.text("♥ " * model.players[1].lives, self.small, (255, 124, 151), (1065, 72), False)

    def _pumpkin(self, x, y, elapsed):
        pulse = 1 + 0.08 * math.sin(elapsed * 4 + x)
        radius = int(22 * pulse)
        glow = pygame.Surface((70, 70), pygame.SRCALPHA)
        _aa_circle(glow, (255, 133, 30, 36), (35, 35), radius + 8)
        _aa_circle(glow, (255, 175, 58, 30), (35, 35), radius)
        self.surface.blit(glow, (x - 35, y - 35))
        _aa_ellipse(self.surface, (206, 81, 26), (x - radius, y - radius * .68, radius * 2, radius * 1.36))
        _aa_ellipse(self.surface, (255, 135, 39), (x - radius * .64, y - radius * .65, radius * 1.28, radius * 1.3))
        _aa_ellipse(self.surface, (255, 171, 56), (x - radius * .22, y - radius * .72, radius * .44, radius * 1.35))
        pygame.draw.line(self.surface, (93, 107, 49), (x, y - radius * .55), (x + 2, y - radius - 5), 5)
        for ex in (-6, 6):
            _aa_polygon(self.surface, (255, 237, 161), [(x + ex, y - 4), (x + ex - 3, y + 2), (x + ex + 3, y + 2)])
        pygame.draw.arc(self.surface, (115, 42, 25), (x - 7, y, 14, 9), 3.2, 6.1, 2)

    def _ghost(self, x, y, elapsed, phase):
        bob = math.sin(elapsed * 4 + phase) * 2
        layer = pygame.Surface((76, 84), pygame.SRCALPHA)
        _aa_ellipse(layer, (161, 211, 255, 28), (4, 4, 68, 68))
        _aa_ellipse(layer, (153, 211, 255, 105), (13, 11, 50, 55))
        pygame.draw.rect(layer, (153, 211, 255, 105), (13, 38, 50, 25))
        _aa_circle(layer, (153, 211, 255, 105), (20, 61), 7)
        _aa_circle(layer, (153, 211, 255, 105), (38, 64), 7)
        _aa_circle(layer, (153, 211, 255, 105), (55, 61), 7)
        _aa_ellipse(layer, (13, 27, 55, 220), (25, 30, 5, 8))
        _aa_ellipse(layer, (13, 27, 55, 220), (45, 30, 5, 8))
        pygame.draw.arc(layer, (51, 67, 96, 220), (32, 38, 14, 10), 3.2, 6, 2)
        self.surface.blit(layer, (x - 38, y - 40 + bob))

    def _player(self, player, elapsed):
        if player.invulnerable > 0 and int(elapsed * 13) % 2:
            return
        x, y = int(player.x), int(player.y)
        glow = pygame.Surface((90, 90), pygame.SRCALPHA)
        _aa_circle(glow, (*player.color, 36), (45, 45), 39)
        self.surface.blit(glow, (x - 45, y - 45))
        _aa_ellipse(self.surface, (11, 17, 32), (x - 18, y + 11, 36, 12))
        _aa_circle(self.surface, player.color, (x, y), 17)
        _aa_circle(self.surface, (231, 246, 255), (x + 2, y - 2), 12)
        _aa_circle(self.surface, (42, 71, 103), (x + (4 if player.facing > 0 else -4), y), 7)
        _aa_circle(self.surface, (11, 21, 39), (x + (5 if player.facing > 0 else -5), y - 1), 3)
        pygame.draw.arc(self.surface, (player.color), (x - 12, y - 15, 24, 20), math.pi, math.tau, 3)
        _aa_circle(self.surface, (255, 255, 255), (x - 3, y - 6), 2)

    def _particles(self, model):
        for p in model.particles:
            alpha = max(0, min(255, int(255 * p["life"] / p["max"])))
            dot = pygame.Surface((8, 8), pygame.SRCALPHA)
            _aa_circle(dot, (*p["color"], alpha), (4, 4), 3)
            self.surface.blit(dot, (int(p["x"]), int(p["y"])))

    def _menu(self, elapsed, selected):
        # Декоративные герои и акцентная тыква делают стартовый экран самодостаточным.
        self._pumpkin(320, 390, elapsed)
        self._ghost(965, 390 + math.sin(elapsed * 2) * 7, elapsed, 1.4)
        self.text("HALLOWEEN", self.title, (255, 151, 55), (640, 132))
        self.text("Ночная ночь с тыквами", self.medium, (230, 226, 255), (640, 188))
        self.text("Выбери, с кем отправиться на лесную поляну", self.small, (173, 189, 220), (640, 230), False)
        options = [
            ("ОДНОМУ", "Только ты против", "призраков", "1"),
            ("С БОТОМ", "Соревнуйся с", "умным напарником", "2"),
            ("С ДРУГОМ", "Два игрока", "за одной клавиатурой", "3"),
        ]
        for index, (title, line1, line2, key) in enumerate(options):
            rect = pygame.Rect(150 + index * 340, 278, 300, 205)
            active = index == selected
            fill = (35, 42, 76) if active else (14, 20, 44)
            outline = (255, 197, 104) if active else (74, 86, 129)
            pygame.draw.rect(self.surface, fill, rect, border_radius=18)
            pygame.draw.rect(self.surface, outline, rect, 3 if active else 2, border_radius=18)
            self.text(f"[{key}]", self.small, (255, 219, 147) if active else (143, 158, 191), (rect.centerx, 310), False)
            self.text(title, self.medium, (255, 220, 146) if active else (222, 228, 246), (rect.centerx, 359))
            self.text(line1, self.small, (185, 197, 223), (rect.centerx, 408), False)
            self.text(line2, self.small, (185, 197, 223), (rect.centerx, 436), False)
        self.text("← → или 1 / 2 / 3 — выбрать     •     ENTER — играть", self.font, (238, 243, 255), (640, 532))
        self.text("Игрок 1: W A S D     •     Игрок 2: стрелки     •     P — пауза", self.small, (151, 164, 194), (640, 579), False)
        self.text("ESC — выход", self.small, (113, 125, 154), (640, 635), False)

    def _overlay(self, title, subtitle, color):
        veil = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        veil.fill((4, 7, 20, 178))
        self.surface.blit(veil, (0, 0))
        pygame.draw.rect(self.surface, (15, 21, 47), (270, 260, 740, 200), border_radius=24)
        pygame.draw.rect(self.surface, (81, 97, 145), (270, 260, 740, 200), 2, border_radius=24)
        self.text(title, self.title, color, (640, 326))
        self.text(subtitle, self.font, (223, 229, 245), (640, 397), False)

    def _level_complete(self, model):
        title = f"Уровень {model.level} пройден!"
        subtitle = "ENTER — следующий уровень    •    R — начать заново    •    ESC — меню"
        self._overlay(title, subtitle, (255, 211, 123))
        if model.mode == "solo":
            scores = f"Твои тыквы: {model.players[0].score}"
        else:
            second = "Бот" if model.mode == "bot" else "Игрок 2"
            scores = f"Игрок 1: {model.players[0].score}       {second}: {model.players[1].score}"
        self.text(scores, self.font, (231, 237, 255), (640, 455), False)

    def _round_over(self, model):
        self._overlay(model.winner_text(), "ENTER — сыграть ещё раз    •    R — новый раунд    •    ESC — меню", (255, 190, 104))
        if model.mode == "solo":
            scores = f"Собрано тыкв: {model.players[0].score}"
        else:
            second = "БОТ" if model.mode == "bot" else "ИГРОК 2"
            scores = f"ИГРОК 1   {model.players[0].score} тыкв     ·     {second}   {model.players[1].score} тыкв"
        self.text(scores, self.font, (231, 237, 255), (640, 455), False)
