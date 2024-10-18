from typing import Any, TypeVar, Generic, Callable

T = TypeVar('T')

class lazy_property(Generic[T]):
    def __init__(self, func: Callable[[Any], T]) -> None:
        self.func = func
        self.__name__ = func.__name__
        self.__doc__ = func.__doc__

    def __get__(self, instance: Any, owner: Any) -> T:
        if instance is None:
            return self
        if self.__name__ not in instance.__dict__:
            instance.__dict__[self.__name__] = self.func(instance)
        return instance.__dict__[self.__name__]

    def __set__(self, instance: Any, value: T) -> None:
        instance.__dict__[self.__name__] = value

    def __delete__(self, instance: Any) -> None:
        if self.__name__ in instance.__dict__:
            del instance.__dict__[self.__name__]
