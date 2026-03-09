from __future__ import annotations

from collections.abc import Callable
from typing import Any


class Registry:
    """Simple name -> factory registry used across platform modules."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Callable[..., Any]]] = {
            "signals": {},
            "representations": {},
            "experiments": {},
            "analysis": {},
            "pose_extractors": {},
        }

    def register(self, category: str, name: str, factory: Callable[..., Any]) -> None:
        if category not in self._store:
            raise KeyError(f"Unknown registry category: {category}")
        self._store[category][name] = factory

    def get(self, name: str) -> Callable[..., Any]:
        for category in self._store.values():
            if name in category:
                return category[name]
        raise KeyError(f"Unregistered component: {name}")

    def get_from_category(self, category: str, name: str) -> Callable[..., Any]:
        if name not in self._store.get(category, {}):
            raise KeyError(f"Unregistered {category} component: {name}")
        return self._store[category][name]

    def list_signals(self) -> list[str]:
        return sorted(self._store["signals"])

    def list_representations(self) -> list[str]:
        return sorted(self._store["representations"])

    def list_experiments(self) -> list[str]:
        return sorted(self._store["experiments"])

    def list_analysis_tasks(self) -> list[str]:
        return sorted(self._store["analysis"])

    def list_pose_extractors(self) -> list[str]:
        return sorted(self._store["pose_extractors"])


registry = Registry()


def register_signal(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(factory: Callable[..., Any]) -> Callable[..., Any]:
        registry.register("signals", name, factory)
        return factory

    return decorator


def register_representation(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(factory: Callable[..., Any]) -> Callable[..., Any]:
        registry.register("representations", name, factory)
        return factory

    return decorator


def register_experiment(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(factory: Callable[..., Any]) -> Callable[..., Any]:
        registry.register("experiments", name, factory)
        return factory

    return decorator


def register_analysis(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(factory: Callable[..., Any]) -> Callable[..., Any]:
        registry.register("analysis", name, factory)
        return factory

    return decorator


def register_pose_extractor(name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    def decorator(factory: Callable[..., Any]) -> Callable[..., Any]:
        registry.register("pose_extractors", name, factory)
        return factory

    return decorator
