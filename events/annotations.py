from collections.abc import Callable
from functools import wraps
from typing import Any
from events.system import EventError, get_event_system


class Subscription:
    def __init__(self, event_type: str, callback: Any):
        self.event_type = event_type
        self.callback = callback

    def unsubscribe(self):
        get_event_system().unsubscribe(self.event_type, self.callback)

    def subscribe(self):
        get_event_system().subscribe(self.event_type, self.callback)


class _EventMixin:
    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        cls._event_listeners = {
            method._of_event_type: method  # type:ignore
            for method in vars(cls).values()
            if callable(method) and getattr(method, "_is_event_listener", False)
        }

    def __init__(self):
        self._subscriptions: dict[str, Subscription] = {}
        for event_type, func in self.__class__._event_listeners.items():
            bound = func.__get__(self)
            get_event_system().subscribe(event_type, bound)
            self._subscriptions[event_type] = Subscription(event_type, bound)

    def unsubscribe(self, event_type: str):
        sub = self._subscriptions.pop(event_type, None)
        if sub is None:
            raise EventError(f"Not subscribed to event type {event_type}")
        sub.unsubscribe()

    def unsubscribe_all(self):
        for sub in self._subscriptions.values():
            sub.unsubscribe()
        self._subscriptions.clear()


# region internal helpers
def _inject_event_machinery(cls: type) -> type:
    if _EventMixin in cls.__mro__:
        return cls

    original_init = cls.__dict__.get("__init__")

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if original_init is not None:
            original_init(self, *args, **kwargs)
        _EventMixin.__init__(self)

    attrs = dict(cls.__dict__)
    attrs["__init__"] = __init__
    return type(cls.__name__, (_EventMixin, cls), attrs)


# region decorator api
def event_model(*, event_type: str) -> Callable[[type], type]:
    def event_model_decorator(cls: type) -> type:
        cls._event_type = event_type
        cls._is_event_model = True
        get_event_system().register_event_type(event_type, cls)
        return cls
    return event_model_decorator


def event_listener(*, event_type: str) -> Callable:             # type: ignore
    def event_listener_decorator(func: Callable) -> Callable:   # type: ignore
        func._of_event_type = event_type                        # type: ignore
        func._is_event_listener = True                          # type: ignore
        return func                                             # type: ignore
    return event_listener_decorator                             # type: ignore


def subscribes(cls: type) -> type:
    """Class decorator — injects event machinery for @event_listener methods."""
    return _inject_event_machinery(cls)


def event_source(*, event_type: str) -> Callable:                                               # type: ignore
    def event_source_decorator(func: Callable) -> Callable:                                     # type: ignore
        @wraps(func)                                                                    # type: ignore
        def wrapper(self, *args: Any, **kwargs: Any) -> Any:                                    # type: ignore
            event = func(self, *args, **kwargs)                                            # type: ignore                                     
            if not hasattr(event, "_event_type") or event._event_type != event_type:   # type: ignore
                raise EventError(
                    f"Expected event model of type '{event_type}', "
                    f"got {type(event).__name__}"                                               # type: ignore
                )
            event_system = get_event_system()
            if event_system.is_registered_event_type(event_type):
                event_system.fire(event)                                                  # type: ignore
            return event                                                                        # type: ignore
        return wrapper                                                                          # type: ignore
    return event_source_decorator                                                               # type: ignore