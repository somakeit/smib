# Source - https://stackoverflow.com/a
# Posted by Raymond Hettinger, modified by community. See post 'Timeline' for change history
# Retrieved 2025-12-13, License - CC BY-SA 4.0

import functools
import weakref

def weak_lru(maxsize=128, typed=False):
    """LRU Cache decorator that keeps a weak reference to `self`"""
    def wrapper(func):

        @functools.lru_cache(maxsize, typed)
        def _func(_self, *args, **kwargs):
            return func(_self(), *args, **kwargs)

        @functools.wraps(func)
        def inner(self, *args, **kwargs):
            return _func(weakref.ref(self), *args, **kwargs)

        return inner

    return wrapper
