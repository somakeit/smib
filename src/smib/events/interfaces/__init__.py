from slack_bolt.kwargs_injection.async_args import AsyncArgs


def get_reserved_parameter_names() -> set[str]:
    return set(AsyncArgs.__annotations__.keys())