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


def main() -> None:
	logger = ConsoleAuditLogger()
	service = UserService()

	print("[demo] First event should be handled")
	service.create_user("alice")

	print("[demo] Unsubscribing listener")
	logger.unsubscribe(USER_CREATED)

	print("[demo] Second event should NOT be handled")
	service.create_user("bob")


if __name__ == "__main__":
	main()
