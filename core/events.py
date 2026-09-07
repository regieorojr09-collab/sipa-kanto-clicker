"""Typed event bus and game event definitions for Sipa: Kanto Clicker."""

from enum import Enum, auto
from typing import Any, Callable, Dict, List
import logging

logger = logging.getLogger(__name__)


class GameEvent(Enum):
    """Enumeration of all decoupled game events."""
    # Hit & Rhythm system events
    HIT_RESULT = auto()       # payload: {judgment: str, position: tuple[float, float], timing_delta_ms: float, points: int, combo: int}
    SIPA_LAUNCHED = auto()    # payload: {origin: tuple[float, float], velocity: tuple[float, float], angle: float}
    SIPA_LANDED = auto()      # payload: {position: tuple[float, float], was_miss: bool}

    # Combo & difficulty progression
    COMBO_MILESTONE = auto()  # payload: {combo_count: int}
    PIKON_THRESHOLD = auto()  # payload: {level: int, modifier: str}
    TAYA_CALL = auto()        # payload: {modifier_type: str, message: str}

    # System & Lifecycle
    AUDIO_UNLOCK = auto()     # payload: {} (Triggered on first valid user interaction in browser)
    ROUND_START = auto()      # payload: {chart_id: str}
    ROUND_END = auto()        # payload: {passed: bool, final_score: int, max_combo: int}


# Type alias for event callbacks
EventCallback = Callable[..., None]


class EventBus:
    """
    Central publish/subscribe dispatcher for loosely coupled communication.
    Guarantees thread-safe iteration and defensive dispatch against runtime listener changes.
    """

    def __init__(self) -> None:
        self._subscribers: Dict[GameEvent, List[EventCallback]] = {
            event: [] for event in GameEvent
        }

    def subscribe(self, event: GameEvent, callback: EventCallback) -> None:
        """Register a callback for a specific GameEvent."""
        if not isinstance(event, GameEvent):
            raise TypeError(f"Expected GameEvent enum instance, got {type(event).__name__}")
        if not callable(callback):
            raise TypeError(f"Callback must be callable, got {type(callback).__name__}")

        listeners = self._subscribers.setdefault(event, [])
        if callback not in listeners:
            listeners.append(callback)

    def unsubscribe(self, event: GameEvent, callback: EventCallback) -> None:
        """Unregister a previously registered callback for a specific GameEvent."""
        if event in self._subscribers and callback in self._subscribers[event]:
            self._subscribers[event].remove(callback)

    def publish(self, event: GameEvent, **payload: Any) -> None:
        """
        Dispatch an event to all registered subscribers with arbitrary keyword payload.
        Iterates over a shallow copy of listeners to allow handlers to safely unsubscribe.
        """
        if event not in self._subscribers:
            return

        for callback in list(self._subscribers[event]):
            try:
                callback(**payload)
            except Exception as exc:
                logger.error(
                    "Error executing listener '%s' for event '%s': %s",
                    getattr(callback, "__name__", repr(callback)),
                    event.name,
                    exc,
                    exc_info=True
                )

    def clear(self) -> None:
        """Clear all active subscriptions across all events."""
        for event in self._subscribers:
            self._subscribers[event].clear()


# Shared singleton event bus instance
event_bus: EventBus = EventBus()
