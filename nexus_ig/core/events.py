"""Event dispatch system for Nexus IG Bot."""


class EventDispatcher:
    def __init__(self):
        self._listeners = {}

    def on(self, event_name: str, listener):
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(listener)

    def emit(self, event_name: str, *args, **kwargs):
        for listener in self._listeners.get(event_name, []):
            try:
                listener(*args, **kwargs)
            except Exception as exc:
                print(f"Event error ({event_name}): {exc}")

events = EventDispatcher()
