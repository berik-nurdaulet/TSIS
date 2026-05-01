import pygame
import math

# ── palette ────────────────────────────────────────────────────────────────
BG         = (12,  14,  22)
PANEL      = (22,  26,  40)
ACCENT     = (0,  200, 255)
ACCENT2    = (255, 80,  120)
WHITE      = (240, 240, 240)
GREY       = (120, 130, 150)
DARK_GREY  = (40,  45,  60)
GREEN      = (60,  210, 100)
YELLOW     = (255, 210,  30)
RED        = (220,  50,  60)
ORANGE     = (255, 140,  30)

CAR_PREVIEW= {
    "red":    (220,  50,  50),
    "blue":   (50,  100, 220),
    "yellow": (230, 200,  20),
    "green":  (50,  180,  80),
    "white":  (230, 230, 230),
}

SCREEN_W, SCREEN_H = 480, 700


def _font(size, bold=False):
    return pygame.font.SysFont("Consolas", size, bold=bold)


def _draw_text(surf, text, font, color, cx, cy, alpha=255):
    s = font.render(text, True, color)
    if alpha < 255:
        s.set_alpha(alpha)
    surf.blit(s, (cx - s.get_width()//2, cy - s.get_height()//2))
    return s.get_rect(center=(cx, cy))


def _draw_panel(surf, rect, radius=12, alpha=200):
    s = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
    pygame.draw.rect(s, (*PANEL, alpha), (0, 0, rect.w, rect.h), border_radius=radius)
    pygame.draw.rect(s, (*ACCENT, 80),  (0, 0, rect.w, rect.h), 2, border_radius=radius)
    surf.blit(s, rect.topleft)


class Button:
    def __init__(self, cx, cy, w, h, label, color=ACCENT, text_color=(10,10,20)):
        self.rect   = pygame.Rect(cx - w//2, cy - h//2, w, h)
        self.label  = label
        self.color  = color
        self.tcolor = text_color
        self._hover = False

    def draw(self, surf):
        col   = tuple(min(255, c + 30) for c in self.color) if self._hover else self.color
        glow  = pygame.Surface((self.rect.w + 8, self.rect.h + 8), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*col, 60), (0, 0, glow.get_width(), glow.get_height()),
                         border_radius=14)
        surf.blit(glow, (self.rect.x - 4, self.rect.y - 4))
        pygame.draw.rect(surf, col, self.rect, border_radius=10)
        font = _font(16, bold=True)
        _draw_text(surf, self.label, font, self.tcolor,
                   self.rect.centerx, self.rect.centery)

    def handle(self, event):
        if event.type == pygame.MOUSEMOTION:
            self._hover = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and self._hover:
            return True
        return False


# ══════════════════════════════════════════════════════════════════════════════
class MainMenu:
    def __init__(self):
        self.tick    = 0
        self.buttons = [
            Button(SCREEN_W//2, 320, 200, 50, "  PLAY",      ACCENT,  (5, 5, 20)),
            Button(SCREEN_W//2, 385, 200, 50, " LEADERBOARD", DARK_GREY, WHITE),
            Button(SCREEN_W//2, 450, 200, 50, "  SETTINGS",  DARK_GREY, WHITE),
            Button(SCREEN_W//2, 515, 200, 50, "  QUIT",      (80, 20, 30), WHITE),
        ]

    def handle(self, events):
        for event in events:
            for i, btn in enumerate(self.buttons):
                if btn.handle(event):
                    return ["play", "leaderboard", "settings", "quit"][i]
        return None

    def draw(self, surf):
        self.tick += 1
        surf.fill(BG)

        # animated bg lines
        for i in range(10):
            y  = (i * 80 + self.tick * 1.5) % SCREEN_H
            al = int(20 + 15 * math.sin(self.tick * 0.04 + i))
            s  = pygame.Surface((SCREEN_W, 2), pygame.SRCALPHA)
            s.fill((*ACCENT, al))
            surf.blit(s, (0, y))

        # title
        f1 = _font(52, bold=True)
        f2 = _font(20)
        off= int(4 * math.sin(self.tick * 0.04))
        _draw_text(surf, "RACER", f1, ACCENT2, SCREEN_W//2, 160 + off)
        _draw_text(surf, "NURDAULET EDITION", f2, GREY, SCREEN_W//2, 220)

        # decorative car silhouette
        _draw_mini_car(surf, SCREEN_W//2, 270, (0, 180, 220), 1.0)

        for btn in self.buttons:
            btn.draw(surf)


# ══════════════════════════════════════════════════════════════════════════════
class SettingsScreen:
    def __init__(self, settings):
        self.settings = dict(settings)
        self.msg      = ""
        self.msg_t    = 0
        self.tick     = 0
        colors        = list(CAR_PREVIEW.keys())
        diffs         = ["easy", "medium", "hard"]
        self._color_idx = colors.index(self.settings.get("car_color","red"))
        self._diff_idx  = diffs.index(self.settings.get("difficulty","medium"))
        self._colors    = colors
        self._diffs     = diffs

        cx = SCREEN_W // 2
        self.btn_sound  = Button(cx+80, 250, 120, 40, "TOGGLE", DARK_GREY, WHITE)
        self.btn_col_l  = Button(cx-90, 330, 40,  40, "◀", DARK_GREY, WHITE)
        self.btn_col_r  = Button(cx+90, 330, 40,  40, "▶", DARK_GREY, WHITE)
        self.btn_dif_l  = Button(cx-90, 410, 40,  40, "◀", DARK_GREY, WHITE)
        self.btn_dif_r  = Button(cx+90, 410, 40,  40, "▶", DARK_GREY, WHITE)
        self.btn_save   = Button(cx,    510, 180, 50, "SAVE & BACK", ACCENT, (5,5,20))
        self.btn_back   = Button(cx,    575, 180, 44, "CANCEL",      DARK_GREY, WHITE)

    def handle(self, events):
        for event in events:
            if self.btn_sound.handle(event):
                self.settings["sound"] = not self.settings["sound"]
            if self.btn_col_l.handle(event):
                self._color_idx = (self._color_idx - 1) % len(self._colors)
                self.settings["car_color"] = self._colors[self._color_idx]
            if self.btn_col_r.handle(event):
                self._color_idx = (self._color_idx + 1) % len(self._colors)
                self.settings["car_color"] = self._colors[self._color_idx]
            if self.btn_dif_l.handle(event):
                self._diff_idx = (self._diff_idx - 1) % len(self._diffs)
                self.settings["difficulty"] = self._diffs[self._diff_idx]
            if self.btn_dif_r.handle(event):
                self._diff_idx = (self._diff_idx + 1) % len(self._diffs)
                self.settings["difficulty"] = self._diffs[self._diff_idx]
            if self.btn_save.handle(event):
                return ("save", self.settings)
            if self.btn_back.handle(event):
                return ("back", None)
        return None

    def draw(self, surf):
        self.tick += 1
        surf.fill(BG)
        f_title = _font(36, bold=True)
        f_lbl   = _font(15)
        f_val   = _font(17, bold=True)
        cx      = SCREEN_W // 2

        _draw_text(surf, "SETTINGS", f_title, ACCENT, cx, 80)
        pygame.draw.line(surf, ACCENT, (cx-120, 110), (cx+120, 110), 2)

        # sound
        _draw_panel(surf, pygame.Rect(cx-160, 225, 320, 55))
        _draw_text(surf, "SOUND", f_lbl, GREY, cx-60, 253)
        sv   = "ON" if self.settings["sound"] else "OFF"
        scol = GREEN if self.settings["sound"] else RED
        _draw_text(surf, sv, f_val, scol, cx-5, 253)
        self.btn_sound.draw(surf)

        # car color
        _draw_panel(surf, pygame.Rect(cx-160, 305, 320, 55))
        _draw_text(surf, "CAR COLOR", f_lbl, GREY, cx-20, 322)
        cname = self._colors[self._color_idx]
        ccol  = CAR_PREVIEW[cname]
        _draw_text(surf, cname.upper(), f_val, ccol, cx+10, 338)
        self.btn_col_l.draw(surf)
        self.btn_col_r.draw(surf)
        # mini car preview
        _draw_mini_car(surf, cx, 360, ccol, 0.55)

        # difficulty
        _draw_panel(surf, pygame.Rect(cx-160, 385, 320, 55))
        _draw_text(surf, "DIFFICULTY", f_lbl, GREY, cx-10, 403)
        dcol = GREEN if self._diffs[self._diff_idx]=="easy" else \
               YELLOW if self._diffs[self._diff_idx]=="medium" else RED
        _draw_text(surf, self._diffs[self._diff_idx].upper(), f_val, dcol, cx+10, 418)
        self.btn_dif_l.draw(surf)
        self.btn_dif_r.draw(surf)

        self.btn_save.draw(surf)
        self.btn_back.draw(surf)


# ══════════════════════════════════════════════════════════════════════════════
class LeaderboardScreen:
    def __init__(self, entries):
        self.entries  = entries
        self.btn_back = Button(SCREEN_W//2, 640, 160, 44, "◀ BACK", DARK_GREY, WHITE)
        self.tick     = 0

    def handle(self, events):
        for event in events:
            if self.btn_back.handle(event):
                return "back"
        return None

    def draw(self, surf):
        self.tick += 1
        surf.fill(BG)
        f_title = _font(34, bold=True)
        f_head  = _font(12, bold=True)
        f_row   = _font(13)
        cx      = SCREEN_W // 2

        _draw_text(surf, "LEADERBOARD", f_title, YELLOW, cx, 60)
        pygame.draw.line(surf, YELLOW, (cx-160, 90), (cx+160, 90), 2)

        # header
        hy = 110
        _draw_panel(surf, pygame.Rect(20, hy, SCREEN_W-40, 28))
        _draw_text(surf, "#",      f_head, GREY, 50,  hy+14)
        _draw_text(surf, "NAME",   f_head, GREY, 145, hy+14)
        _draw_text(surf, "SCORE",  f_head, GREY, 280, hy+14)
        _draw_text(surf, "DIST m", f_head, GREY, 390, hy+14)
        _draw_text(surf, "COINS",  f_head, GREY, 455, hy+14)

        medal = ["🥇","🥈","🥉"]
        for i, e in enumerate(self.entries[:10]):
            ry   = 145 + i * 46
            hov  = i < 3
            col  = (*DARK_GREY, 180) if not hov else (*PANEL, 220)
            _draw_panel(surf, pygame.Rect(20, ry-2, SCREEN_W-40, 40))
            rank_col = [YELLOW, (200,200,210),(180,100,30)][i] if i < 3 else GREY
            rank_str = medal[i] if i < 3 else str(i+1)
            _draw_text(surf, rank_str, f_row, rank_col, 50, ry+18)
            _draw_text(surf, e.get("name","?")[:10], f_row, WHITE, 145, ry+18)
            _draw_text(surf, str(e.get("score",0)),  f_row, ACCENT, 280, ry+18)
            _draw_text(surf, str(int(e.get("distance",0))), f_row, GREEN, 390, ry+18)
            _draw_text(surf, str(e.get("coins",0)),  f_row, YELLOW, 455, ry+18)

        if not self.entries:
            _draw_text(surf, "No entries yet!", _font(18), GREY, cx, 320)

        self.btn_back.draw(surf)


# ══════════════════════════════════════════════════════════════════════════════
class GameOverScreen:
    def __init__(self, score, distance, coins, finished=False):
        self.score    = score
        self.distance = distance
        self.coins    = coins
        self.finished = finished
        self.tick     = 0
        cx            = SCREEN_W // 2
        self.btn_retry = Button(cx-100, 530, 160, 50, "↺ RETRY",     ACCENT,    (5,5,20))
        self.btn_menu  = Button(cx+100, 530, 160, 50, "⌂ MAIN MENU", DARK_GREY, WHITE)

    def handle(self, events):
        for event in events:
            if self.btn_retry.handle(event):
                return "retry"
            if self.btn_menu.handle(event):
                return "menu"
        return None

    def draw(self, surf):
        self.tick += 1
        surf.fill(BG)
        cx = SCREEN_W // 2

        # title
        f_big   = _font(44, bold=True)
        f_sub   = _font(20)
        f_stat  = _font(16)
        f_val   = _font(22, bold=True)

        title = "FINISH!" if self.finished else "GAME OVER"
        tcol  = GREEN     if self.finished else ACCENT2
        off   = int(3 * math.sin(self.tick * 0.07))
        _draw_text(surf, title, f_big, tcol, cx, 150 + off)

        if self.finished:
            _draw_text(surf, "You completed the race!", f_sub, YELLOW, cx, 210)
        else:
            _draw_text(surf, "Better luck next time.", f_sub, GREY, cx, 210)

        # stats panel
        _draw_panel(surf, pygame.Rect(60, 250, SCREEN_W-120, 220), radius=14)
        stats = [
            ("SCORE",    str(self.score),         ACCENT),
            ("DISTANCE", f"{int(self.distance)} m", GREEN),
            ("COINS",    str(self.coins),          YELLOW),
        ]
        for idx, (lbl, val, col) in enumerate(stats):
            y = 300 + idx * 58
            _draw_text(surf, lbl, f_stat, GREY, cx-80, y)
            _draw_text(surf, val, f_val,  col,  cx+60, y)
            if idx < 2:
                pygame.draw.line(surf, DARK_GREY, (80, y+28), (SCREEN_W-80, y+28), 1)

        self.btn_retry.draw(surf)
        self.btn_menu.draw(surf)


# ══════════════════════════════════════════════════════════════════════════════
class UsernameScreen:
    def __init__(self):
        self.name     = ""
        self.tick     = 0
        self.error    = ""
        self.btn_ok   = Button(SCREEN_W//2, 430, 160, 50, "START ▶", ACCENT, (5,5,20))
        self.active   = True

    def handle(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and self.active:
                if event.key == pygame.K_RETURN:
                    n = self.name.strip()
                    if n:
                        return n
                    self.error = "Please enter a name!"
                elif event.key == pygame.K_BACKSPACE:
                    self.name = self.name[:-1]
                elif len(self.name) < 14 and event.unicode.isprintable():
                    self.name += event.unicode
            if self.btn_ok.handle(event):
                n = self.name.strip()
                if n:
                    return n
                self.error = "Please enter a name!"
        return None

    def draw(self, surf):
        self.tick += 1
        surf.fill(BG)
        cx = SCREEN_W // 2
        f_title = _font(36, bold=True)
        f_lbl   = _font(16)
        f_name  = _font(26, bold=True)
        f_err   = _font(13)

        _draw_text(surf, "ENTER YOUR NAME", f_title, ACCENT, cx, 180)
        pygame.draw.line(surf, ACCENT, (cx-160, 215), (cx+160, 215), 2)

        # input box
        box = pygame.Rect(cx-160, 280, 320, 58)
        _draw_panel(surf, box, radius=10)
        blink = (self.tick // 30) % 2 == 0
        display = self.name + ("|" if blink else " ")
        _draw_text(surf, display, f_name, WHITE, cx, 309)

        if self.error:
            _draw_text(surf, self.error, f_err, ACCENT2, cx, 355)

        self.btn_ok.draw(surf)
        _draw_text(surf, "or press Enter", f_lbl, GREY, cx, 500)


# ══════════════════════════════════════════════════════════════════════════════
class HUD:
    """Draws the in-game overlay: score, distance, coins, power-up status."""

    def draw(self, surf, world):
        f_sm  = _font(13, bold=True)
        f_md  = _font(15, bold=True)
        cx    = SCREEN_W // 2

        # top bar background
        bar = pygame.Surface((SCREEN_W, 52), pygame.SRCALPHA)
        bar.fill((10, 12, 22, 200))
        surf.blit(bar, (0, 0))

        # score
        _draw_text(surf, f"SCORE  {world.score}", f_md, ACCENT, 90, 26)
        # coins
        _draw_text(surf, f"🪙 {world.coins_collected}", f_md, YELLOW, cx, 26)
        # distance
        remaining = max(0, 2000 - int(world.distance))
        _draw_text(surf, f"{int(world.distance)}m / {remaining}m left", f_sm, GREEN, SCREEN_W-100, 26)

        # progress bar
        prog = min(1.0, world.distance / 2000)
        pb_w = SCREEN_W - 20
        pygame.draw.rect(surf, DARK_GREY, (10, 48, pb_w, 6), border_radius=3)
        pygame.draw.rect(surf, ACCENT,    (10, 48, int(pb_w * prog), 6), border_radius=3)

        # active power-up
        if world.active_pu:
            _draw_pu_indicator(surf, world.active_pu, world.player)

        # difficulty / speed
        spd_str = f"SPD {world.road_speed:.1f}"
        _draw_text(surf, spd_str, _font(11), GREY, SCREEN_W-30, 70)

        # slow indicator
        if world.slow_timer > 0:
            _draw_text(surf, "⚠ SLOW", f_sm, ORANGE, cx, 75)


def _draw_pu_indicator(surf, kind, player):
    cols = {"nitro": (0,200,255), "shield": (100,255,100), "repair": (255,120,50)}
    col  = cols.get(kind, WHITE)
    box  = pygame.Rect(10, 60, 110, 30)
    _draw_panel(surf, box, radius=6, alpha=180)
    labels = {"nitro": f"NITRO {player.nitro_t//60+1}s", "shield": "SHIELD ✓", "repair": "REPAIR"}
    lbl = labels.get(kind, kind.upper())
    f   = _font(12, bold=True)
    _draw_text(surf, lbl, f, col, 65, 75)


def _draw_mini_car(surf, cx, cy, color, scale=1.0):
    w = int(38 * scale)
    h = int(64 * scale)
    dark  = tuple(max(0, c - 60) for c in color)
    light = tuple(min(255, c + 40) for c in color)
    pygame.draw.rect(surf, dark,  (cx-w//2, cy-h//2,     w,     h),     border_radius=int(6*scale))
    pygame.draw.rect(surf, color, (cx-w//2+3, cy-h//2+4, w-6,   h-8),   border_radius=int(4*scale))
    pygame.draw.rect(surf, light, (cx-w//2+7, cy-h//2+10, w-14, h//2-10), border_radius=int(4*scale))
    pygame.draw.rect(surf, (140,200,240),
                            (cx-w//2+8, cy-h//2+12, w-16, int(14*scale)), border_radius=3)