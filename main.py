"""Запуск игры Halloween — Ночная ночь с тыквами."""

try:
    import pygame
except ImportError as error:
    raise SystemExit("Не найдена Pygame. Установите зависимости командой: python -m pip install -r requirements.txt") from error

from game.model import GameModel
from game.renderer import HEIGHT, WIDTH, Renderer

PLAY_MODES = ("solo", "bot", "friend")


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Halloween — Ночная ночь с тыквами")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    renderer = Renderer(screen)
    game = GameModel()
    screen_state = "menu"
    menu_mode_index = 0
    elapsed = 0.0
    running = True

    while running:
        dt = clock.tick(60) / 1000.0
        elapsed += dt
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and screen_state == "menu" and event.button == 1:
                x, y = event.pos
                if 278 <= y <= 483:
                    option = (x - 150) // 340
                    if 0 <= option < len(PLAY_MODES) and 150 + option * 340 <= x <= 450 + option * 340:
                        menu_mode_index = option
                        game = GameModel(mode=PLAY_MODES[menu_mode_index])
                        screen_state = "playing"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if screen_state == "menu":
                        running = False
                    else:
                        screen_state = "menu"
                        game.paused = False
                elif event.key == pygame.K_RETURN:
                    if screen_state == "menu":
                        game = GameModel(mode=PLAY_MODES[menu_mode_index])
                        screen_state = "playing"
                    elif screen_state == "paused":
                        game.paused = False
                        screen_state = "playing"
                    elif screen_state == "level_complete":
                        game.next_level()
                        screen_state = "round_over" if game.state == "round_over" else "playing"
                    elif screen_state == "round_over":
                        game.restart()
                        screen_state = "playing"
                elif event.key == pygame.K_p and screen_state in ("playing", "paused"):
                    game.paused = not game.paused
                    screen_state = "paused" if game.paused else "playing"
                elif event.key == pygame.K_r and screen_state != "menu":
                    game.restart()
                    screen_state = "playing"
                elif screen_state == "menu":
                    if event.key in (pygame.K_LEFT, pygame.K_UP):
                        menu_mode_index = (menu_mode_index - 1) % len(PLAY_MODES)
                    elif event.key in (pygame.K_RIGHT, pygame.K_DOWN):
                        menu_mode_index = (menu_mode_index + 1) % len(PLAY_MODES)
                    elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3):
                        menu_mode_index = event.key - pygame.K_1

        if screen_state == "playing":
            keys = pygame.key.get_pressed()
            directions = {
                "p1": (float(keys[pygame.K_d]) - float(keys[pygame.K_a]), float(keys[pygame.K_s]) - float(keys[pygame.K_w])),
                "p2": (float(keys[pygame.K_RIGHT]) - float(keys[pygame.K_LEFT]), float(keys[pygame.K_DOWN]) - float(keys[pygame.K_UP])),
            }
            if game.mode == "bot":
                directions["p2"] = game.bot_direction()
            elif game.mode == "solo":
                directions["p2"] = (0.0, 0.0)
            game.move_players(directions, dt)
            game.update(dt)
            if game.state == "level_complete":
                screen_state = "level_complete"
            elif game.state == "round_over":
                screen_state = "round_over"

        renderer.draw(game, screen_state, elapsed, menu_mode_index)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
