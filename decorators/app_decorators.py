import inspect
from functools import wraps
from typing import Any, Callable, ParamSpec, TypeVar
from enum import IntEnum

P = ParamSpec("P")
R = TypeVar("R")

# Decorator to replace flags if
def _resolve_config(instance: Any) -> Any:
    """Resolve config object from a service instance supporting both naming conventions."""
    config = getattr(instance, "config", None) or getattr(instance, "config_service", None)
    if config is None:
        raise AttributeError(
            f"{type(instance).__name__} must define 'config' or 'config_service' to use feature-flag decorators."
        )
    return config


def _eval_flag(instance: Any, key: str, default_if_null: bool) -> bool:
    config = _resolve_config(instance)
    raw_value = config.get(key)
    return default_if_null if raw_value is None else bool(raw_value)


def _flag_condition(
    key: str,
    expected: bool,
    default_if_null: bool,
    fallback_factory: Callable[[], Any] | None = None,
):
    def decorator(func):
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                if _eval_flag(self, key, default_if_null) == expected:
                    return await func(self, *args, **kwargs)
                return fallback_factory() if fallback_factory is not None else None  

            return async_wrapper

        @wraps(func)
        def sync_wrapper(self, *args, **kwargs):
            if _eval_flag(self, key, default_if_null) == expected:
                return func(self, *args, **kwargs)
            return fallback_factory() if fallback_factory is not None else None  

        return sync_wrapper

    return decorator

def when_enabled(
    key: str,
    default: bool = False,
    fallback_factory: Callable[[], Any] | None = None,
):
    return _flag_condition(key, expected=True, default_if_null=default, fallback_factory=fallback_factory)


def skip_when_enabled(
    key: str,
    default: bool = True,
    fallback_factory: Callable[[], Any] | None = None,
):
    return _flag_condition(key, expected=False, default_if_null=default, fallback_factory=fallback_factory)


def when_any_enabled(
    *keys: str,
    default: bool = False,
    fallback_factory: Callable[[], Any] | None = None,
) -> Callable[[Callable[P, R]], Callable[P, R | Any]]:
    """Executes the method if at least one of the keys is enabled (OR logic)."""
    def decorator(func: Callable[P, R]) -> Callable[P, R | Any]:
        if inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(self: Any, *args: P.args, **kwargs: P.kwargs) -> Any:
                if any(_eval_flag(self, key, default) for key in keys):
                    return await func(self, *args, **kwargs)
                return fallback_factory() if fallback_factory is not None else None  

            return async_wrapper

        @wraps(func)
        def sync_wrapper(self: Any, *args: P.args, **kwargs: P.kwargs) -> R | Any:
            if any(_eval_flag(self, key, default) for key in keys):
                return func(self, *args, **kwargs)
            return fallback_factory() if fallback_factory is not None else None 

        return sync_wrapper

    return decorator
# End Decorator

#Decorater to convert string to int enum
def keys_from_str(cls):
    names = cls.__doc__.replace(",", " ").split()
    return IntEnum(cls.__name__, {name: i for i, name in enumerate(names)})
#End Decorator