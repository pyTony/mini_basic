"""Pure Python + pygame benchmark v3 - with filled shapes

This version is closer to the real soccer.bas:
- Large filled yellow circle
- Multiple FILLED rotating pentagons (like PLOT 85 triangle fills in the original)
- Some line work on top

Run with: python benchmark_soccer_v3.py
"""

import pygame
import math
import time
import sys

# === Configuration ===
WIDTH = 640
HEIGHT = 512
CIRCLE_RADIUS = 220
CENTER_X = WIDTH // 2
CENTER_Y = HEIGHT // 2

BLACK = (0, 0, 0)
YELLOW = (255, 255, 0)
CYAN = (0, 255, 255)
WHITE = (255, 255, 255)
MAGENTA = (255, 100, 255)
LIGHT_BLUE = (100, 200, 255)

def create_regular_polygon(cx, cy, radius, rotation, num_sides=5):
    points = []
    for i in range(num_sides):
        angle = rotation + (2 * math.pi * i / num_sides) - math.pi / 2
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((x, y))
    return points

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Pure Python Soccerball Benchmark v3 (Filled Shapes)")
    clock = pygame.time.Clock()

    rotation = 0.0
    rotation_speed = 0.022

    frame_count = 0
    fps = 0.0
    last_time = time.time()

    print("Pure Python benchmark v3 (with filled shapes) running...")
    print("This version uses filled pentagons to better match the original soccer.bas.\n")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        screen.fill(BLACK)

        # === 1. Large filled circle (the ball) ===
        pygame.draw.circle(screen, YELLOW, (CENTER_X, CENTER_Y), CIRCLE_RADIUS)

        # === 2. FILLED rotating pentagons ===
        # Large filled cyan pentagon (semi-transparent feel via color choice)
        p1 = create_regular_polygon(CENTER_X, CENTER_Y, CIRCLE_RADIUS * 0.88, rotation, 5)
        pygame.draw.polygon(screen, CYAN, p1)

        # Medium filled white pentagon
        p2 = create_regular_polygon(CENTER_X, CENTER_Y, CIRCLE_RADIUS * 0.62, -rotation * 1.35, 5)
        pygame.draw.polygon(screen, WHITE, p2)

        # Small filled magenta pentagon
        p3 = create_regular_polygon(CENTER_X, CENTER_Y, CIRCLE_RADIUS * 0.38, rotation * 0.65, 5)
        pygame.draw.polygon(screen, MAGENTA, p3)

        # === 3. Some line work on top (like the original PLOT segments) ===
        # Outer outline
        pygame.draw.polygon(screen, LIGHT_BLUE, p1, width=2)
        # Inner outlines
        pygame.draw.polygon(screen, (200, 200, 200), p2, width=2)

        # Radial lines from center
        for i in range(10):
            angle = rotation * 0.4 + (2 * math.pi * i / 10)
            x = CENTER_X + CIRCLE_RADIUS * 0.92 * math.cos(angle)
            y = CENTER_Y + CIRCLE_RADIUS * 0.92 * math.sin(angle)
            pygame.draw.line(screen, WHITE, (CENTER_X, CENTER_Y), (x, y), 1)

        pygame.display.flip()

        rotation += rotation_speed

        # FPS measurement
        frame_count += 1
        current_time = time.time()
        if current_time - last_time >= 1.0:
            fps = frame_count
            print(f"FPS: {fps}")
            frame_count = 0
            last_time = current_time

    pygame.quit()
    print(f"\nFinal measured FPS (v3 with filled shapes): {fps}")
    sys.exit(0)

if __name__ == "__main__":
    main()
