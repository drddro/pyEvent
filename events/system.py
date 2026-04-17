
_event_system: 'EventSystem | None' = None

def get_event_system() -> 'EventSystem':
    global _event_system
    if _event_system is None:
        _event_system = EventSystem()
    return _event_system

class EventSystem:


    def register_event_source(self, source: object) -> None:
        pass

    def unregister_event_source(self, source: object) -> None:
        pass

    def emit(self, event_type: str, event_model: object, target_id: str | None = None) -> None:
        pass

    def subscribe(self, event_type: str, event_listener: object) -> None:
        pass

    def unsubscribe(self, event_type: str, event_listener: object) -> None:
        pass


class _Subscriber:

    def __init__(self, event_listener: object):
        pass
