import pygame
import sys

pygame.init()
screen = pygame.display.set_mode((640, 480))
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 24)

def main():
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                print(f"MOUSEBUTTONDOWN: button={event.button}, pos={event.pos}")
            elif event.type == pygame.MOUSEWHEEL:
                print(f"MOUSEWHEEL: x={event.x}, y={event.y}")

        # Get button states for up to 5 buttons
        buttons = pygame.mouse.get_pressed(5)   # returns tuple of length 5
        pos = pygame.mouse.get_pos()

        screen.fill((30, 30, 30))
        lines = [
            f"Pos: {pos}",
            f"Buttons (0..4): {buttons}",
            f"Left: {buttons[0]}, Middle: {buttons[1]}, Right: {buttons[2]}",
            f"Button3: {buttons[3]}, Button4: {buttons[4]}",
            "Click each button and watch the console."
        ]
        y = 20
        for line in lines:
            text = font.render(line, True, (255, 255, 255))
            screen.blit(text, (20, y))
            y += 30
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
