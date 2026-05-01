#!/usr/bin/env python3
# main.py — Entry point for Snake TSIS 4

import sys
import pygame

import db
import settings as settings_mod
from config import WINDOW_WIDTH, WINDOW_HEIGHT, TITLE
from game import (
    SnakeGame,
    screen_main_menu,
    screen_game_over,
    screen_leaderboard,
    screen_settings,
)


def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption(TITLE)

    # ── Database init (graceful fallback if no DB) ──────────────────────
    db_available = db.init_db()
    if not db_available:
        print("[main] Running WITHOUT database (leaderboard disabled).")

    # ── Load settings ───────────────────────────────────────────────────
    cfg = settings_mod.load()

    player_id     = None
    personal_best = 0
    current_screen = "menu"

    while True:

        # ── MAIN MENU ──────────────────────────────────────────────────
        if current_screen == "menu":
            action = screen_main_menu(screen, cfg)

            if action == "play":
                username = cfg.get("username", "Player")
                if db_available:
                    player_id     = db.get_or_create_player(username)
                    personal_best = db.get_personal_best(player_id) if player_id else 0
                else:
                    player_id     = None
                    personal_best = 0
                current_screen = "play"

            elif action == "leaderboard":
                current_screen = "leaderboard"

            elif action == "settings":
                current_screen = "settings"

        # ── GAMEPLAY ───────────────────────────────────────────────────
        elif current_screen == "play":
            game = SnakeGame(screen, cfg.get("username", "Player"),
                             player_id or 0, personal_best, cfg)
            result = game.run()

            # Save to DB
            if db_available and player_id:
                db.save_session(player_id, result["score"], result["level"])
                # refresh personal best from DB
                personal_best = db.get_personal_best(player_id)
                result["best"] = personal_best

            current_screen = "gameover"

        # ── GAME OVER ──────────────────────────────────────────────────
        elif current_screen == "gameover":
            action = screen_game_over(screen, result)
            if action == "retry":
                current_screen = "play"
            else:
                current_screen = "menu"

        # ── LEADERBOARD ────────────────────────────────────────────────
        elif current_screen == "leaderboard":
            rows = db.get_leaderboard() if db_available else []
            screen_leaderboard(screen, rows)
            current_screen = "menu"

        # ── SETTINGS ───────────────────────────────────────────────────
        elif current_screen == "settings":
            cfg = screen_settings(screen, cfg)
            current_screen = "menu"


if __name__ == "__main__":
    main()