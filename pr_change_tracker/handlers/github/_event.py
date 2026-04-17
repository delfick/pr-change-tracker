import attrs

from pr_change_tracker.protocols import Logger


@attrs.frozen
class Incoming:
    # The json in the body of the request
    body: dict[str, object]

    # Logger instance already bound with relevant information
    logger: Logger

    # Name of the event that triggered the delivery.
    event: str

    # Unique identifier of the webhook.
    hook_id: str

    # A globally unique identifier (GUID) to identify the event.
    delivery: str

    # Unique identifier of the resource where the webhook was created.
    hook_installation_target_id: str

    # Type of resource where the webhook was created.
    hook_installation_target_type: str
