from inspect import Signature
from typing import TypeVar

from slack_bolt.kwargs_injection.async_args import AsyncArgs


def get_reserved_parameter_names() -> set[str]:
    return set(AsyncArgs.__annotations__.keys())

ParameterType_ = TypeVar("ParameterType_")

def extract_parameter_and_value(parameter_annotation: type[ParameterType_], signature: Signature, args, kwargs) -> tuple[ParameterType_, str]:
    bound = signature.bind(*args, **kwargs)
    bound.apply_defaults()

    parameter = next(
        (param for param in signature.parameters.values() if param.annotation == parameter_annotation),
        None
    )
    parameter_value = bound.arguments.get(parameter.name) if parameter else None
    return parameter_value, parameter.name

def find_annotation_in_signature(parameter_annotation: type[ParameterType_], signature: Signature) -> ParameterType_ | None:
    parameter = next(
        (param for param in signature.parameters.values() if param.annotation == parameter_annotation),
        None
    )
    return parameter