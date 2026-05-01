import pygame
import sys
from datetime import datetime
import tools

pygame.init()

#  SCREEN 
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("TSIS 2 Paint")

clock = pygame.time.Clock()

#  CANVAS 
canvas = pygame.Surface((WIDTH, HEIGHT))
canvas.fill((255, 255, 255))

#  SETTINGS 
color = (0, 0, 255)
brush_size = 2
tool = "pencil"

drawing = False
start_pos = None
points = []

#  TEXT 
font = pygame.font.SysFont("Arial", 24)

text_input = ""
text_pos = None

typing = False
text_color = color

#  SAVE FUNCTION 
def save_canvas():
    filename = datetime.now().strftime("paint_%Y-%m-%d_%H-%M-%S.png")
    pygame.image.save(canvas, filename)
    print("Saved:", filename)

#  MAIN LOOP 
while True:

    for event in pygame.event.get():

        # EXIT
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        
        # KEYBOARD
        
        if event.type == pygame.KEYDOWN:

            #  COLORS 
            if event.key == pygame.K_r:
                color = (255, 0, 0)

            elif event.key == pygame.K_g:
                color = (0, 255, 0)

            elif event.key == pygame.K_b:
                color = (0, 0, 255)

            #  BRUSH SIZE 
            elif event.key == pygame.K_1:
                brush_size = 2

            elif event.key == pygame.K_2:
                brush_size = 5

            elif event.key == pygame.K_3:
                brush_size = 10

            #  TOOLS 
            elif event.key == pygame.K_p:
                tool = "pencil"

            elif event.key == pygame.K_l:
                tool = "line"

            elif event.key == pygame.K_e:
                tool = "rect"

            elif event.key == pygame.K_o:
                tool = "circle"

            elif event.key == pygame.K_4:
                tool = "square"

            elif event.key == pygame.K_5:
                tool = "right_triangle"

            elif event.key == pygame.K_6:
                tool = "equilateral_triangle"

            elif event.key == pygame.K_7:
                tool = "rhombus"

            elif event.key == pygame.K_f:
                tool = "fill"

            elif event.key == pygame.K_t:
                tool = "text"

            elif event.key == pygame.K_x:
                tool = "eraser"

            #  SAVE 
            elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_CTRL:
                save_canvas()

            
            # TEXT TYPING
            
            if typing:

                # FINALIZE TEXT
                if event.key == pygame.K_RETURN:

                    text_surface = font.render(
                        text_input,
                        True,
                        text_color
                    )

                    canvas.blit(text_surface, text_pos)

                    typing = False
                    text_input = ""

                # CANCEL TEXT
                elif event.key == pygame.K_ESCAPE:

                    typing = False
                    text_input = ""

                # ADD CHARACTER
                else:
                    text_input += event.unicode

        
        # MOUSE BUTTON DOWN
        
        if event.type == pygame.MOUSEBUTTONDOWN:

            start_pos = event.pos
            drawing = True

            #  FILL 
            if tool == "fill":
                tools.flood_fill(canvas, *event.pos, color)

            #  TEXT 
            elif tool == "text":

                text_pos = event.pos
                typing = True
                text_input = ""

                # IMPORTANT:
                # Save current color for this text
                text_color = color

            #  PENCIL 
            elif tool == "pencil":
                points = [event.pos]

        
        # MOUSE BUTTON UP
        
        if event.type == pygame.MOUSEBUTTONUP:

            drawing = False
            end_pos = event.pos

            #  LINE 
            if tool == "line":
                tools.draw_line(
                    canvas,
                    color,
                    start_pos,
                    end_pos,
                    brush_size
                )

            #  RECTANGLE 
            elif tool == "rect":
                tools.draw_rect(
                    canvas,
                    color,
                    start_pos,
                    end_pos,
                    brush_size
                )

            #  CIRCLE 
            elif tool == "circle":
                tools.draw_circle(
                    canvas,
                    color,
                    start_pos,
                    end_pos,
                    brush_size
                )

            #  SQUARE 
            elif tool == "square":
                tools.draw_square(
                    canvas,
                    color,
                    start_pos,
                    end_pos,
                    brush_size
                )

            #  RIGHT TRIANGLE 
            elif tool == "right_triangle":
                tools.draw_right_triangle(
                    canvas,
                    color,
                    start_pos,
                    end_pos,
                    brush_size
                )

            #  EQUILATERAL TRIANGLE 
            elif tool == "equilateral_triangle":
                tools.draw_equilateral_triangle(
                    canvas,
                    color,
                    start_pos,
                    end_pos,
                    brush_size
                )

            #  RHOMBUS 
            elif tool == "rhombus":
                tools.draw_rhombus(
                    canvas,
                    color,
                    start_pos,
                    end_pos,
                    brush_size
                )

        
        # MOUSE MOTION
        
        if event.type == pygame.MOUSEMOTION and drawing:

            #  PENCIL 
            if tool == "pencil":

                points.append(event.pos)

                tools.draw_pencil(
                    canvas,
                    color,
                    points,
                    brush_size
                )

            #  ERASER 
            elif tool == "eraser":

                tools.erase(
                    canvas,
                    event.pos,
                    brush_size * 2
                )

    
    # DRAW CANVAS
    
    screen.blit(canvas, (0, 0))

    
    # LIVE PREVIEW
    
    if drawing and start_pos:

        mouse_pos = pygame.mouse.get_pos()

        # LINE
        if tool == "line":
            tools.draw_line(
                screen,
                color,
                start_pos,
                mouse_pos,
                brush_size
            )

        # RECTANGLE
        elif tool == "rect":
            tools.draw_rect(
                screen,
                color,
                start_pos,
                mouse_pos,
                brush_size
            )

        # CIRCLE
        elif tool == "circle":
            tools.draw_circle(
                screen,
                color,
                start_pos,
                mouse_pos,
                brush_size
            )

        # SQUARE
        elif tool == "square":
            tools.draw_square(
                screen,
                color,
                start_pos,
                mouse_pos,
                brush_size
            )

        # RIGHT TRIANGLE
        elif tool == "right_triangle":
            tools.draw_right_triangle(
                screen,
                color,
                start_pos,
                mouse_pos,
                brush_size
            )

        # EQUILATERAL TRIANGLE
        elif tool == "equilateral_triangle":
            tools.draw_equilateral_triangle(
                screen,
                color,
                start_pos,
                mouse_pos,
                brush_size
            )

        # RHOMBUS
        elif tool == "rhombus":
            tools.draw_rhombus(
                screen,
                color,
                start_pos,
                mouse_pos,
                brush_size
            )

    
    # TEXT PREVIEW
    
    if typing and text_input:

        preview = font.render(
            text_input,
            True,
            text_color
        )

        screen.blit(preview, text_pos)

    
    # UPDATE
    
    pygame.display.update()
    clock.tick(60)