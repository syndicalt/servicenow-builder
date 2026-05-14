from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from jedi_devproject.fulfillment_worker import FulfillmentWorkerResult
from jedi_devproject.runtime import (
    RuntimeSettings,
    load_runtime_settings,
    process_one_runtime_fulfillment,
)

DEFAULT_ENV_PATH = Path("/app/.env")
RuntimeProcessor = Callable[[RuntimeSettings], FulfillmentWorkerResult]


def process_runtime_settings(settings: RuntimeSettings) -> FulfillmentWorkerResult:
    return process_one_runtime_fulfillment(settings=settings)


def run_once(
    *,
    settings: RuntimeSettings,
    processor: RuntimeProcessor = process_runtime_settings,
) -> FulfillmentWorkerResult:
    return processor(settings)


def main() -> int:
    result = run_once(settings=load_runtime_settings(DEFAULT_ENV_PATH))
    print(result.model_dump_json())
    return 0 if result.status in {"idle", "completed"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
