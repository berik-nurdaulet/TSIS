import pygame
import math

# ---------------- PENCIL ----------------
def draw_pencil(surface, color, points, size):
    for i in range(len(points) - 1):
        pygame.draw.line(surface, color, points[i], points[i+1], size)


# ---------------- LINE ----------------
def draw_line(surface, color, start, end, size):
    pygame.draw.line(surface, color, start, end, size)


# ---------------- RECTANGLE ----------------
def draw_rect(surface, color, start, end, size):
    x1, y1 = start
    x2, y2 = end

    rect = pygame.Rect(min(x1, x2), min(y1, y2),
                       abs(x2 - x1), abs(y2 - y1))
    pygame.draw.rect(surface, color, rect, size)


# ---------------- SQUARE ----------------
def draw_square(surface, color, start, end, size):
    side = min(abs(end[0]-start[0]), abs(end[1]-start[1]))
    rect = pygame.Rect(start[0], start[1], side, side)
    pygame.draw.rect(surface, color, rect, size)


# ---------------- CIRCLE ----------------
def draw_circle(surface, color, start, end, size):
    radius = int(math.dist(start, end))
    pygame.draw.circle(surface, color, start, radius, size)


# ---------------- TRIANGLES ----------------
def draw_right_triangle(surface, color, start, end, size):
    x1, y1 = start
    x2, y2 = end
    pygame.draw.polygon(surface, color,
                        [start, (x1, y2), end], size)


def draw_equilateral_triangle(surface, color, start, end, size):
    x1, y1 = start
    x2, y2 = end

    h = int(math.sqrt(3)/2 * (x2 - x1))
    points = [start, (x2, y1), ((x1+x2)//2, y1 - h)]

    pygame.draw.polygon(surface, color, points, size)


def draw_rhombus(surface, color, start, end, size):
    x1, y1 = start
    x2, y2 = end

    cx, cy = (x1+x2)//2, (y1+y2)//2
    points = [(cx,y1), (x2,cy), (cx,y2), (x1,cy)]

    pygame.draw.polygon(surface, color, points, size)


# ---------------- FLOOD FILL ----------------
def flood_fill(surface, x, y, new_color):
    target = surface.get_at((x, y))

    if target == new_color:
        return

    stack = [(x, y)]
    width, height = surface.get_size()

    while stack:
        cx, cy = stack.pop()

        if 0 <= cx < width and 0 <= cy < height:
            if surface.get_at((cx, cy)) == target:
                surface.set_at((cx, cy), new_color)

                stack.append((cx+1, cy))
                stack.append((cx-1, cy))
                stack.append((cx, cy+1))
                stack.append((cx, cy-1))


# ---------------- ERASER ----------------
def erase(surface, position, size):
    pygame.draw.circle(surface, (255, 255, 255), position, size)