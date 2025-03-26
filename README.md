# StarFox-Inspired 3D Space Shooter

Welcome to **StarFox**, a 3D space shooter game inspired by the classic *Star Fox* series, built using Python, Pygame, and OpenGL. Take control of an Arwing-inspired spacecraft, navigate through an endless terrain, and engage in thrilling combat against enemy TIE Fighter-like ships. Dodge enemy fire, collect power-ups, and rack up points in this fast-paced action game!

## Game Overview

In this game, you pilot a spacecraft through a procedurally generated terrain featuring hills and trees. Enemies spawn ahead of you and move toward your position, firing green laser bullets. Your goal is to destroy enemies, avoid damage, and survive as long as possible while earning points. The game includes sound effects, background music, and a simple HUD displaying your health and score.

### Key Features
- **Player Controls**: Fly your ship using arrow keys (up, down, left, right) and shoot with the spacebar. Use `Q` and `E` to rotate the ship.
- **Enemies**: TIE Fighter-inspired enemy ships that pursue and shoot at you.
- **Combat**: Fire red bullet projectiles to destroy enemies, triggering explosion particle effects.
- **Terrain**: Procedurally generated scrolling terrain with hills and trees.
- **Power-Ups**: Collect yellow cubes to restore health (max 5).
- **Audio**: Background music and sound effects for shooting and explosions.
- **HUD**: Displays your remaining health and current score.
- **Game Over**: When health reaches zero, the game ends. Press any key to restart.

## Prerequisites

To run the game, ensure you have the following installed:
- **Python 3.x** (tested with Python 3.9+)
- **Pygame**: For game framework and audio.
- **PyOpenGL**: For 3D rendering.
- **NumPy**: For mathematical operations.
- **Pywavefront** (optional): For loading custom 3D enemy models (e.g., `mech.obj`).

Install the required libraries using pip:
```bash
pip install pygame pyopengl numpy pywavefront
