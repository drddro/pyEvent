# pyEvent

Minimal decorator-based event system for Python.

The repository provides a small event bus with three main ideas:

- event models declare an event type
- event sources produce and publish events
- listener classes subscribe methods to event types automatically

The working example is in `example.py`.

## Files

- `events/system.py`: core event bus and global singleton access
- `events/annotations.py`: decorator API and subscription helpers
- `example.py`: end-to-end example showing publish, handle, and unsubscribe

## Core Concepts

### 1. Event models

Use `@event_model(event_type=...)` on a class to mark it as a valid event payload and register its event type with the global event system.

```python
@event_model(event_type="user.created")
@dataclass
class UserCreatedEvent:
    username: str
```

What this does:

- adds `_event_type` to the class
- marks the class as an event model
- registers the event type in the global `EventSystem`

Registration is idempotent. If the event type is already registered, the system keeps the existing registration.

### 2. Event sources

Use `@event_source(event_type=...)` on a method that returns an event model instance.

```python
class UserService:
    @event_source(event_type="user.created")
    def create_user(self, username: str) -> UserCreatedEvent:
        return UserCreatedEvent(username=username)
```

When the method is called:

1. the original method runs
2. the returned object is checked for `_event_type`
3. the returned object's event type must match the decorator's `event_type`
4. if that event type is registered, the event is fired to all listeners
5. the original event object is returned to the caller

If the returned object does not match the declared event type, an `EventError` is raised.

### 3. Event listeners

Use `@event_listener(event_type=...)` on instance methods that should receive events.

```python
class ConsoleAuditLogger:
    @event_listener(event_type="user.created")
    def on_user_created(self, event: UserCreatedEvent) -> None:
        print(event.username)
```

This decorator only marks the method. It does not subscribe anything by itself.

### 4. Subscribing classes

Use `@subscribes` on a class that contains one or more `@event_listener` methods.

```python
@subscribes
class ConsoleAuditLogger:
    @event_listener(event_type="user.created")
    def on_user_created(self, event: UserCreatedEvent) -> None:
        print(event.username)
```

What `@subscribes` does:

- injects event subscription behavior into the class
- on instance creation, finds all listener methods declared on the class
- binds those methods to the instance
- subscribes each bound method to the global event system
- stores subscription handles on the instance

That means subscription happens when you instantiate the class, not when Python imports the module.

## Event Flow

Typical lifecycle:

1. Define an event class with `@event_model`
2. Define a producer method with `@event_source`
3. Define a listener class with `@subscribes`
4. Mark listener methods with `@event_listener`
5. Instantiate the listener class so it subscribes
6. Call the source method
7. The returned event is validated and dispatched
8. Matching listeners are invoked with the event object

## Full Example

From `example.py`:

```python
from dataclasses import dataclass

from events.annotations import event_listener, event_model, event_source, subscribes


USER_CREATED = "user.created"


@event_model(event_type=USER_CREATED)
@dataclass
class UserCreatedEvent:
    username: str


class UserService:
    @event_source(event_type=USER_CREATED)
    def create_user(self, username: str) -> UserCreatedEvent:
        print(f"[service] Creating user: {username}")
        return UserCreatedEvent(username=username)


@subscribes
class ConsoleAuditLogger:
    @event_listener(event_type=USER_CREATED)
    def on_user_created(self, event: UserCreatedEvent) -> None:
        print(f"[listener] Received {USER_CREATED} for: {event.username}")
```

Using it:

```python
logger = ConsoleAuditLogger()
service = UserService()

service.create_user("alice")
logger.unsubscribe(USER_CREATED)
service.create_user("bob")
```

Expected behavior:

- the first call publishes the event and the logger receives it
- after `unsubscribe`, the second call still creates and returns the event, but no listener handles it

## Subscription Management

Instances decorated with `@subscribes` get these methods through the injected mixin:

- `unsubscribe(event_type: str)`: remove the subscription for one event type on that instance
- `unsubscribe_all()`: remove all subscriptions for that instance

If you call `unsubscribe` for an event type that instance is not subscribed to, an `EventError` is raised.

Internally, each subscription is tracked by a small `Subscription` object with:

- `subscribe()`
- `unsubscribe()`

## EventSystem API

The underlying event bus lives in `events/system.py`.

```python
event_system = get_event_system()
```

`get_event_system()` returns a process-wide singleton `EventSystem`.

The main operations are:

- `register_event_type(event_type, model_cls)`
- `is_registered_event_type(event_type)`
- `fire(event)`
- `subscribe(event_type, listener)`
- `unsubscribe(event_type, listener)`

### How dispatch works

When `fire(event)` is called:

- the system reads `event._event_type`
- it verifies that the event type is registered
- it calls every listener currently stored under that event type

If the event object has no `_event_type`, or the event type was never registered, an `EventError` is raised.

## Important Behavior Notes

- The system is global. All subscriptions use the singleton returned by `get_event_system()`.
- Listener registration is instance-based. Creating two listener objects creates two subscriptions.
- Listener discovery only looks for methods marked with `@event_listener` on the class.
- `subscribe()` can add listeners for event types that were not explicitly registered yet, because the internal listener map uses `setdefault`. However, `fire()` still requires the event type to be registered.
- `unsubscribe()` removes listeners by identity from the stored listener list.

## Running the Example

Run:

```bash
python example.py
```

You should see:

1. a user creation message from the service
2. a listener message for the first event
3. an unsubscribe message from the demo
4. no listener output for the second event

## When To Use This

This pattern works well when you want:

- loose coupling between producers and consumers
- a simple in-process pub/sub mechanism
- decorator-based registration with minimal boilerplate

It is not a distributed event bus, message queue, or persistent event store. Everything is in-process and in-memory.