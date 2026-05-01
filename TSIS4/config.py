# config.py — Game constants

# Window
WINDOW_WIDTH  = 800
WINDOW_HEIGHT = 600
TITLE         = "Snake Game"

# Grid
CELL_SIZE  = 20
COLS       = WINDOW_WIDTH  // CELL_SIZE   # 40
ROWS       = WINDOW_HEIGHT // CELL_SIZE   # 30

# Frame-rate / speed
BASE_FPS        = 10
SPEED_PER_LEVEL = 2        # FPS added each level
MAX_FPS         = 30

# Scoring & levelling
FOOD_PER_LEVEL  = 5        # foods eaten to advance a level
OBSTACLE_START_LEVEL = 3   # obstacles appear from this level
OBSTACLE_COUNT_PER_LEVEL = 4

# Food
FOOD_DISAPPEAR_SECONDS = 8

# Poison food
POISON_SHORTEN = 2

# Power-up
POWERUP_FIELD_SECONDS  = 8   # time before disappears if not collected
POWERUP_EFFECT_SECONDS = 5   # how long effect lasts after collection
SPEED_BOOST_BONUS = 4
SLOW_MOTION_PENALTY = 4

# Colors (default; overridden by settings.json)
BLACK      = (  0,   0,   0)
WHITE      = (255, 255, 255)
GREEN      = ( 50, 200,  50)
DARK_GREEN = ( 20, 140,  20)
RED        = (220,  50,  50)
DARK_RED   = (120,   0,   0)
ORANGE     = (230, 130,   0)
YELLOW     = (240, 220,   0)
BLUE       = ( 50, 100, 220)
CYAN       = (  0, 200, 200)
PURPLE     = (150,  50, 200)
GRAY       = (100, 100, 100)
LIGHT_GRAY = (180, 180, 180)
DARK_GRAY  = ( 40,  40,  40)

# Food type colors
FOOD_COLORS = {
    "normal":  GREEN,
    "bonus":   YELLOW,
    "poison":  DARK_RED,
}

# Food point weights
FOOD_WEIGHTS = {
    "normal": 1,
    "bonus":  3,
}

# Power-up colors
POWERUP_COLORS = {
    "speed":  CYAN,
    "slow":   BLUE,
    "shield": PURPLE,
}

# DB connection string — edit to match your PostgreSQL setup
DB_DSN = "dbname=snake_game user=postgres password=Nurda2007 host=localhost port=5432"