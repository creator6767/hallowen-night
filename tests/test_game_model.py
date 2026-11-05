import unittest

from game.model import GameModel, Player, Rect, safe_spawn


class GameModelTests(unittest.TestCase):
    def test_player_movement_is_independent_and_clamped(self):
        game = GameModel(seed=3)
        game.players = [Player(100, 100), Player(900, 600)]
        game.move_players({"p1": (1, 0), "p2": (-1, 0)}, 1.0)
        self.assertGreater(game.players[0].x, 100)
        self.assertLess(game.players[1].x, 900)
        game.move_players({"p1": (-1, -1), "p2": (1, 1)}, 20.0)
        for player in game.players:
            self.assertTrue(30 <= player.x <= game.width - 30)
            self.assertTrue(105 <= player.y <= game.height - 30)

    def test_ghost_hit_grants_invulnerability(self):
        game = GameModel(seed=4)
        player = game.players[0]
        player.x, player.y = 300, 250
        game.ghosts[0].x, game.ghosts[0].y = 300, 250
        game.update(0.016)
        self.assertEqual(player.lives, 2)
        game.update(0.016)
        self.assertEqual(player.lives, 2)

    def test_pause_freezes_round_clock(self):
        game = GameModel(seed=5)
        before = game.time_left
        game.paused = True
        game.update(3.0)
        self.assertEqual(game.time_left, before)

    def test_collecting_target_finishes_level_and_tie_is_draw(self):
        game = GameModel(seed=6)
        game.target_pumpkins = 1
        game.pumpkins = [Rect(game.players[0].x, game.players[0].y, 25, 25)]
        game.update(0.016)
        self.assertEqual(game.state, "level_complete")
        game.players[1].score = game.players[0].score
        self.assertEqual(game.winner_text(), "Ничья!")

    def test_spawn_candidates_respect_clearance(self):
        blocked = [Rect(90, 90, 40, 40)]
        spot = safe_spawn(200, 200, blocked, [Rect(180, 180, 30, 30)], seed=9)
        self.assertIsNotNone(spot)
        x, y = spot
        self.assertFalse(Rect(x, y, 24, 24).colliderect(blocked[0]))
        self.assertFalse(Rect(x, y, 24, 24).colliderect(Rect(180, 180, 30, 30)))

    def test_round_ends_when_timer_expires(self):
        game = GameModel(seed=7)
        game.update(game.time_left + 1)
        self.assertEqual(game.state, "round_over")

    def test_solo_mode_disables_the_second_player(self):
        game = GameModel(seed=8, mode="solo")
        player2 = game.players[1]
        game.ghosts[0].x, game.ghosts[0].y = player2.x, player2.y
        game.pumpkins = [Rect(player2.x, player2.y, 24, 24)]
        game.update(0.016)
        self.assertEqual(len(game.active_players()), 1)
        self.assertEqual(player2.lives, 3)
        self.assertEqual(player2.score, 0)

    def test_bot_moves_toward_a_nearby_pumpkin(self):
        game = GameModel(seed=10, mode="bot")
        bot = game.players[1]
        game.ghosts = []
        game.pumpkins = [Rect(bot.x + 100, bot.y - 12, 24, 24)]
        dx, dy = game.bot_direction()
        self.assertGreater(dx, 0)
        self.assertEqual(dy, 0)

    def test_game_has_fifteen_levels_and_finishes_after_the_last(self):
        game = GameModel(seed=12, mode="solo")
        self.assertEqual(game.level_count, 15)
        for _ in range(14):
            game.state = "level_complete"
            game.next_level()
        self.assertEqual(game.level, 15)
        self.assertEqual(game.state, "playing")
        game.state = "level_complete"
        game.next_level()
        self.assertEqual(game.state, "round_over")

    def test_level_layout_and_ghost_difficulty_progress(self):
        game = GameModel(seed=13)
        first_layout = [(o.x, o.y, o.w, o.h) for o in game.obstacles]
        first_ghost_speed = game.ghosts[0].speed
        game.level = 4
        game._make_obstacles()
        game._make_ghosts()
        self.assertNotEqual([(o.x, o.y, o.w, o.h) for o in game.obstacles], first_layout)
        self.assertGreater(game.ghosts[0].speed, first_ghost_speed)
        layouts = set()
        for level in range(1, game.level_count + 1):
            game.level = level
            game._make_obstacles()
            layouts.add(tuple((o.x, o.y, o.w, o.h) for o in game.obstacles))
        self.assertEqual(len(layouts), 15)


if __name__ == "__main__":
    unittest.main()
