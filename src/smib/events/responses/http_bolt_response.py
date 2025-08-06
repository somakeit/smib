from typing import Sequence, Any

from slack_bolt import BoltResponse


class HttpBoltResponse(BoltResponse):
    def __init__(
            self,
            *,
            status: int,
            body: str | dict[str, Any] = "",
            headers: dict[str, str | Sequence[str]] | None = None,
            fastapi_response: Any | None = None,
            fastapi_kwargs: dict[str, Any] | None = None
    ):
        """The response from a Bolt app with custom fields.

        Args:
            status: HTTP status code
            body: The response body (dict and str are supported)
            headers: The response headers.
            fastapi_response: Actual fastapi response
            fastapi_kwargs: Resulting fastapi kwargs
        """
        super().__init__(status=status, body=body, headers=headers)

        # Initialize custom fields
        self.fastapi_response = fastapi_response
        self.fastapi_kwargs = fastapi_kwargs

    def __repr__(self) -> str:
        base_repr = super().__repr__()
        return (
            f"{base_repr}, fastapi_response={self.fastapi_response}, "
            f"fastapi_kwargs={self.fastapi_kwargs}"
        )
