"""
TSIS 3 — Racer X: Advanced Driving
Entry point and game state machine.

States: main_menu → username → playing → game_over
        main_menu → leaderboard → main_menu
        main_menu → settings    → main_menu
"""

import pygame
import sys

from persistence import (load_settings, save_settings,
                          load_leaderboard, add_leaderboard_entry)
from racer import GameWorld, SCREEN_W, SCREEN_H
from ui   import (MainMenu, SettingsScreen, LeaderboardScreen,
                  GameOverScreen, UsernameScreen, HUD)

FPS = 60


def main():
    pygame.init()
    pygame.display.set_caption("Racer Game")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock  = pygame.time.Clock()

    # ── load persistent state ─────────────────────────────────────────────
    settings    = load_settings()
    leaderboard = load_leaderboard()

    # ── state ─────────────────────────────────────────────────────────────
    state    = "main_menu"
    username = "PLAYER"
    world    = None
    hud      = HUD()

    menu_screen   = MainMenu()
    set_screen    = None
    lb_screen     = None
    over_screen   = None
    user_screen   = None



    pygame.mixer.init()

    crash_sound = pygame.mixer.Sound("assets/crash.wav")
    def start_game():
        nonlocal world
        world = GameWorld(
            difficulty=settings.get("difficulty", "medium"),
            car_color =settings.get("car_color",  "red"),
            sound     =settings.get("sound",       True),
        )

    # ── main loop ─────────────────────────────────────────────────────────
    while True:
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                if state == "playing":
                    state = "main_menu"
                    menu_screen = MainMenu()

        # ── STATE: main_menu ─────────────────────────────────────────────
        if state == "main_menu":
            action = menu_screen.handle(events)
            if action == "play":
                user_screen = UsernameScreen()
                state = "username"
            elif action == "leaderboard":
                leaderboard = load_leaderboard()
                lb_screen   = LeaderboardScreen(leaderboard)
                state       = "leaderboard"
            elif action == "settings":
                set_screen  = SettingsScreen(settings)
                state       = "settings"
            elif action == "quit":
                pygame.quit()
                sys.exit()
            menu_screen.draw(screen)

        # ── STATE: username ──────────────────────────────────────────────
        elif state == "username":
            result = user_screen.handle(events)
            if result:
                username = result
                start_game()
                state = "playing"
            user_screen.draw(screen)

        # ── STATE: playing ───────────────────────────────────────────────
        elif state == "playing":
            for event in events:
                if event.type == pygame.KEYDOWN:
                    world.handle_key(event.key)

            world.update()
            world.draw(screen)
            hud.draw(screen, world)

            if world.game_over or world.finished:
                # save to leaderboard
                crash_sound.play()
                add_leaderboard_entry(
                    username,
                    world.score,
                    int(world.distance),
                    world.coins_collected,
                )
                over_screen = GameOverScreen(
                    world.score,
                    world.distance,
                    world.coins_collected,
                    finished=world.finished,
                )
                state = "game_over"

        # ── STATE: game_over ─────────────────────────────────────────────
        elif state == "game_over":
            action = over_screen.handle(events)
            if action == "retry":
                start_game()
                state = "playing"
            elif action == "menu":
                menu_screen = MainMenu()
                state       = "main_menu"
            over_screen.draw(screen)

        # ── STATE: leaderboard ───────────────────────────────────────────
        elif state == "leaderboard":
            action = lb_screen.handle(events)
            if action == "back":
                menu_screen = MainMenu()
                state       = "main_menu"
            lb_screen.draw(screen)

        # ── STATE: settings ──────────────────────────────────────────────
        elif state == "settings":
            result = set_screen.handle(events)
            if result:
                action, new_settings = result
                if action == "save" and new_settings:
                    settings = new_settings
                    save_settings(settings)
                menu_screen = MainMenu()
                state       = "main_menu"
            set_screen.draw(screen)

        pygame.display.flip()
        clock.tick(FPS)


if __name__ == "__main__":
    main()