"""Stack-based scene management and abstract Scene interface for Sipa: Kanto Clicker."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional
import pygame
from pygame.math import Vector2


class Scene(ABC):
    """
    Abstract base class for all game scenes (Title, Play, Pause, Results).
    Enforces a uniform lifecycle and explicit event/update/render passes.
    """

    def __init__(self, manager: "SceneManager") -> None:
        self.manager: "SceneManager" = manager

    def on_enter(self, **kwargs: Any) -> None:
        """Called immediately when this scene becomes the active top of the stack."""
        pass

    def on_exit(self) -> None:
        """Called when this scene is removed or suspended from the active stack."""
        pass

    @abstractmethod
    def handle_event(self, event: pygame.event.Event, logical_mouse_pos: Vector2) -> None:
        """Process user input with mouse coordinates mapped to logical 1280x720 space."""
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """Advance scene logic by delta time (in seconds)."""
        pass

    @abstractmethod
    def draw(self, surface: pygame.Surface) -> None:
        """Render all scene visuals directly to the 1280x720 logical surface."""
        pass


class SceneManager:
    """
    Stack-based scene director supporting:
    - push(): Adds a modal scene over the current (e.g. Pause overlay).
    - pop(): Removes the top scene and resumes the one beneath it.
    - switch(): Replaces the current scene tree with a new active scene.
    """

    def __init__(self) -> None:
        self._stack: List[Scene] = []

    @property
    def current_scene(self) -> Optional[Scene]:
        """Returns the currently active scene at the top of the stack."""
        return self._stack[-1] if self._stack else None

    @property
    def is_empty(self) -> bool:
        """Checks if any scene is currently active."""
        return len(self._stack) == 0

    def push(self, scene: Scene, **kwargs: Any) -> None:
        """Pushes a new scene onto the stack, making it active without destroying previous scenes."""
        if self.current_scene:
            self.current_scene.on_exit()
        self._stack.append(scene)
        scene.on_enter(**kwargs)

    def pop(self) -> Optional[Scene]:
        """Pops and exits the active top scene, resuming the previous one if available."""
        if not self._stack:
            return None
        popped_scene = self._stack.pop()
        popped_scene.on_exit()
        if self.current_scene:
            self.current_scene.on_enter()
        return popped_scene

    def switch(self, scene: Scene, **kwargs: Any) -> None:
        """Empties the existing scene stack and sets the provided scene as the sole active scene."""
        while self._stack:
            self._stack.pop().on_exit()
        self._stack.append(scene)
        scene.on_enter(**kwargs)

    def handle_event(self, event: pygame.event.Event, logical_mouse_pos: Vector2) -> None:
        """Dispatches input events to the active top scene."""
        if self.current_scene:
            self.current_scene.handle_event(event, logical_mouse_pos)

    def update(self, dt: float) -> None:
        """Updates the active top scene."""
        if self.current_scene:
            self.current_scene.update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        """Renders the active top scene to the logical surface."""
        if self.current_scene:
            self.current_scene.draw(surface)
