from typing import Any, TypeVar, Generic, Callable, Union

T = TypeVar('T')


class lazy_property(Generic[T]):
    def __init__(self, func: Callable[[Any], T]) -> None:
        self.func = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __get__(self, instance: Any, owner: Any) -> Union[T, 'lazy_property[T]']:
        if instance is None:
            return self  # Return self if accessed through the class

        # Check if the property is already computed
        if self.__name__ not in instance.__dict__:
            calculated_value: T = self.func(instance)  # Compute the value
            instance.__dict__[self.__name__] = calculated_value
        else:
            cached_value: T = instance.__dict__[self.__name__]  # Retrieve the cached value
            return cached_value

        return calculated_value  # Return the computed value

    def __set__(self, instance: Any, value: T) -> None:
        instance.__dict__[self.__name__] = value

    def __delete__(self, instance: Any) -> None:
        if self.__name__ in instance.__dict__:
            del instance.__dict__[self.__name__]
