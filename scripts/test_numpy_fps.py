import numpy as np
import pygame
pygame.init()
screen = pygame.display.set_mode((640, 512))
import time
t = time.time()
for i in range(100):
    arr = np.zeros((512, 640), dtype=np.uint8)
    arr[100:400, 100:500] = 7
    palette = np.array([(0,0,0),(180,0,0),(0,160,0),(180,180,0),(0,0,180),(180,0,180),(0,180,180),(180,180,180)]*32, dtype=np.uint8)
    rgb = palette[arr]
    surf = pygame.surfarray.make_surface(np.transpose(rgb, (1,0,2)))
    screen.blit(surf, (0,0))
    pygame.display.flip()
fps = 100 / (time.time() - t)
print(f"numpy surfarray: {fps:.0f} fps")
pygame.quit()
