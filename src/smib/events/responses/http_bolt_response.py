from typing import Union, Optional, Dict, Sequence

from slack_bolt import BoltResponse


class HttpBoltResponse(BoltResponse):
    def __init__(
            self,
            *,
            status: int,
            body: Union[str, dict] = "",
            headers: Optional[Dict[str, Union[str, Sequence[str]]]] = None,
            fastapi_response: Optional[any] = None,
            fastapi_kwargs: Optional[dict] = None
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

    def __repr__(self):
        base_repr = super().__repr__()
        return (
            f"{base_repr}, fastapi_response={self.fastapi_response}, "
            f"fastapi_kwargs={self.fastapi_kwargs}"
        )
