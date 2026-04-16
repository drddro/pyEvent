from events import system as event_system


event_system.init()

from events.annotations import event_listener, event_model, event_source


@event_model(event_type="user.created")
class UserCreatedEvent:
	type: str
	target: object | None

	def __init__(self, username: str):
		self.username = username


@event_listener(event_type="user.created")
def print_user_created(event: UserCreatedEvent) -> None:
	print(f"received event '{event.type}' for user '{event.username}'")


@event_source(event_type="user.created")
def create_user(username: str) -> UserCreatedEvent:
	print(f"creating user '{username}'")
	return UserCreatedEvent(username)


def main() -> None:
	create_user("alice")


if __name__ == "__main__":
	main()
