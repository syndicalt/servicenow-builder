from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI

from jedi_devproject.runtime import StoreFactory, create_runtime_api, load_runtime_settings


def build_app(
    *,
    env_path: Path | None = None,
    store_factory: StoreFactory | None = None,
) -> FastAPI:
    settings = load_runtime_settings(env_path)
    if store_factory is None:
        return create_runtime_api(settings=settings)
    return create_runtime_api(settings=settings, store_factory=store_factory)
