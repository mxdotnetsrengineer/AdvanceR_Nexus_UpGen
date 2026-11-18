import inspect
from functools import wraps
from typing import Any, Callable, ParamSpec, TypeVar
from enum import IntEnum

P = ParamSpec("P")
R = TypeVar("R")

# Decorator to replace flags if
def _eval_flag(config: Any, key: str, default_if_null: bool) -> bool:
    raw_value = config.get(key)
    return default_if_null if raw_value is None else bool(raw_value)

def _flag_condition(key: str, expected: bool, default_if_null: bool):
    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                if _eval_flag(self.config, key, default_if_null) == expected:
                    return await func(self, *args, **kwargs)
                return None
            return async_wrapper

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            if _eval_flag(self.config, key, default_if_null) == expected:
                return func(self, *args, **kwargs)
            return None
        return sync_wrapper
    return decorator

def when_enabled(key: str, default: bool = False):
    return _flag_condition(key, expected=True, default_if_null=default)

def skip_when_enabled(key: str, default: bool = True):
    return _flag_condition(key, expected=False, default_if_null=default)

def when_any_enabled(*keys: str, default: bool = False) -> Callable[[Callable[P, R]], Callable[P, R | None]]:
    """Executes the method if at least one of the keys is enabled (OR logic)."""
    def decorator(func: Callable[P, R]) -> Callable[P, R | None]:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(self: Any, *args: P.args, **kwargs: P.kwargs) -> Any:
                if any(_eval_flag(self.config, key, default) for key in keys):
                    return await func(self, *args, **kwargs)
                return None
            return async_wrapper  # type: ignore[return-value]

        @wraps(func)
        def sync_wrapper(self: Any, *args: P.args, **kwargs: P.kwargs) -> R | None:
            if any(_eval_flag(self.config, key, default) for key in keys):
                return func(self, *args, **kwargs)
            return None
        return sync_wrapper
    return decorator
# End Decorator

#Decorater to convert string to int enum
def keys_from_str(cls):
    names = cls.__doc__.replace(",", " ").split()
    return IntEnum(cls.__name__, {name: i for i, name in enumerate(names)})
#End Decorator