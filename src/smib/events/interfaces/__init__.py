from inspect import Signature, Parameter
from typing import TypeVar, Any

from slack_bolt.kwargs_injection.async_args import AsyncArgs


def get_reserved_parameter_names() -> set[str]:
    return set(AsyncArgs.__annotations__.keys())

ParameterType_ = TypeVar("ParameterType_")

def extract_parameter_and_value(parameter_annotation: type[ParameterType_], signature: Signature, args: tuple[Any, ...], kwargs: dict[str, Any]) -> tuple[ParameterType_, str] | None:
    bound = signature.bind(*args, **kwargs)
    bound.apply_defaults()

    parameter = next(
        (param for param in signature.parameters.values() if param.annotation == parameter_annotation),
        None
    )
    return (bound.arguments.get(parameter.name), parameter.name) if parameter else None

def find_annotation_in_signature(parameter_annotation: type[Any], signature: Signature) -> Parameter | None:
    parameter = next(
        (param for param in signature.parameters.values() if param.annotation == parameter_annotation),
        None
    )
    return parameter