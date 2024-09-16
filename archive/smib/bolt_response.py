from typing import Dict, Sequence, Union, Optional
import json
from http.cookies import SimpleCookie

from slack_bolt.response import BoltResponse


class CustomBoltResponse(BoltResponse):
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
            f"{base_repr}, custom_field={self.fastapi_response}, "
            f"another_custom_field={self.fastapi_kwargs}"
        )
