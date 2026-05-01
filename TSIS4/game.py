# game.py — Snake game logic (all screens + gameplay)

import pygame
import random
import sys

import db
import settings as settings_mod
from config import *



#  Utility helpers


def cell_rect(col: int, row: int) -> pygame.Rect:
    return pygame.Rect(col * CELL_SIZE, row * CELL_SIZE, CELL_SIZE, CELL_SIZE)


def random_cell(exclude: set) -> tuple[int, int]:
    """Pick a random grid cell not in exclude."""
    while True:
        c = random.randint(1, COLS - 2)
        r = random.randint(1, ROWS - 2)
        if (c, r) not in exclude:
            return c, r


def draw_text(surface, text, size, color, cx, cy, font_name=None):
    font = pygame.font.SysFont(font_name or "monospace", size, bold=True)
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(cx, cy))
    surface.blit(surf, rect)
    return rect


def draw_button(surface, text, rect, color, hover_color, mouse_pos, font_size=22):
    hovered = rect.collidepoint(mouse_pos)
    pygame.draw.rect(surface, hover_color if hovered else color, rect, border_radius=8)
    pygame.draw.rect(surface, WHITE, rect, 2, border_radius=8)
    draw_text(surface, text, font_size, WHITE, rect.centerx, rect.centery)
    return hovered



#  Food item


class FoodItem:
    def __init__(self, kind: str, pos: tuple[int, int], spawn_time: int):
        self.kind       = kind          # "normal" | "bonus" | "poison"
        self.pos        = pos
        self.spawn_time = spawn_time    # pygame.time.get_ticks()

    @property
    def color(self):
        return FOOD_COLORS[self.kind]

    def is_expired(self, now: int) -> bool:
        return (now - self.spawn_time) > FOOD_DISAPPEAR_SECONDS * 1000

    def draw(self, surface, now: int):
        rect = cell_rect(*self.pos)
        # Blink in final 2 seconds
        remaining = FOOD_DISAPPEAR_SECONDS * 1000 - (now - self.spawn_time)
        if remaining < 2000 and (now // 250) % 2 == 0:
            return
        pygame.draw.ellipse(surface, self.color, rect.inflate(-4, -4))



#  Power-up item


class PowerUp:
    def __init__(self, kind: str, pos: tuple[int, int], spawn_time: int):
        self.kind       = kind   # "speed" | "slow" | "shield"
        self.pos        = pos
        self.spawn_time = spawn_time

    @property
    def color(self):
        return POWERUP_COLORS[self.kind]

    def is_expired(self, now: int) -> bool:
        return (now - self.spawn_time) > POWERUP_FIELD_SECONDS * 1000

    def draw(self, surface, now: int):
        rect = cell_rect(*self.pos)
        # Pulse
        if (now // 300) % 2 == 0:
            pygame.draw.rect(surface, self.color, rect.inflate(-2, -2), border_radius=4)
        else:
            pygame.draw.rect(surface, WHITE, rect.inflate(-6, -6), border_radius=4)
        label_map = {"speed": "S", "slow": "W", "shield": "X"}
        font = pygame.font.SysFont("monospace", 12, bold=True)
        surf = font.render(label_map[self.kind], True, BLACK)
        surface.blit(surf, surf.get_rect(center=rect.center))



#  Main Game class


class SnakeGame:
    def __init__(self, screen: pygame.Surface, username: str,
                 player_id: int, personal_best: int, cfg: dict):
        self.screen        = screen
        self.username      = username
        self.player_id     = player_id
        self.personal_best = personal_best
        self.cfg           = cfg          # settings dict

        self.clock  = pygame.time.Clock()
        self.font_s = pygame.font.SysFont("monospace", 16)
        self.font_m = pygame.font.SysFont("monospace", 20, bold=True)

        self.snake_color = tuple(cfg.get("snake_color", list(GREEN)))

        self._reset()

    #initialise / reset

    def _reset(self):
        cx, cy = COLS // 2, ROWS // 2
        self.body     = [(cx, cy), (cx - 1, cy), (cx - 2, cy)]
        self.direction = (1, 0)
        self.next_dir  = (1, 0)

        self.score         = 0
        self.level         = 1
        self.foods_eaten   = 0
        self.fps           = BASE_FPS
        self.game_over     = False

        self.foods:    list[FoodItem] = []
        self.powerup:  PowerUp | None = None
        self.obstacles: set[tuple[int, int]] = set()

        # Active effect state
        self.shield_active      = False
        self.effect_type: str | None = None   # "speed" | "slow" | None
        self.effect_end_time    = 0

        self._spawn_food()
        self._spawn_food()   # start with 2 foods

    #occupied cells
    def _occupied(self) -> set:
        occ = set(self.body)
        occ |= self.obstacles
        occ |= {f.pos for f in self.foods}
        if self.powerup:
            occ.add(self.powerup.pos)
        return occ

    #spawning

    def _spawn_food(self):
        now  = pygame.time.get_ticks()
        occ  = self._occupied()
        pos  = random_cell(occ)
        roll = random.random()
        if roll < 0.15:
            kind = "poison"
        elif roll < 0.35:
            kind = "bonus"
        else:
            kind = "normal"
        self.foods.append(FoodItem(kind, pos, now))

    def _spawn_powerup(self):
        if self.powerup is not None:
            return
        now = pygame.time.get_ticks()
        kind = random.choice(["speed", "slow", "shield"])
        pos  = random_cell(self._occupied())
        self.powerup = PowerUp(kind, pos, now)

    def _place_obstacles(self):
        """Randomly place obstacle blocks, not trapping the snake head."""
        self.obstacles.clear()
        count = OBSTACLE_COUNT_PER_LEVEL * (self.level - OBSTACLE_START_LEVEL + 1)
        hx, hy = self.body[0]
        safe_zone = {(hx + dx, hy + dy)
                     for dx in range(-3, 4)
                     for dy in range(-3, 4)}
        occ = set(self.body) | safe_zone
        placed = 0
        attempts = 0
        while placed < count and attempts < 1000:
            attempts += 1
            c = random.randint(1, COLS - 2)
            r = random.randint(1, ROWS - 2)
            if (c, r) not in occ:
                self.obstacles.add((c, r))
                occ.add((c, r))
                placed += 1

    #level up

    def _level_up(self):
        self.level      += 1
        self.fps         = min(BASE_FPS + (self.level - 1) * SPEED_PER_LEVEL, MAX_FPS)
        self.foods_eaten  = 0
        self.foods.clear()
        self.powerup = None
        if self.level >= OBSTACLE_START_LEVEL:
            self._place_obstacles()
        else:
            self.obstacles.clear()
        self._spawn_food()
        self._spawn_food()

    #active effect

    def _apply_effect(self, kind: str):
        now = pygame.time.get_ticks()
        self.effect_type     = kind
        self.effect_end_time = now + POWERUP_EFFECT_SECONDS * 1000
        if kind == "speed":
            self.fps = min(self.fps + SPEED_BOOST_BONUS, MAX_FPS)
        elif kind == "slow":
            self.fps = max(self.fps - SLOW_MOTION_PENALTY, 3)
        elif kind == "shield":
            self.shield_active = True

    def _check_effect_expiry(self):
        if self.effect_type and self.effect_type != "shield":
            now = pygame.time.get_ticks()
            if now >= self.effect_end_time:
                self.fps = min(BASE_FPS + (self.level - 1) * SPEED_PER_LEVEL, MAX_FPS)
                self.effect_type = None

    #main game loop

    def run(self) -> dict:
        """Run gameplay. Returns result dict for Game Over screen."""
        POWERUP_SPAWN_INTERVAL = 10_000   # ms between power-up spawn attempts
        last_pu_attempt = pygame.time.get_ticks()

        while not self.game_over:
            now = pygame.time.get_ticks()
            self._handle_events()
            self._check_effect_expiry()

            # Expire food
            self.foods = [f for f in self.foods if not f.is_expired(now)]
            if len(self.foods) == 0:
                self._spawn_food()

            # Expire power-up on field
            if self.powerup and self.powerup.is_expired(now):
                self.powerup = None

            # Attempt to spawn power-up periodically
            if now - last_pu_attempt > POWERUP_SPAWN_INTERVAL:
                last_pu_attempt = now
                if random.random() < 0.5:
                    self._spawn_powerup()

            self._move()
            self._draw(now)
            self.clock.tick(self.fps)

        return {
            "score":  self.score,
            "level":  self.level,
            "best":   max(self.personal_best, self.score),
        }

    #event handling

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                dx, dy = self.direction
                if event.key in (pygame.K_UP, pygame.K_w)    and dy == 0:
                    self.next_dir = (0, -1)
                elif event.key in (pygame.K_DOWN,  pygame.K_s) and dy == 0:
                    self.next_dir = (0,  1)
                elif event.key in (pygame.K_LEFT,  pygame.K_a) and dx == 0:
                    self.next_dir = (-1, 0)
                elif event.key in (pygame.K_RIGHT, pygame.K_d) and dx == 0:
                    self.next_dir = (1,  0)

    #movement & collision 

    def _move(self):
        self.direction = self.next_dir
        hx, hy = self.body[0]
        dx, dy = self.direction
        new_head = (hx + dx, hy + dy)

        # Wall collision
        if not (0 < new_head[0] < COLS - 1 and 0 < new_head[1] < ROWS - 1):
            if self.shield_active:
                self.shield_active = False
                self.effect_type   = None
                return           # ignore this collision once
            self.game_over = True
            return

        # Self collision
        if new_head in self.body[1:]:
            if self.shield_active:
                self.shield_active = False
                self.effect_type   = None
                return
            self.game_over = True
            return

        # Obstacle collision
        if new_head in self.obstacles:
            if self.shield_active:
                self.shield_active = False
                self.effect_type   = None
                return
            self.game_over = True
            return

        self.body.insert(0, new_head)
        ate_food = False

        # Check food
        for food in list(self.foods):
            if food.pos == new_head:
                ate_food = True
                self.foods.remove(food)
                if food.kind == "poison":
                    # Shorten snake
                    for _ in range(POISON_SHORTEN):
                        if len(self.body) > 1:
                            self.body.pop()
                    if len(self.body) <= 1:
                        self.game_over = True
                        return
                else:
                    self.score       += FOOD_WEIGHTS[food.kind]
                    self.foods_eaten += 1
                    if self.foods_eaten >= FOOD_PER_LEVEL:
                        self._level_up()
                self._spawn_food()
                break

        # Check power-up
        if self.powerup and self.powerup.pos == new_head:
            self._apply_effect(self.powerup.kind)
            self.powerup = None
            ate_food = True   # don't remove tail

        if not ate_food:
            self.body.pop()

    #drawing 

    def _draw(self, now: int):
        self.screen.fill(BLACK)
        self._draw_border()
        if self.cfg.get("grid_overlay"):
            self._draw_grid()
        self._draw_obstacles()
        for food in self.foods:
            food.draw(self.screen, now)
        if self.powerup:
            self.powerup.draw(self.screen, now)
        self._draw_snake()
        self._draw_hud(now)
        pygame.display.flip()

    def _draw_border(self):
        pygame.draw.rect(self.screen, GRAY,
                         pygame.Rect(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT), CELL_SIZE)

    def _draw_grid(self):
        for c in range(COLS):
            pygame.draw.line(self.screen, DARK_GRAY,
                             (c * CELL_SIZE, 0), (c * CELL_SIZE, WINDOW_HEIGHT))
        for r in range(ROWS):
            pygame.draw.line(self.screen, DARK_GRAY,
                             (0, r * CELL_SIZE), (WINDOW_WIDTH, r * CELL_SIZE))

    def _draw_obstacles(self):
        for (c, r) in self.obstacles:
            rect = cell_rect(c, r)
            pygame.draw.rect(self.screen, GRAY, rect)
            pygame.draw.rect(self.screen, LIGHT_GRAY, rect, 1)

    def _draw_snake(self):
        for i, (c, r) in enumerate(self.body):
            rect  = cell_rect(c, r)
            color = self.snake_color if i > 0 else WHITE
            pygame.draw.rect(self.screen, color, rect.inflate(-2, -2), border_radius=4)

    def _draw_hud(self, now: int):
        # Score / level
        score_surf = self.font_s.render(
            f"Score: {self.score}   Level: {self.level}   Best: {self.personal_best}",
            True, WHITE)
        self.screen.blit(score_surf, (CELL_SIZE + 4, 4))

        # Active effect indicator
        if self.effect_type:
            remaining = max(0, self.effect_end_time - now) // 1000
            label = {"speed": "SPEED BOOST", "slow": "SLOW MO", "shield": "SHIELD"}
            color = POWERUP_COLORS.get(self.effect_type, WHITE)
            eff_surf = self.font_s.render(
                f"[{label.get(self.effect_type,'')}] {remaining}s",
                True, color)
            self.screen.blit(eff_surf, (WINDOW_WIDTH // 2 - eff_surf.get_width() // 2, 4))
        elif self.shield_active:
            eff_surf = self.font_s.render("[SHIELD ACTIVE]", True, PURPLE)
            self.screen.blit(eff_surf, (WINDOW_WIDTH // 2 - eff_surf.get_width() // 2, 4))



#  Screen helpers (used by main.py)


def screen_main_menu(screen: pygame.Surface, cfg: dict) -> str:
    """
    Returns: "play" | "leaderboard" | "settings" | "quit"
    Also sets cfg["username"] via keyboard input.
    """
    clock = pygame.font.SysFont("monospace", 18)
    username = cfg.get("username", "")
    input_active = True

    while True:
        mouse = pygame.mouse.get_pos()
        screen.fill(BLACK)

        draw_text(screen, "SNAKE game by Nurdaulet", 54, GREEN,
                  WINDOW_WIDTH // 2, WINDOW_HEIGHT // 6)

        # Username input box
        draw_text(screen, "Enter your name:", 20, LIGHT_GRAY,
                  WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 70)
        inp_rect = pygame.Rect(WINDOW_WIDTH // 2 - 140, WINDOW_HEIGHT // 2 - 50, 280, 36)
        pygame.draw.rect(screen, DARK_GRAY, inp_rect, border_radius=6)
        pygame.draw.rect(screen, GREEN if input_active else GRAY, inp_rect, 2, border_radius=6)
        font = pygame.font.SysFont("monospace", 20)
        txt_surf = font.render(username + ("|" if input_active else ""), True, WHITE)
        screen.blit(txt_surf, (inp_rect.x + 8, inp_rect.y + 7))

        cy = WINDOW_HEIGHT // 2 + 20
        btn_w, btn_h = 200, 44
        bx = WINDOW_WIDTH // 2 - btn_w // 2

        b_play  = pygame.Rect(bx, cy,       btn_w, btn_h)
        b_lead  = pygame.Rect(bx, cy + 56,  btn_w, btn_h)
        b_sett  = pygame.Rect(bx, cy + 112, btn_w, btn_h)
        b_quit  = pygame.Rect(bx, cy + 168, btn_w, btn_h)

        draw_button(screen, "PLAY",        b_play,  DARK_GREEN, GREEN,      mouse)
        draw_button(screen, "LEADERBOARD", b_lead,  (50,50,150),(80,80,200),mouse)
        draw_button(screen, "SETTINGS",    b_sett,  DARK_GRAY,  GRAY,       mouse)
        draw_button(screen, "QUIT",         b_quit,  (120,0,0),  RED,        mouse)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if inp_rect.collidepoint(event.pos):
                    input_active = True
                else:
                    input_active = False
                if b_play.collidepoint(event.pos):
                    cfg["username"] = username.strip() or "Player"
                    return "play"
                if b_lead.collidepoint(event.pos):
                    return "leaderboard"
                if b_sett.collidepoint(event.pos):
                    return "settings"
                if b_quit.collidepoint(event.pos):
                    pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and input_active:
                if event.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                elif event.key == pygame.K_RETURN:
                    input_active = False
                elif len(username) < 20:
                    username += event.unicode


def screen_game_over(screen: pygame.Surface, result: dict) -> str:
    """Returns "retry" | "menu"."""
    clock_obj = pygame.time.Clock()
    while True:
        mouse = pygame.mouse.get_pos()
        screen.fill(BLACK)

        draw_text(screen, "GAME OVER", 52, RED,
                  WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4)
        draw_text(screen, f"Score: {result['score']}",
                  28, WHITE, WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 60)
        draw_text(screen, f"Level reached: {result['level']}",
                  24, LIGHT_GRAY, WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 20)
        draw_text(screen, f"Personal best: {result['best']}",
                  24, YELLOW, WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 20)

        bw, bh = 200, 44
        bx = WINDOW_WIDTH // 2 - bw // 2
        b_retry = pygame.Rect(bx, WINDOW_HEIGHT // 2 + 80,  bw, bh)
        b_menu  = pygame.Rect(bx, WINDOW_HEIGHT // 2 + 140, bw, bh)

        draw_button(screen, "  RETRY",     b_retry, DARK_GREEN, GREEN, mouse)
        draw_button(screen, "  MAIN MENU", b_menu,  DARK_GRAY,  GRAY,  mouse)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if b_retry.collidepoint(event.pos):
                    return "retry"
                if b_menu.collidepoint(event.pos):
                    return "menu"
        clock_obj.tick(30)


def screen_leaderboard(screen: pygame.Surface, rows: list[dict]) -> None:
    """Display leaderboard. Returns when Back is clicked."""
    clock_obj = pygame.time.Clock()
    font_h = pygame.font.SysFont("monospace", 18, bold=True)
    font_r = pygame.font.SysFont("monospace", 16)

    while True:
        mouse = pygame.mouse.get_pos()
        screen.fill(BLACK)

        draw_text(screen, "  LEADERBOARD", 36, YELLOW,
                  WINDOW_WIDTH // 2, 40)

        # Header
        header = f"{'#':>3}  {'Name':<15} {'Score':>6}  {'Lvl':>4}  {'Date':<12}"
        hsurf = font_h.render(header, True, LIGHT_GRAY)
        screen.blit(hsurf, (60, 90))
        pygame.draw.line(screen, GRAY, (60, 112), (WINDOW_WIDTH - 60, 112), 1)

        for i, row in enumerate(rows):
            rank_color = [YELLOW, LIGHT_GRAY, (200, 120, 40)][i] if i < 3 else WHITE
            line = (f"{row['rank']:>3}  {row['username']:<15} "
                    f"{row['score']:>6}  {row['level_reached']:>4}  {row['played_at']:<12}")
            rsurf = font_r.render(line, True, rank_color)
            screen.blit(rsurf, (60, 120 + i * 26))

        if not rows:
            draw_text(screen, "No records yet.", 22, LIGHT_GRAY,
                      WINDOW_WIDTH // 2, 200)

        b_back = pygame.Rect(WINDOW_WIDTH // 2 - 80, WINDOW_HEIGHT - 70, 160, 44)
        draw_button(screen, "◀  BACK", b_back, DARK_GRAY, GRAY, mouse)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if b_back.collidepoint(event.pos):
                    return
        clock_obj.tick(30)


def screen_settings(screen: pygame.Surface, cfg: dict) -> dict:
    """
    Displays settings. Returns (possibly modified) cfg dict when Save & Back clicked.
    """
    clock_obj = pygame.time.Clock()
    snake_color = list(cfg.get("snake_color", list(GREEN)))
    grid        = cfg.get("grid_overlay", False)
    sound       = cfg.get("sound", True)

    color_options = [
        ("Green",  [50, 200, 50]),
        ("Cyan",   [0, 200, 200]),
        ("Orange", [230, 130, 0]),
        ("Purple", [150, 50, 200]),
        ("White",  [240, 240, 240]),
        ("Yellow", [240, 220, 0]),
    ]

    while True:
        mouse = pygame.mouse.get_pos()
        screen.fill(BLACK)

        draw_text(screen, " SETTINGS", 36, LIGHT_GRAY, WINDOW_WIDTH // 2, 50)

        # Grid toggle
        draw_text(screen, "Grid Overlay:", 22, WHITE, 200, 160)
        b_grid = pygame.Rect(340, 145, 100, 32)
        draw_button(screen, "ON" if grid else "OFF", b_grid,
                    DARK_GREEN if grid else (100, 0, 0),
                    GREEN      if grid else RED,
                    mouse, 20)

        # Sound toggle
        draw_text(screen, "Sound:", 22, WHITE, 200, 220)
        b_sound = pygame.Rect(340, 205, 100, 32)
        draw_button(screen, "ON" if sound else "OFF", b_sound,
                    DARK_GREEN if sound else (100, 0, 0),
                    GREEN      if sound else RED,
                    mouse, 20)

        # Snake color
        draw_text(screen, "Snake Color:", 22, WHITE, 200, 290)
        for idx, (name, rgb) in enumerate(color_options):
            cx2 = 340 + idx * 70
            rect = pygame.Rect(cx2 - 24, 275, 48, 28)
            is_selected = (rgb == snake_color)
            pygame.draw.rect(screen, tuple(rgb), rect, border_radius=5)
            if is_selected:
                pygame.draw.rect(screen, WHITE, rect, 3, border_radius=5)

        # Preview snake
        draw_text(screen, "Preview:", 20, LIGHT_GRAY, 200, 360)
        for i in range(5):
            r = pygame.Rect(300 + i * 26, 348, 22, 22)
            pygame.draw.rect(screen, tuple(snake_color), r, border_radius=4)

        b_save = pygame.Rect(WINDOW_WIDTH // 2 - 110, WINDOW_HEIGHT - 80, 220, 44)
        draw_button(screen, "  SAVE & BACK", b_save, (0, 100, 180), BLUE, mouse)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if b_grid.collidepoint(event.pos):
                    grid = not grid
                elif b_sound.collidepoint(event.pos):
                    sound = not sound
                elif b_save.collidepoint(event.pos):
                    cfg["snake_color"]  = snake_color
                    cfg["grid_overlay"] = grid
                    cfg["sound"]        = sound
                    settings_mod.save(cfg)
                    return cfg
                for idx, (name, rgb) in enumerate(color_options):
                    cx2 = 340 + idx * 70
                    rect = pygame.Rect(cx2 - 24, 275, 48, 28)
                    if rect.collidepoint(event.pos):
                        snake_color = list(rgb)
        clock_obj.tick(30)