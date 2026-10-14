"""In-memory event logger for live call tracking in the web UI."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
import threading
from typing import List, Optional


@dataclass
class CallEvent:
    timestamp: str
    stage: str
    message: str
    call_uuid: Optional[str] = None
    details: Optional[dict] = None


class EventTracker:
    def __init__(self, max_events: int = 100):
        self._events: List[CallEvent] = []
        self._lock = threading.Lock()
        self._max_events = max_events

    def add_event(self, stage: str, message: str, call_uuid: Optional[str] = None, details: Optional[dict] = None) -> CallEvent:
        event = CallEvent(
            timestamp=datetime.now().strftime("%H:%M:%S"),
            stage=stage,
            message=message,
            call_uuid=call_uuid,
            details=details or {},
        )
        with self._lock:
            self._events.append(event)
            if len(self._events) > self._max_events:
                self._events.pop(0)
        return event

    def get_events(self, since_index: int = 0) -> List[dict]:
        with self._lock:
            return [asdict(e) for e in self._events[since_index:]]

    def clear(self):
        with self._lock:
            self._events.clear()


event_tracker = EventTracker()
