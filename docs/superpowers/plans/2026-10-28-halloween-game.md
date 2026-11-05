# Halloween — Ночная ночь с тыквами Implementation Plan

**Goal:** Создать завершённую локальную игру для двух игроков на Python 3 и Pygame.

**Architecture:** Чистая логика раунда и сущности отделены от Pygame-отрисовки. `main.py` владеет циклом, вводом и экранами; `game/renderer.py` рисует процедурные сцены и эффекты.

**Tech Stack:** Python 3.10+, Pygame, unittest.

**Spec:** Требования пользователя в чате от 2026-10-28.

## Global Constraints
- Запуск `python main.py`; зависимость описана в `requirements.txt`.
- Игра для двух игроков на одном компьютере, клавиши WASD и стрелки.
- Delta time для движения; графика полностью рисуется Pygame.
- Уровни, жизни, таймер, сбор, урон с неуязвимостью, меню, пауза, итог.

## Review Focus
- Клавиши обоих игроков одновременно должны обрабатываться в одном кадре; проверка в `test_player_movement_is_independent`.
- Объекты не должны порождаться внутри препятствий или у игроков; проверка в `test_spawn_candidates_respect_clearance`.
- Пауза не должна отнимать время; проверка в `test_pause_freezes_round_clock`.
- Урон не должен повторяться в окно неуязвимости; проверка в `test_ghost_hit_grants_invulnerability`.
- Нулевые жизни и истечение таймера должны корректно завершать раунд; проверка в `test_round_finishes_on_timeout_or_lives`.

### Task 1: Pure game rules
Создать `game/model.py` и `tests/test_game_model.py`; зафиксировать сбор, движение, урон, таймер, уровни и безопасное размещение.

### Task 2: Pygame renderer and effects
Создать `game/renderer.py` с фоном, лесной поляной, HUD, меню/паузы/итога и процедурными спрайтами.

### Task 3: App integration and docs
Создать `main.py`, `requirements.txt`, `README.md`; связать ввод, экраны, delta time и модель. Проверить импорты, тесты и headless запуск.
