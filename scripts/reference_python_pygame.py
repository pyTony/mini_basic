#!/usr/bin/env python3
"""Mandelbrot - exactly matching the BBC BASIC version."""

import pygame
import sys
import time

# Constants matching the BASIC version
Z_CHARS = ".,'~=+:;*%&$OXB#@ "
BBC_COLOURS = [
    (0, 0, 0),       # 0: Black
    (255, 0, 0),     # 1: Red
    (0, 255, 0),     # 2: Green
    (255, 255, 0),   # 3: Yellow
    (0, 0, 255),     # 4: Blue
    (255, 0, 255),   # 5: Magenta
    (0, 255, 255),   # 6: Cyan
    (255, 255, 255), # 7: White
]

def mandelbrot_point(c_real, c_imag, f=50, max_iter=16):
    """Exactly matches the BBC BASIC algorithm."""
    a = c_real
    b = c_imag
    i = 0
    
    while i < max_iter:
        q = b / f
        s = b - (q * f)
        t = ((a * a) - (b * b)) / f + c_real
        b = 2 * ((a * q) + (a * s / f)) + c_imag
        a = t
        p = a / f
        q = b / f
        
        if (p * p) + (q * q) >= 5:
            return i
        
        i += 1
    
    return max_iter

def render_mandelbrot():
    """Render the Mandelbrot set exactly like the BASIC version."""
    grid = []
    f = 50
    
    for y in range(-12, 13):
        row = []
        for x in range(-49, 30):
            c_real = x * 229 / 100
            c_imag = y * 416 / 100
            
            i = mandelbrot_point(c_real, c_imag, f)
            
            if i < 16:
                char = Z_CHARS[i]
                colour = i % 8
            else:
                char = ' '
                colour = 7
            
            row.append((char, colour))
        grid.append(row)
    
    return grid

def main():
    pygame.init()
    
    # Settings matching the BASIC version's MODE 8
    font_size = 12
    char_width = font_size // 2
    char_height = font_size
    cols = 80  # -49 to 30 = 79 columns, rounded to 80
    rows = 25  # -12 to 12 = 25 rows
    
    display_width = cols * char_width
    display_height = rows * char_height
    
    screen = pygame.display.set_mode((display_width, display_height))
    pygame.display.set_caption("Mandelbrot - Python (matching BASIC)")
    
    try:
        font = pygame.font.Font(None, font_size)
    except:
        font = pygame.font.SysFont("monospace", font_size)
    
    # Pre-render all characters for speed
    char_surfaces = {}
    for i, ch in enumerate(Z_CHARS):
        colour = BBC_COLOURS[i % 8]
        char_surfaces[(ch, i % 8)] = font.render(ch, True, colour)
    
    # Blank space
    blank = font.render(" ", True, (255, 255, 255))
    
    print("Rendering Mandelbrot...")
    start_time = time.time()
    
    grid = render_mandelbrot()
    
    render_time = time.time() - start_time
    print(f"Rendered in {render_time:.2f} seconds")
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    print("ESC pressed - exiting")
                    running = False
        
        screen.fill((0, 0, 0))
        
        for row_idx, row in enumerate(grid):
            for col_idx, (char, colour_idx) in enumerate(row):
                if char == ' ':
                    surface = blank
                else:
                    surface = char_surfaces.get((char, colour_idx), blank)
                
                x = col_idx * char_width
                y = row_idx * char_height
                screen.blit(surface, (x, y))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
