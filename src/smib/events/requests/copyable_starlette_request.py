from starlette.requests import Request


class CopyableStarletteRequest:
    def __init__(self, request: Request):
        self._request = request

    def __getattr__(self, attr):
        return getattr(self._request, attr)

    def __deepcopy__(self, memo):
        # Return self to prevent recursion during deepcopy
        return self

    def __getstate__(self):
        # Empty state to prevent deep copying internals
        return {}

    def __setstate__(self, state):
        # Nothing to restore
        pass
