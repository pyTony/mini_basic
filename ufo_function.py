import numpy as np
import matplotlib.pyplot as plt

# 1. Initialize grid ranges to closely match the image's coordinate bounds
r = np.linspace(0.1, 14, 150)        # Radius vector (avoid zero to fix divide-by-zero)
theta = np.linspace(0, 2 * np.pi, 250) # Circular sweep for fine ring resolution

# 2. Configure a completely black retro display canvas 
fig = plt.figure(figsize=(9, 8), facecolor='black')
ax = fig.add_subplot(111, projection='3d', facecolor='black')

# 3. Plot every single coordinate line transparently (No hidden line removal)
for radius in r:
    # Classic sinc / damped sine function
    z_val = np.sin(radius) / radius
    
    # Map out the ring points in 3D space
    x = radius * np.cos(theta)
    y = radius * np.sin(theta)
    z = np.full_like(theta, z_val)
    
    # alpha=0.6 provides a clean neon glow where the wirelines intersect and bunch up
    ax.plot(x, y, z, color='#00f3ff', linewidth=0.8, alpha=0.6, zorder=1)

# 4. Hide structural axis frameworks to cleanly isolate the asset
ax.axis('off')

# Set specific view angles to perfectly match the original orthographic skew
ax.view_init(elev=26, azim=-45)

# Adjust axes limits to keep the proportions perfectly circular rather than stretched
ax.set_xlim(-15, 15)
ax.set_ylim(-15, 15)
ax.set_zlim(-0.5, 1.2)

plt.show()
