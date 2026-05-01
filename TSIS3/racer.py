import pygame
import random
import math
import os

#colours
ROAD_DARK   = (40,  40,  40)
LANE_WHITE  = (240, 240, 220)
LANE_YELLOW = (255, 210,   0)
GRASS_GREEN = (34,  120,  34)
SKY_BLUE    = (100, 160, 210)

CAR_COLORS = {
    "red":    (220,  50,  50),
    "blue":   (50,  100, 220),
    "yellow": (230, 200,  20),
    "green":  (50,  180,  80),
    "white":  (230, 230, 230),
}

# layout constants 
SCREEN_W, SCREEN_H = 480, 700
NUM_LANES    = 4
ROAD_LEFT    = 80
ROAD_RIGHT   = SCREEN_W - 80
ROAD_W       = ROAD_RIGHT - ROAD_LEFT
LANE_W       = ROAD_W // NUM_LANES
PLAYER_Y     = SCREEN_H - 150
PLAYER_W, PLAYER_H = 44, 72    # hitbox / sprite size

DIFFICULTY_PARAMS = {
    "easy":   dict(base_speed=4, coin_freq=55, traffic_freq=90, obs_freq=120, speed_step=0.003),
    "medium": dict(base_speed=5, coin_freq=45, traffic_freq=65, obs_freq=85,  speed_step=0.005),
    "hard":   dict(base_speed=7, coin_freq=35, traffic_freq=48, obs_freq=60,  speed_step=0.008),
}

COIN_WEIGHTS    = {1: 0.55, 3: 0.30, 5: 0.15}
POWERUP_TYPES   = ["nitro", "shield", "repair"]
POWERUP_TIMEOUT = 8 * 60
NITRO_DURATION  = 4 * 60
TOTAL_DISTANCE  = 2000


def lane_centre(lane):
    return ROAD_LEFT + lane * LANE_W + LANE_W // 2



#  Sprite / asset cache

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
_cache: dict = {}


def _load(name: str, width: int, height: int):
    """Load assets/<name>.png, scale to (width, height), cache result.
    Returns None silently if the file doesn't exist."""
    key = (name, width, height)
    if key in _cache:
        return _cache[key]

    path = os.path.join(ASSETS_DIR, f"{name}.png")
    if not os.path.exists(path):
        _cache[key] = None
        return None

    try:
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, (width, height))
        _cache[key] = img
        return img
    except Exception:
        _cache[key] = None
        return None


def _blit_centre(surf, img, cx, cy):
    surf.blit(img, (cx - img.get_width() // 2, cy - img.get_height() // 2))



class Player:
    W, H = PLAYER_W, PLAYER_H

    def __init__(self, color_name="red"):
        self.lane      = 1
        self.x         = float(lane_centre(self.lane))
        self.y         = float(PLAYER_Y)
        self.color     = CAR_COLORS.get(color_name, CAR_COLORS["red"])
        self.alive     = True
        self.shield    = False
        self.nitro     = False
        self.nitro_t   = 0
        self.speed_mul = 1.0
        self._target_x = self.x

    def move(self, direction):
        new_lane = self.lane + direction
        if 0 <= new_lane < NUM_LANES:
            self.lane      = new_lane
            self._target_x = float(lane_centre(self.lane))

    def update(self):
        self.x += (self._target_x - self.x) * 0.18
        if self.nitro:
            self.nitro_t -= 1
            if self.nitro_t <= 0:
                self.nitro     = False
                self.speed_mul = 1.0

    def activate_nitro(self):
        self.nitro     = True
        self.nitro_t   = NITRO_DURATION
        self.speed_mul = 1.6

    def activate_shield(self):
        self.shield = True

    def hit(self):
        if self.shield:
            self.shield = False
            return False    # absorbed
        self.alive = False
        return True         # dead

    def rect(self):
        return pygame.Rect(int(self.x) - self.W // 2, int(self.y), self.W, self.H)

    def draw(self, surf):
        x, y = int(self.x), int(self.y)
        w, h = self.W, self.H

        sprite = _load("Player", w, h)
        if sprite:
            surf.blit(sprite, (x - w // 2, y))
        else:
            col   = self.color
            dark  = tuple(max(0, c - 60) for c in col)
            light = tuple(min(255, c + 40) for c in col)
            pygame.draw.rect(surf, dark,  (x-w//2,   y,      w,    h),    border_radius=6)
            pygame.draw.rect(surf, col,   (x-w//2+3, y+4,    w-6,  h-8),  border_radius=4)
            pygame.draw.rect(surf, light, (x-w//2+7, y+10,   w-14, h//2-10), border_radius=4)
            pygame.draw.rect(surf, (140,200,240),
                                   (x-w//2+8, y+12, w-16, 14), border_radius=3)
            for wx, wy in [(x-w//2-4,y+8),(x+w//2-4,y+8),
                           (x-w//2-4,y+h-20),(x+w//2-4,y+h-20)]:
                pygame.draw.rect(surf, (30,30,30), (wx, wy, 8, 14), border_radius=2)

        # shield aura
        if self.shield:
            sh = _load("shield", w + 24, h + 24)
            if sh:
                surf.blit(sh, (x - w//2 - 12, y - 12))
            else:
                s = pygame.Surface((w+24, h+24), pygame.SRCALPHA)
                pygame.draw.ellipse(s, (100, 255, 100, 90), s.get_rect())
                surf.blit(s, (x - w//2 - 12, y - 12))

        # nitro flames
        if self.nitro:
            for i in range(3):
                fx = x - 8 + i * 8
                fy = y + h + random.randint(0, 6)
                fh = random.randint(10, 22)
                pygame.draw.polygon(surf, (255, 140, 0),
                    [(fx, fy), (fx-5, fy+fh), (fx+5, fy+fh)])



class TrafficCar:
    W, H = PLAYER_W, PLAYER_H

    def __init__(self, lane, speed):
        self.lane  = lane
        self.x     = float(lane_centre(lane))
        self.y     = float(-self.H - random.randint(0, 80))
        self.speed = speed

    def update(self, road_speed):
        self.y += self.speed + road_speed * 0.3

    def off_screen(self):
        return self.y > SCREEN_H + 20

    def rect(self):
        return pygame.Rect(int(self.x) - self.W//2, int(self.y), self.W, self.H)

    def draw(self, surf):
        x, y = int(self.x), int(self.y)
        w, h = self.W, self.H

        sprite = _load("Enemy", w, h)
        if sprite:
            surf.blit(sprite, (x - w//2, y))
        else:
            col  = (180, 60, 60)
            dark = tuple(max(0, c-50) for c in col)
            pygame.draw.rect(surf, dark, (x-w//2,   y,      w,    h),   border_radius=5)
            pygame.draw.rect(surf, col,  (x-w//2+3, y+4,    w-6,  h-8), border_radius=4)
            pygame.draw.rect(surf, (140,200,240),
                                   (x-w//2+7, y+h-24, w-14, 12),        border_radius=3)
            for wx, wy in [(x-w//2-4,y+8),(x+w//2-4,y+8),
                           (x-w//2-4,y+h-20),(x+w//2-4,y+h-20)]:
                pygame.draw.rect(surf, (30,30,30), (wx, wy, 8, 14), border_radius=2)
            pygame.draw.circle(surf, (255,80,80), (x-w//2+7, y+h-6), 4)
            pygame.draw.circle(surf, (255,80,80), (x+w//2-7, y+h-6), 4)



class Obstacle:
    SPRITE_SIZES = {
        "oil":     (52, 44),
        "barrier": (LANE_W - 4, 38),
        "pothole": (44, 32),
    }
    EFFECTS = {"oil": "slow", "barrier": "crash", "pothole": "slow"}
    FALLBACK_COLS = {
        "oil":     (20,  20,  60),
        "barrier": (255, 50,  50),
        "pothole": (30,  30,  30),
    }

    def __init__(self, lane, speed, obs_type=None):
        self.lane = lane
        self.x    = float(lane_centre(lane))
        self.y    = float(-50)
        if obs_type is None:
            obs_type = random.choice(list(self.SPRITE_SIZES.keys()))
        self.type   = obs_type
        self.effect = self.EFFECTS[obs_type]
        self.w, self.h = self.SPRITE_SIZES[obs_type]
        self.speed  = speed

    def update(self, road_speed):
        self.y += self.speed + road_speed

    def off_screen(self):
        return self.y > SCREEN_H + 30

    def rect(self):
        return pygame.Rect(int(self.x) - self.w//2,
                           int(self.y) - self.h//2,
                           self.w, self.h)

    def draw(self, surf):
        cx, cy = int(self.x), int(self.y)
        sprite  = _load(self.type, self.w, self.h)   # "oil", "barrier", "pothole"
        if sprite:
            _blit_centre(surf, sprite, cx, cy)
        else:
            col = self.FALLBACK_COLS[self.type]
            r   = self.rect()
            if self.type in ("oil", "pothole"):
                pygame.draw.ellipse(surf, col, r)
            else:
                for i in range(0, r.w, 12):
                    c2 = (255,200,0) if (i//12)%2==0 else col
                    pygame.draw.rect(surf, c2, (r.x+i, r.y, min(12,r.w-i), r.h))
                pygame.draw.rect(surf, (200,0,0), r, 2, border_radius=4)



class Coin:
    BASE_W, BASE_H = 36, 36

    def __init__(self, lane, speed):
        self.lane  = lane
        self.x     = float(lane_centre(lane)) + random.randint(-10, 10)
        self.y     = float(-20)
        self.speed = speed
        r = random.random()
        cum = 0
        for val, prob in COIN_WEIGHTS.items():
            cum += prob
            if r < cum:
                self.value = val
                break
        else:
            self.value = 1
        scale  = 1.0 + self.value * 0.12
        self.w = int(self.BASE_W * scale)
        self.h = int(self.BASE_H * scale)

    def update(self, road_speed):
        self.y += self.speed + road_speed

    def off_screen(self):
        return self.y > SCREEN_H + 20

    def rect(self):
        return pygame.Rect(int(self.x) - self.w//2,
                           int(self.y) - self.h//2,
                           self.w, self.h)

    def draw(self, surf, tick):
        cx = int(self.x)
        cy = int(self.y) + int(3 * math.sin(tick * 0.08 + self.x))   # gentle bob

        sprite = _load("coin", self.w, self.h)
        if sprite:
            _blit_centre(surf, sprite, cx, cy)
            if self.value > 1:
                font = pygame.font.SysFont("Consolas", 11, bold=True)
                lbl  = font.render(f"x{self.value}", True, (255, 230, 50))
                surf.blit(lbl, (cx + self.w//2 - 4, cy - self.h//2 - 2))
        else:
            cols = {1:(180,100,30), 3:(200,200,210), 5:(255,200,30)}
            col  = cols.get(self.value, (255,200,30))
            rad  = self.w // 2
            pygame.draw.circle(surf, tuple(min(255,c+60) for c in col), (cx,cy), rad+3)
            pygame.draw.circle(surf, col, (cx, cy), rad)
            font = pygame.font.SysFont("Arial", 9, bold=True)
            lbl  = font.render(str(self.value), True, (30,20,0))
            surf.blit(lbl, (cx - lbl.get_width()//2, cy - lbl.get_height()//2))



class PowerUp:
    SIZE = 48
    SPRITE_NAMES = {"nitro": "nitro", "shield": "shield", "repair": "repair"}
    FALLBACK_COLS = {
        "nitro":  (0,   200, 255),
        "shield": (100, 255, 100),
        "repair": (255, 120,  50),
    }

    def __init__(self, lane, speed):
        self.lane    = lane
        self.x       = float(lane_centre(lane))
        self.y       = float(-30)
        self.speed   = speed
        self.kind    = random.choice(POWERUP_TYPES)
        self.timeout = POWERUP_TIMEOUT
        self.size    = self.SIZE

    def update(self, road_speed):
        self.y       += self.speed + road_speed
        self.timeout -= 1

    def expired(self):
        return self.timeout <= 0 or self.y > SCREEN_H + 20

    def rect(self):
        s = self.size // 2
        return pygame.Rect(int(self.x) - s, int(self.y) - s, self.size, self.size)

    def draw(self, surf, tick):
        cx = int(self.x)
        cy = int(self.y) + int(4 * math.sin(tick * 0.07))   # float
        s  = self.size

        # glow ring that fades as timeout decreases
        alpha = max(40, int(160 * (self.timeout / POWERUP_TIMEOUT)))
        col   = self.FALLBACK_COLS[self.kind]
        glow  = pygame.Surface((s+20, s+20), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*col, alpha), (s//2+10, s//2+10), s//2+9)
        surf.blit(glow, (cx - s//2 - 10, cy - s//2 - 10))

        name   = self.SPRITE_NAMES[self.kind]
        sprite = _load(name, s, s)
        if sprite:
            _blit_centre(surf, sprite, cx, cy)
        else:
            pts = [(cx,cy-s//2),(cx+s//2,cy),(cx,cy+s//2),(cx-s//2,cy)]
            pygame.draw.polygon(surf, col, pts)
            pygame.draw.polygon(surf, (255,255,255), pts, 2)
            font = pygame.font.SysFont("Arial", 13, bold=True)
            lbl  = {"nitro":"N","shield":"S","repair":"R"}[self.kind]
            t    = font.render(lbl, True, (20,20,20))
            surf.blit(t, (cx-t.get_width()//2, cy-t.get_height()//2))



class RoadEvent:
    def __init__(self, event_type, speed):
        self.type  = event_type
        self.y     = float(-30)
        self.speed = speed
        self.w     = ROAD_W
        self.h     = 20

    def update(self, road_speed):
        self.y += self.speed + road_speed

    def off_screen(self):
        return self.y > SCREEN_H + 40

    def player_rect(self):
        return pygame.Rect(ROAD_LEFT, int(self.y) - self.h//2, self.w, self.h)

    def draw(self, surf, tick):
        x = ROAD_LEFT
        y = int(self.y)
        if self.type == "nitro_strip":
            for i in range(0, self.w, 20):
                col = (0,230,255) if (i//20)%2==0 else (0,100,180)
                pygame.draw.rect(surf, col, (x+i, y, min(20,self.w-i), self.h))
            for _ in range(5):
                sx = x + random.randint(0, self.w)
                sy = y + random.randint(0, self.h)
                pygame.draw.circle(surf, (255,255,255), (sx, sy), 2)
        else:
            for i in range(0, self.w, 16):
                col = (160,120,50) if (i//16)%2==0 else (100,70,20)
                pygame.draw.rect(surf, col, (x+i, y, min(16,self.w-i), self.h))



class GameWorld:
    def __init__(self, difficulty="medium", car_color="red", sound=True):
        params = DIFFICULTY_PARAMS[difficulty]
        self.base_speed   = params["base_speed"]
        self.coin_freq    = float(params["coin_freq"])
        self.traffic_freq = float(params["traffic_freq"])
        self.obs_freq     = float(params["obs_freq"])
        self.speed_step   = params["speed_step"]
        self.sound        = sound

        self.road_speed      = float(self.base_speed)
        self.tick            = 0
        self.distance        = 0.0
        self.coins_collected = 0
        self.score           = 0
        self.bonus_score     = 0

        self.player    = Player(car_color)
        self.traffic   = []
        self.obstacles = []
        self.coins     = []
        self.powerups  = []
        self.events    = []

        self.active_pu  = None
        self.slow_timer = 0

        self.stripe_y = [i * 80 for i in range(12)]

        self.game_over = False
        self.finished  = False

        self._pu_counter  = 0
        self._pu_every    = 300

        #background
        self._road_bg = _load("AnimatedStreet", ROAD_W, SCREEN_H)

    # helpers 
    def _safe_lane(self, exclude=None):
        lanes = list(range(NUM_LANES))
        if exclude:
            lanes = [l for l in lanes if l not in exclude]
        return random.choice(lanes) if lanes else random.randint(0, NUM_LANES-1)

    def _speed(self):
        s = self.road_speed
        if self.slow_timer > 0:
            s *= 0.5
        if self.player.nitro:
            s *= self.player.speed_mul
        return s

    # spawners 
    def _try_spawn_coin(self):
        if self.tick % max(1, int(self.coin_freq)) == 0:
            self.coins.append(Coin(random.randint(0, NUM_LANES-1), 0))

    def _try_spawn_traffic(self):
        if self.tick % max(1, int(self.traffic_freq)) == 0:
            occupied = {t.lane for t in self.traffic if t.y < 160}
            lane = self._safe_lane(list(occupied))
            self.traffic.append(TrafficCar(lane, self.road_speed * random.uniform(0.35, 0.85)))

    def _try_spawn_obstacle(self):
        if self.tick % max(1, int(self.obs_freq)) == 0:
            occupied = {o.lane for o in self.obstacles if o.y < 220}
            lane = self._safe_lane(list(occupied) + [self.player.lane])
            self.obstacles.append(Obstacle(lane, 0))

    def _try_spawn_powerup(self):
        self._pu_counter += 1
        if self._pu_counter >= self._pu_every and not self.powerups:
            self._pu_counter = 0
            self.powerups.append(PowerUp(random.randint(0, NUM_LANES-1), 0))

    def _try_spawn_event(self):
        if self.tick % 400 == 0 and self.tick > 0:
            self.events.append(
                RoadEvent(random.choice(["nitro_strip", "speed_bump"]), 0))

    # update
    def update(self):
        if self.game_over or self.finished:
            return

        self.tick += 1
        speed = self._speed()

        # ramp difficulty
        self.road_speed   += self.speed_step
        self.coin_freq     = max(18, self.coin_freq    - 0.002)
        self.traffic_freq  = max(22, self.traffic_freq - 0.003)
        self.obs_freq      = max(28, self.obs_freq     - 0.002)

        self.distance += speed / 60.0
        if self.distance >= TOTAL_DISTANCE:
            self.finished = True
            self._finalize_score()
            return

        if self.slow_timer > 0:
            self.slow_timer -= 1

        for i, sy in enumerate(self.stripe_y):
            self.stripe_y[i] = (sy + speed) % (SCREEN_H + 80)

        self._try_spawn_coin()
        self._try_spawn_traffic()
        self._try_spawn_obstacle()
        self._try_spawn_powerup()
        self._try_spawn_event()

        for c in self.coins:     c.update(speed)
        for t in self.traffic:   t.update(speed)
        for o in self.obstacles: o.update(speed)
        for p in self.powerups:  p.update(speed)
        for e in self.events:    e.update(speed)
        self.player.update()

        self.coins     = [c for c in self.coins     if not c.off_screen()]
        self.traffic   = [t for t in self.traffic   if not t.off_screen()]
        self.obstacles = [o for o in self.obstacles if not o.off_screen()]
        self.powerups  = [p for p in self.powerups  if not p.expired()]
        self.events    = [e for e in self.events    if not e.off_screen()]

        pr = self.player.rect()

        # coins
        still = []
        for c in self.coins:
            if pr.colliderect(c.rect()):
                self.coins_collected += c.value
            else:
                still.append(c)
        self.coins = still

        # enemy traffic
        for t in list(self.traffic):
            if pr.colliderect(t.rect()):
                dead = self.player.hit()
                if dead:
                    self._finalize_score()
                    self.game_over = True
                    return
                self.traffic.remove(t)
                break

        # obstacles
        still = []
        for o in self.obstacles:
            if pr.colliderect(o.rect()):
                if o.effect == "crash":
                    dead = self.player.hit()
                    if dead:
                        self._finalize_score()
                        self.game_over = True
                        return
                else:
                    self.slow_timer = 90
            else:
                still.append(o)
        self.obstacles = still

        # power-ups
        still = []
        for pu in self.powerups:
            if pr.colliderect(pu.rect()):
                self._apply_powerup(pu.kind)
            else:
                still.append(pu)
        self.powerups = still

        # road events
        for ev in self.events:
            if pr.colliderect(ev.player_rect()):
                if ev.type == "nitro_strip":
                    self.player.activate_nitro()
                    self.active_pu = "nitro"
                else:
                    self.slow_timer = 60

        self.score = self.coins_collected * 10 + int(self.distance) + self.bonus_score

    def _apply_powerup(self, kind):
        self.player.shield    = False
        self.player.nitro     = False
        self.player.speed_mul = 1.0

        if kind == "nitro":
            self.player.activate_nitro()
            self.active_pu = "nitro"
        elif kind == "shield":
            self.player.activate_shield()
            self.active_pu = "shield"
        elif kind == "repair":
            if self.obstacles:
                self.obstacles.sort(key=lambda o: abs(o.y - self.player.y))
                self.obstacles.pop(0)
            self.slow_timer   = 0
            self.active_pu    = None
            self.bonus_score += 50

    def _finalize_score(self):
        self.score = self.coins_collected * 10 + int(self.distance) + self.bonus_score

    def handle_key(self, key):
        if key in (pygame.K_LEFT,  pygame.K_a): self.player.move(-1)
        if key in (pygame.K_RIGHT, pygame.K_d): self.player.move(1)

    # draw
    def draw(self, surf):
        surf.fill(SKY_BLUE)

        # grass
        pygame.draw.rect(surf, GRASS_GREEN, (0,          0, ROAD_LEFT,             SCREEN_H))
        pygame.draw.rect(surf, GRASS_GREEN, (ROAD_RIGHT, 0, SCREEN_W - ROAD_RIGHT, SCREEN_H))

        # road surface
        if self._road_bg:
            surf.blit(self._road_bg, (ROAD_LEFT, 0))
        else:
            pygame.draw.rect(surf, ROAD_DARK, (ROAD_LEFT, 0, ROAD_W, SCREEN_H))

        # scrolling lane dashes 
        for lane in range(1, NUM_LANES):
            lx = ROAD_LEFT + lane * LANE_W
            for sy in self.stripe_y:
                s = pygame.Surface((3, 28), pygame.SRCALPHA)
                s.fill((*LANE_WHITE, 140))
                surf.blit(s, (lx - 1, sy - 40))

        # edge lines
        pygame.draw.rect(surf, LANE_YELLOW, (ROAD_LEFT,    0, 4, SCREEN_H))
        pygame.draw.rect(surf, LANE_YELLOW, (ROAD_RIGHT-4, 0, 4, SCREEN_H))

        # road events
        for ev in self.events:
            ev.draw(surf, self.tick)

        # obstacles
        for o in self.obstacles:
            o.draw(surf)

        # coins
        for c in self.coins:
            c.draw(surf, self.tick)

        # power-ups
        for pu in self.powerups:
            pu.draw(surf, self.tick)

        # enemy traffic cars
        for t in self.traffic:
            t.draw(surf)

        # player 
        self.player.draw(surf)