"""Main entry point and asynchronous Pygbag game loop for Sipa: Kanto Clicker."""

import asyncio
import sys
import pygame

from core.engine import Engine
from core.events import event_bus
from core.settings import WINDOW_TITLE, TARGET_FPS
from scenes.scene_manager import SceneManager
from scenes.title_scene import TitleScene


async def main() -> None:
    """
    Main asynchronous game loop.
    Pygbag compiles this loop to WebAssembly; 'await asyncio.sleep(0)' yields
    control back to the browser on every frame to avoid locking the UI thread.
    """
    pygame.init()
    pygame.font.init()

    # Initialize display engine and letterboxed canvas scaler
    engine = Engine()

    # Initialize scene director and launch initial TitleScene
    scene_manager = SceneManager()
    scene_manager.switch(TitleScene(scene_manager))

    running = True

    while running:
        # 1. Delta time calculation (clamped to prevent tab hitching)
        dt = engine.tick()

        # 2. Coordinate conversion: window mouse position -> 1280x720 logical space
        raw_mouse_pos = pygame.mouse.get_pos()
        logical_mouse_pos = engine.canvas_to_logical_pos(raw_mouse_pos)

        # 3. Input and OS Event processing
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.VIDEORESIZE:
                # Handle browser window or canvas resizing
                engine.recalculate_viewport(event.w, event.h)

            else:
                # Dispatch event with translated coordinates to active scene
                scene_manager.handle_event(event, logical_mouse_pos)

        # 4. Update scene logic
        scene_manager.update(dt)

        # 5. Render active scene onto 1280x720 logical surface
        scene_manager.draw(engine.logical_surface)

        # 6. Letterbox / pillarbox blit logical surface to the physical window canvas
        engine.render_to_screen()

        # 7. Swap display buffers
        pygame.display.flip()

        # 8. YIELD TO BROWSER (MANDATORY FOR PYGBAG / WEB)
        # Using 0 guarantees the browser refreshes the DOM/canvas without blocking.
        await asyncio.sleep(0)

    # Clean exit for desktop execution
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
