from typing import Any, Callable
from .system import get_event_system

#region class decorators
def event_model(*, event_type: str) -> Callable[[type], type]:
    # marks model as event
    def event_decorator(cls: type) -> type:
        original_init = cls.__init__
        
        def __init__(self, *args, **kwargs):  #type: ignore
            original_init(self, *args, **kwargs) #type: ignore
            self.event_type = event_type

        cls.__init__ = __init__
        return cls
    return event_decorator

def event_listener(cls: type) -> type:
    pass



#region function decorators
def event_source(*, event_type: str, target_id: str | None = None) -> Callable[..., object]:
    # marks function as event source
    def event_source_decorator(func: Callable[..., object]) -> Callable[..., object]:
        def wrapper(self: object, *args: Any, **kwargs: Any) -> None:
            result: object = func(self, *args, **kwargs)
            get_event_system().emit(event_type, result, target_id)
        return wrapper
    return event_source_decorator


