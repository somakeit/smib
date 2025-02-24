import inspect


def dynamic_function_caller(func, **kwargs):
    """
    Dynamically calls a function using arguments from kwargs that match the function's signature.

    :param func: The function to call
    :param kwargs: Dictionary containing arguments to pass to the function
    :return: The return value of the function
    """
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
            raise ValueError(f"Missing required parameter: {param}")

    # Call the function with the filtered arguments
    return func(**filtered_kwargs)


# Example function with a variety of arguments
def example_function(http, schedule):
    return f"http={http}, schedule={schedule}"


if __name__ == "__main__":
    # Defined arguments
    arguments = {
        "slack": 1,
        "http": 2,
        "mqtt": 30,
        "schedule": 100
    }

    # Dynamically call example_function using dynamic_function_caller
    result = dynamic_function_caller(example_function, **arguments)
    print(result)  # Output: a=1, b=2, c=30, d=20
