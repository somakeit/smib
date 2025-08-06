from collections.abc import Callable
from typing import Any


def dynamic_caller(func: Callable[..., Any], **kwargs: Any) -> Any:
    """
    Dynamically calls a function using arguments from kwargs that match the function's signature.

    :param func: The function to call
    :param kwargs: Dictionary containing arguments to pass to the function
    :return: The return value of the function
    """
    import inspect

    # Get the signature of the function
    sig = inspect.signature(func)

    # Filter kwargs to only include the parameters in the function's signature
    filtered_kwargs = {k: v for k, v in kwargs.items() if k in sig.parameters}

    # Ensure all required arguments are provided
    required_params = [
        param for param, details in sig.parameters.items()
        if details.default is inspect.Parameter.empty and details.kind in (
            inspect.Parameter.POSITIONAL_OR_KEYWORD, inspect.Parameter.KEYWORD_ONLY)
    ]
    for param in required_params:
        if param not in filtered_kwargs:
            raise ValueError(f"Invalid required parameter: {param}")

    # Call the function with the filtered arguments
    return func(**filtered_kwargs)
