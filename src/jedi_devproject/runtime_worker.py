from __future__ import annotations

import json
import logging
import math
import os
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from enum import Enum
from functools import partial
from pathlib import Path
from time import monotonic as monotonic_seconds
from time import sleep as sleep_seconds
from typing import Any, Protocol, Self, cast

from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from pydantic_core import PydanticSerializationError

from jedi_devproject.alert_delivery import (
    emit_alert_webhook,
    stale_requeue_alert,
    worker_failure_alert,
)
from jedi_devproject.alert_webhook_url import validate_alert_webhook_url
from jedi_devproject.exception_diagnostics import exception_diagnostic_message
from jedi_devproject.fulfillment_worker import FulfillmentWorkerResult
from jedi_devproject.numeric_settings import (
    parse_optional_ascii_decimal_float,
    parse_optional_base10_int,
)
from jedi_devproject.operational_store import (
    MAX_RETENTION_PRUNE_BATCH_SIZE,
    RETENTION_ARTIFACT_BLOB_DAYS_ENV,
    RETENTION_JOB_EVENT_DAYS_ENV,
    RETENTION_PRUNE_BATCH_SIZE_ENV,
    FulfillmentJobRecord,
    RetentionPolicy,
    RetentionPruneReport,
    connect_operational_store,
    load_retention_policy,
)
from jedi_devproject.runtime import (
    RuntimeConfigError,
    RuntimeSettings,
    load_runtime_settings,
    process_one_runtime_fulfillment,
)
from jedi_devproject.runtime_config import (
    MAX_PRODUCTION_ALERT_WEBHOOK_BODY_BYTES,
    _database_url_errors,
    _direct_optional_runtime_setting_text,
    _runtime_environment,
    _runtime_role,
    _runtime_setting_int,
    _runtime_setting_text,
)
from jedi_devproject.runtime_redaction import _redact_diagnostic_text
from jedi_devproject.servicenow import HttpTransport, UrllibTransport, load_dotenv_values
from jedi_devproject.url_query_safety import has_whitespace_or_control_character

LOGGER = logging.getLogger(__name__)
DEFAULT_ENV_PATH = Path("/app/.env")
DEFAULT_PRUNE_INTERVAL_SECONDS = 3600.0
DEFAULT_STALE_JOB_REQUEUE_INTERVAL_SECONDS = 3600.0
DEFAULT_STALE_JOB_REQUEUE_BATCH_SIZE = 10
MAX_STALE_JOB_REQUEUE_BATCH_SIZE = 100
MAX_RUNNING_JOB_STALE_AFTER_SECONDS = 24 * 60 * 60
MAX_WORKER_IDLE_SLEEP_SECONDS = 300.0
MAX_MAINTENANCE_INTERVAL_SECONDS = 24 * 60 * 60.0
MAX_WORKER_MAX_ITERATIONS = 10_000
RUNTIME_WORKER_REPORT_NON_FINITE_DIAGNOSTIC = (
    "runtime worker report contains non-finite numeric values"
)
RUNTIME_WORKER_REPORT_NON_JSON_DIAGNOSTIC = (
    "runtime worker report contains non-JSON values"
)
RuntimeProcessor = Callable[[RuntimeSettings], FulfillmentWorkerResult]
Sleeper = Callable[[float], None]
Pruner = Callable[[], object]
StaleJobRecoverer = Callable[[], object]
AlertEmitter = Callable[[FulfillmentWorkerResult], None]
StaleJobRequeueAlertEmitter = Callable[["StaleJobRequeueReport"], None]
Clock = Callable[[], float]


class PrunableStore(Protocol):
    def __enter__(self) -> PrunableStore: ...

    def __exit__(self, *_args: object) -> None: ...

    def prune_expired_records(
        self,
        *,
        policy: RetentionPolicy,
        now: datetime | None = None,
    ) -> RetentionPruneReport: ...


PruneStoreFactory = Callable[[str], PrunableStore]
DEFAULT_PRUNE_STORE_FACTORY = cast(PruneStoreFactory, connect_operational_store)


class StaleJobRecoveryStore(Protocol):
    def __enter__(self) -> StaleJobRecoveryStore: ...

    def __exit__(self, *_args: object) -> None: ...

    def requeue_stale_running_jobs(
        self,
        *,
        stale_before: datetime,
        limit: int,
        message: str,
    ) -> list[FulfillmentJobRecord]: ...


StaleJobRecoveryStoreFactory = Callable[[str], StaleJobRecoveryStore]
DEFAULT_STALE_JOB_RECOVERY_STORE_FACTORY = cast(
    StaleJobRecoveryStoreFactory,
    connect_operational_store,
)


class RuntimeWorkerLoopSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    iterations: int
    completed: int
    idle: int
    failed: int
    alerts_emitted: int = 0
    alert_failures: int = 0
    prune_failures: int = 0
    stale_job_recovery_failures: int = 0
    stopped_reason: str


class RuntimeWorkerSettings(BaseModel):
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra="forbid",
        hide_input_in_errors=True,
    )

    runtime: RuntimeSettings
    max_iterations: int | None = None
    idle_sleep_seconds: float = 5.0
    stop_on_failure: bool = False
    retention: RetentionPolicy = RetentionPolicy()
    prune_interval_seconds: float = DEFAULT_PRUNE_INTERVAL_SECONDS
    stale_job_requeue_enabled: bool = False
    stale_job_requeue_interval_seconds: float = DEFAULT_STALE_JOB_REQUEUE_INTERVAL_SECONDS
    stale_job_requeue_batch_size: int = DEFAULT_STALE_JOB_REQUEUE_BATCH_SIZE

    @field_validator("max_iterations")
    @classmethod
    def _positive_max_iterations(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("JEDI_WORKER_MAX_ITERATIONS must be greater than 0 when configured")
        if value is not None and value > MAX_WORKER_MAX_ITERATIONS:
            raise ValueError(
                "JEDI_WORKER_MAX_ITERATIONS must be at most "
                f"{MAX_WORKER_MAX_ITERATIONS} when configured"
            )
        return value

    @field_validator("idle_sleep_seconds")
    @classmethod
    def _bounded_idle_sleep_seconds(cls, value: float) -> float:
        if value > MAX_WORKER_IDLE_SLEEP_SECONDS:
            raise ValueError(
                "JEDI_WORKER_IDLE_SLEEP_SECONDS must be at most "
                f"{MAX_WORKER_IDLE_SLEEP_SECONDS:g}"
            )
        return value

    @field_validator("prune_interval_seconds")
    @classmethod
    def _positive_prune_interval(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("JEDI_RETENTION_PRUNE_INTERVAL_SECONDS must be greater than 0")
        if value > MAX_MAINTENANCE_INTERVAL_SECONDS:
            raise ValueError(
                "JEDI_RETENTION_PRUNE_INTERVAL_SECONDS must be at most "
                f"{MAX_MAINTENANCE_INTERVAL_SECONDS:g}"
            )
        return value

    @field_validator("stale_job_requeue_interval_seconds")
    @classmethod
    def _positive_stale_requeue_interval(cls, value: float) -> float:
        if value <= 0:
            raise ValueError("JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS must be greater than 0")
        if value > MAX_MAINTENANCE_INTERVAL_SECONDS:
            raise ValueError(
                "JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS must be at most "
                f"{MAX_MAINTENANCE_INTERVAL_SECONDS:g}"
            )
        return value

    @field_validator("stale_job_requeue_batch_size")
    @classmethod
    def _positive_stale_requeue_batch_size(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("JEDI_STALE_JOB_REQUEUE_BATCH_SIZE must be greater than 0")
        if value > MAX_STALE_JOB_REQUEUE_BATCH_SIZE:
            raise ValueError(
                "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE must be at most "
                f"{MAX_STALE_JOB_REQUEUE_BATCH_SIZE}"
            )
        return value

    @model_validator(mode="after")
    def _positive_idle_sleep_for_unbounded_workers(self) -> Self:
        if self.max_iterations is None and self.idle_sleep_seconds <= 0:
            raise ValueError(
                "JEDI_WORKER_IDLE_SLEEP_SECONDS must be greater than 0 for unbounded worker loops"
            )
        return self

    @model_validator(mode="after")
    def _reject_stop_on_failure_in_production(self) -> Self:
        if self.runtime.runtime_environment == "production" and self.stop_on_failure:
            raise ValueError("JEDI_WORKER_STOP_ON_FAILURE must be false in production")
        return self


class StaleJobRequeueReport(BaseModel):
    model_config = ConfigDict(extra="forbid", hide_input_in_errors=True)

    enabled: bool
    requeued_at: datetime
    stale_before: datetime
    stale_after_seconds: int
    requeued_count: int
    job_ids: list[str]


def load_worker_settings(env_path: Path | None = DEFAULT_ENV_PATH) -> RuntimeWorkerSettings:
    values = dict(os.environ)
    if env_path is not None and env_path.exists():
        values.update(load_dotenv_values(env_path))
    stale_job_requeue_batch_size = _optional_int(
        values.get("JEDI_STALE_JOB_REQUEUE_BATCH_SIZE"),
        name="JEDI_STALE_JOB_REQUEUE_BATCH_SIZE",
    )
    if stale_job_requeue_batch_size is None:
        stale_job_requeue_batch_size = DEFAULT_STALE_JOB_REQUEUE_BATCH_SIZE
    return RuntimeWorkerSettings(
        runtime=load_runtime_settings(env_path),
        max_iterations=_optional_int(
            values.get("JEDI_WORKER_MAX_ITERATIONS"),
            name="JEDI_WORKER_MAX_ITERATIONS",
        ),
        idle_sleep_seconds=_optional_float(
            values.get("JEDI_WORKER_IDLE_SLEEP_SECONDS"),
            name="JEDI_WORKER_IDLE_SLEEP_SECONDS",
            default=5.0,
        ),
        stop_on_failure=_bool_value(
            values.get("JEDI_WORKER_STOP_ON_FAILURE"),
            name="JEDI_WORKER_STOP_ON_FAILURE",
        ),
        retention=load_retention_policy(values),
        prune_interval_seconds=_optional_float(
            values.get("JEDI_RETENTION_PRUNE_INTERVAL_SECONDS"),
            name="JEDI_RETENTION_PRUNE_INTERVAL_SECONDS",
            default=DEFAULT_PRUNE_INTERVAL_SECONDS,
        ),
        stale_job_requeue_enabled=_bool_value(
            values.get("JEDI_STALE_JOB_REQUEUE_ENABLED"),
            name="JEDI_STALE_JOB_REQUEUE_ENABLED",
        ),
        stale_job_requeue_interval_seconds=_optional_float(
            values.get("JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS"),
            name="JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS",
            default=DEFAULT_STALE_JOB_REQUEUE_INTERVAL_SECONDS,
        ),
        stale_job_requeue_batch_size=stale_job_requeue_batch_size,
    )


def prune_operational_store(
    *,
    settings: RuntimeSettings,
    policy: RetentionPolicy,
    store_factory: PruneStoreFactory = DEFAULT_PRUNE_STORE_FACTORY,
) -> RetentionPruneReport:
    _validate_retention_prune_policy(policy)
    database_url = _maintenance_database_url(settings)
    with store_factory(database_url) as store:
        report = store.prune_expired_records(policy=policy)
    print(_runtime_report_json(report))
    return report


def _validate_retention_prune_policy(policy: RetentionPolicy) -> None:
    _validate_optional_positive_int_setting(
        getattr(policy, "artifact_blob_retention_days", None),
        setting_name=RETENTION_ARTIFACT_BLOB_DAYS_ENV,
    )
    _validate_optional_positive_int_setting(
        getattr(policy, "job_event_retention_days", None),
        setting_name=RETENTION_JOB_EVENT_DAYS_ENV,
    )
    batch_size = getattr(policy, "prune_batch_size", None)
    if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError(f"{RETENTION_PRUNE_BATCH_SIZE_ENV} must be greater than 0")
    if batch_size > MAX_RETENTION_PRUNE_BATCH_SIZE:
        raise ValueError(
            f"{RETENTION_PRUNE_BATCH_SIZE_ENV} must be at most "
            f"{MAX_RETENTION_PRUNE_BATCH_SIZE}"
        )


def _validate_optional_positive_int_setting(value: object, *, setting_name: str) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{setting_name} must be greater than 0")


def requeue_stale_running_jobs(
    *,
    settings: RuntimeSettings,
    stale_after_seconds: int,
    batch_size: int,
    store_factory: StaleJobRecoveryStoreFactory = DEFAULT_STALE_JOB_RECOVERY_STORE_FACTORY,
    now: datetime | None = None,
) -> StaleJobRequeueReport:
    _validate_stale_requeue_controls(
        stale_after_seconds=stale_after_seconds,
        batch_size=batch_size,
    )
    database_url = _maintenance_database_url(settings)
    requeued_at = now or datetime.now(UTC)
    stale_before = requeued_at - timedelta(seconds=stale_after_seconds)
    message = f"Stale running job requeued after {stale_after_seconds} seconds without update"
    with store_factory(database_url) as store:
        jobs = store.requeue_stale_running_jobs(
            stale_before=stale_before,
            limit=batch_size,
            message=message,
        )
    report = StaleJobRequeueReport(
        enabled=True,
        requeued_at=requeued_at,
        stale_before=stale_before,
        stale_after_seconds=stale_after_seconds,
        requeued_count=len(jobs),
        job_ids=[job.job_id for job in jobs],
    )
    print(_runtime_report_json(report))
    return report


def _maintenance_database_url(settings: RuntimeSettings) -> str:
    database_url = _runtime_setting_text(settings.database_url, name="DATABASE_URL")
    errors = _database_url_errors(settings)
    if errors:
        raise RuntimeConfigError("; ".join(errors))
    return database_url


def _validate_stale_requeue_controls(
    *,
    stale_after_seconds: object,
    batch_size: object,
) -> None:
    if (
        isinstance(stale_after_seconds, bool)
        or not isinstance(stale_after_seconds, int)
        or stale_after_seconds <= 0
    ):
        raise ValueError("JEDI_RUNNING_JOB_STALE_AFTER_SECONDS must be greater than 0")
    if stale_after_seconds > MAX_RUNNING_JOB_STALE_AFTER_SECONDS:
        raise ValueError(
            "JEDI_RUNNING_JOB_STALE_AFTER_SECONDS must be at most "
            f"{MAX_RUNNING_JOB_STALE_AFTER_SECONDS}"
        )
    if isinstance(batch_size, bool) or not isinstance(batch_size, int) or batch_size <= 0:
        raise ValueError("JEDI_STALE_JOB_REQUEUE_BATCH_SIZE must be greater than 0")
    if batch_size > MAX_STALE_JOB_REQUEUE_BATCH_SIZE:
        raise ValueError(
            "JEDI_STALE_JOB_REQUEUE_BATCH_SIZE must be at most "
            f"{MAX_STALE_JOB_REQUEUE_BATCH_SIZE}"
        )


def process_runtime_settings(settings: RuntimeSettings) -> FulfillmentWorkerResult:
    return process_one_runtime_fulfillment(settings=settings)


def run_once(
    *,
    settings: RuntimeSettings,
    processor: RuntimeProcessor = process_runtime_settings,
) -> FulfillmentWorkerResult:
    runtime_role = _runtime_role(settings)
    if runtime_role == "api":
        raise RuntimeConfigError("JEDI_RUNTIME_ROLE=api cannot run the runtime worker")
    return processor(settings)


def run_loop(
    *,
    settings: RuntimeSettings,
    processor: RuntimeProcessor = process_runtime_settings,
    max_iterations: int | None = None,
    idle_sleep_seconds: float = 5.0,
    sleep: Sleeper = sleep_seconds,
    stop_on_failure: bool = True,
    pruner: Pruner | None = None,
    prune_interval_seconds: float = DEFAULT_PRUNE_INTERVAL_SECONDS,
    stale_job_recoverer: StaleJobRecoverer | None = None,
    stale_job_recovery_interval_seconds: float = DEFAULT_STALE_JOB_REQUEUE_INTERVAL_SECONDS,
    stale_job_requeue_alert_emitter: StaleJobRequeueAlertEmitter | None = None,
    alert_emitter: AlertEmitter | None = None,
    clock: Clock = monotonic_seconds,
) -> RuntimeWorkerLoopSummary:
    _validate_run_loop_controls(
        settings=settings,
        max_iterations=max_iterations,
        idle_sleep_seconds=idle_sleep_seconds,
        stop_on_failure=stop_on_failure,
        prune_interval_seconds=prune_interval_seconds,
        stale_job_recovery_interval_seconds=stale_job_recovery_interval_seconds,
    )
    iterations = 0
    completed = 0
    idle = 0
    failed = 0
    alerts_emitted = 0
    alert_failures = 0
    prune_failures = 0
    stale_job_recovery_failures = 0
    stopped_reason = "max_iterations"
    last_prune_at: float | None = None
    last_stale_job_recovery_at: float | None = None

    while max_iterations is None or iterations < max_iterations:
        elapsed: float | None = None
        if pruner is not None or stale_job_recoverer is not None:
            elapsed = clock()
        if (
            pruner is not None
            and elapsed is not None
            and (last_prune_at is None or elapsed - last_prune_at >= prune_interval_seconds)
        ):
            try:
                pruner()
            except Exception as exc:
                prune_failures += 1
                _log_pruner_failure(error=exc)
            last_prune_at = elapsed
        if (
            stale_job_recoverer is not None
            and elapsed is not None
            and (
                last_stale_job_recovery_at is None
                or elapsed - last_stale_job_recovery_at >= stale_job_recovery_interval_seconds
            )
        ):
            try:
                stale_job_requeue_report = stale_job_recoverer()
            except Exception as exc:
                stale_job_recovery_failures += 1
                _log_stale_job_recovery_failure(error=exc)
                stale_job_requeue_report = None
            if (
                stale_job_requeue_alert_emitter is not None
                and isinstance(stale_job_requeue_report, StaleJobRequeueReport)
                and stale_job_requeue_report.requeued_count > 0
            ):
                try:
                    stale_job_requeue_alert_emitter(stale_job_requeue_report)
                    alerts_emitted += 1
                except Exception as exc:
                    alert_failures += 1
                    _log_stale_requeue_alert_failure(
                        report=stale_job_requeue_report,
                        error=exc,
                    )
            last_stale_job_recovery_at = elapsed
        result = run_once(settings=settings, processor=processor)
        iterations += 1
        if result.status == "completed":
            completed += 1
            continue
        if result.status == "idle":
            idle += 1
            sleep(idle_sleep_seconds)
            continue
        if result.status == "failed":
            failed += 1
            if alert_emitter is not None:
                try:
                    alert_emitter(result)
                    alerts_emitted += 1
                except Exception as exc:
                    alert_failures += 1
                    _log_worker_alert_failure(result=result, error=exc)
            if stop_on_failure:
                stopped_reason = "failed_job"
                break
            continue

    return RuntimeWorkerLoopSummary(
        iterations=iterations,
        completed=completed,
        idle=idle,
        failed=failed,
        alerts_emitted=alerts_emitted,
        alert_failures=alert_failures,
        prune_failures=prune_failures,
        stale_job_recovery_failures=stale_job_recovery_failures,
        stopped_reason=stopped_reason,
    )


def _validate_run_loop_controls(
    *,
    settings: RuntimeSettings,
    max_iterations: int | None,
    idle_sleep_seconds: float,
    stop_on_failure: bool,
    prune_interval_seconds: float,
    stale_job_recovery_interval_seconds: float,
) -> None:
    if max_iterations is not None:
        if (
            isinstance(max_iterations, bool)
            or not isinstance(max_iterations, int)
            or max_iterations <= 0
        ):
            raise ValueError("JEDI_WORKER_MAX_ITERATIONS must be greater than 0 when configured")
        if max_iterations > MAX_WORKER_MAX_ITERATIONS:
            raise ValueError(
                "JEDI_WORKER_MAX_ITERATIONS must be at most "
                f"{MAX_WORKER_MAX_ITERATIONS} when configured"
            )
    _validate_run_loop_seconds(
        value=idle_sleep_seconds,
        setting_name="JEDI_WORKER_IDLE_SLEEP_SECONDS",
        maximum=MAX_WORKER_IDLE_SLEEP_SECONDS,
        allow_zero=True,
    )
    if max_iterations is None and idle_sleep_seconds <= 0:
        raise ValueError(
            "JEDI_WORKER_IDLE_SLEEP_SECONDS must be greater than 0 for unbounded worker loops"
        )
    _validate_run_loop_seconds(
        value=prune_interval_seconds,
        setting_name="JEDI_RETENTION_PRUNE_INTERVAL_SECONDS",
        maximum=MAX_MAINTENANCE_INTERVAL_SECONDS,
        allow_zero=False,
    )
    _validate_run_loop_seconds(
        value=stale_job_recovery_interval_seconds,
        setting_name="JEDI_STALE_JOB_REQUEUE_INTERVAL_SECONDS",
        maximum=MAX_MAINTENANCE_INTERVAL_SECONDS,
        allow_zero=False,
    )
    runtime_environment = _runtime_environment(settings)
    if runtime_environment == "production" and stop_on_failure:
        raise ValueError("JEDI_WORKER_STOP_ON_FAILURE must be false in production")


def _validate_run_loop_seconds(
    *,
    value: object,
    setting_name: str,
    maximum: float,
    allow_zero: bool,
) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, int | float)
        or not math.isfinite(float(value))
        or value < 0
        or (not allow_zero and value == 0)
    ):
        comparator = "greater than or equal to 0" if allow_zero else "greater than 0"
        raise ValueError(f"{setting_name} must be {comparator}")
    if value > maximum:
        raise ValueError(f"{setting_name} must be at most {maximum:g}")


def main(
    *,
    env_path: Path | None = DEFAULT_ENV_PATH,
    processor: RuntimeProcessor = process_runtime_settings,
    sleep: Sleeper = sleep_seconds,
    prune_store_factory: PruneStoreFactory = DEFAULT_PRUNE_STORE_FACTORY,
    stale_job_recovery_store_factory: StaleJobRecoveryStoreFactory = (
        DEFAULT_STALE_JOB_RECOVERY_STORE_FACTORY
    ),
    alert_transport: HttpTransport | None = None,
) -> int:
    settings = load_worker_settings(env_path)
    pruner: Pruner | None = None
    if settings.retention.enabled:
        pruner = partial(
            prune_operational_store,
            settings=settings.runtime,
            policy=settings.retention,
            store_factory=prune_store_factory,
        )
    stale_job_recoverer: StaleJobRecoverer | None = None
    if settings.stale_job_requeue_enabled:
        stale_job_recoverer = partial(
            requeue_stale_running_jobs,
            settings=settings.runtime,
            stale_after_seconds=settings.runtime.running_job_stale_after_seconds,
            batch_size=settings.stale_job_requeue_batch_size,
            store_factory=stale_job_recovery_store_factory,
        )
    alert_emitter: AlertEmitter | None = None
    stale_job_requeue_alert_emitter: StaleJobRequeueAlertEmitter | None = None
    if settings.runtime.alert_webhook_enabled and settings.runtime.alert_webhook_url:
        transport = alert_transport or UrllibTransport(
            timeout_seconds=settings.runtime.alert_webhook_timeout_seconds
        )
        alert_emitter = partial(
            _emit_worker_failure_alert,
            settings=settings.runtime,
            transport=transport,
        )
        stale_job_requeue_alert_emitter = partial(
            _emit_stale_requeue_alert,
            settings=settings.runtime,
            transport=transport,
        )
    summary = run_loop(
        settings=settings.runtime,
        processor=processor,
        max_iterations=settings.max_iterations,
        idle_sleep_seconds=settings.idle_sleep_seconds,
        sleep=sleep,
        stop_on_failure=settings.stop_on_failure,
        pruner=pruner,
        prune_interval_seconds=settings.prune_interval_seconds,
        stale_job_recoverer=stale_job_recoverer,
        stale_job_recovery_interval_seconds=settings.stale_job_requeue_interval_seconds,
        stale_job_requeue_alert_emitter=stale_job_requeue_alert_emitter,
        alert_emitter=alert_emitter,
    )
    print(_runtime_report_json(summary))
    return 1 if summary.failed and settings.stop_on_failure else 0


def _runtime_report_json(report: BaseModel) -> str:
    try:
        _ensure_runtime_report_json_safe(report.model_dump(mode="python", warnings=False))
        payload = report.model_dump(mode="json", warnings=False)
        json.dumps(
            payload,
            sort_keys=True,
            allow_nan=False,
        )
    except PydanticSerializationError:
        raise ValueError(RUNTIME_WORKER_REPORT_NON_JSON_DIAGNOSTIC) from None
    except ValueError:
        raise ValueError(RUNTIME_WORKER_REPORT_NON_FINITE_DIAGNOSTIC) from None
    except TypeError:
        raise ValueError(RUNTIME_WORKER_REPORT_NON_JSON_DIAGNOSTIC) from None
    return json.dumps(payload, separators=(",", ":"))


def _ensure_runtime_report_json_safe(value: Any) -> None:
    if (
        value is None
        or type(value) is str
        or type(value) is bool
        or type(value) is int
        or type(value) is datetime
        or isinstance(value, Enum)
    ):
        return
    if type(value) is float:
        if math.isfinite(value):
            return
        raise ValueError("non-finite runtime report value")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise TypeError("non-JSON runtime report key")
            _ensure_runtime_report_json_safe(item)
        return
    if type(value) is list:
        for item in value:
            _ensure_runtime_report_json_safe(item)
        return
    if type(value) is tuple:
        for item in value:
            _ensure_runtime_report_json_safe(item)
        return
    raise TypeError("non-JSON runtime report value")


def _optional_int(value: str | None, *, name: str) -> int | None:
    return parse_optional_base10_int(value, name=name)


def _optional_float(value: str | None, *, name: str, default: float) -> float:
    if value is None or value == "":
        return default
    try:
        parsed = parse_optional_ascii_decimal_float(value, name=name)
    except ValueError as exc:
        raise ValueError(
            exception_diagnostic_message(exc, fallback_subject="runtime worker")
        ) from None
    if parsed is None:
        return default
    return parsed


def _bool_value(value: str | None, *, name: str, default: bool = False) -> bool:
    raw = str(value or "")
    if raw == "":
        return default
    if raw != raw.strip() or has_whitespace_or_control_character(raw):
        raise ValueError(f"{name} must be a boolean value without padding or control characters")
    text = raw.lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean value: true/false, 1/0, yes/no, or on/off")


def _log_worker_alert_failure(
    *,
    result: FulfillmentWorkerResult,
    error: Exception,
) -> None:
    LOGGER.warning(
        "worker alert delivery failed for job %s: %s",
        result.job_id or "unknown",
        _redact_runtime_worker_exception(error),
    )


def _log_pruner_failure(*, error: Exception) -> None:
    LOGGER.warning(
        "worker retention prune failed: %s",
        _redact_runtime_worker_exception(error),
    )


def _log_stale_job_recovery_failure(*, error: Exception) -> None:
    LOGGER.warning(
        "worker stale job recovery failed: %s",
        _redact_runtime_worker_exception(error),
    )


def _log_stale_requeue_alert_failure(
    *,
    report: StaleJobRequeueReport,
    error: Exception,
) -> None:
    LOGGER.warning(
        "stale requeue alert delivery failed for jobs %s: %s",
        ", ".join(report.job_ids) if report.job_ids else "none",
        _redact_runtime_worker_exception(error),
    )


def _redact_runtime_worker_exception(error: Exception) -> str:
    return (
        _redact_diagnostic_text(
            exception_diagnostic_message(error, fallback_subject="runtime worker")
        )
        or ""
    )


def _emit_worker_failure_alert(
    result: FulfillmentWorkerResult,
    *,
    settings: RuntimeSettings,
    transport: HttpTransport,
) -> None:
    alert_webhook_url, alert_webhook_max_body_bytes = _alert_delivery_settings(settings)
    if alert_webhook_url is None:
        return
    emit_alert_webhook(
        alert=worker_failure_alert(result, created_at=datetime.now(UTC)),
        webhook_url=alert_webhook_url,
        transport=transport,
        max_body_bytes=alert_webhook_max_body_bytes,
    )


def _emit_stale_requeue_alert(
    report: StaleJobRequeueReport,
    *,
    settings: RuntimeSettings,
    transport: HttpTransport,
) -> None:
    alert_webhook_url, alert_webhook_max_body_bytes = _alert_delivery_settings(settings)
    if alert_webhook_url is None:
        return
    emit_alert_webhook(
        alert=stale_requeue_alert(
            requeued_at=report.requeued_at,
            stale_after_seconds=report.stale_after_seconds,
            requeued_count=report.requeued_count,
            job_ids=report.job_ids,
        ),
        webhook_url=alert_webhook_url,
        transport=transport,
        max_body_bytes=alert_webhook_max_body_bytes,
    )


def _alert_delivery_settings(settings: RuntimeSettings) -> tuple[str | None, int]:
    alert_webhook_url = _direct_optional_runtime_setting_text(
        settings.alert_webhook_url,
        name="JEDI_ALERT_WEBHOOK_URL",
    )
    alert_webhook_max_body_bytes = _runtime_setting_int(
        settings.alert_webhook_max_body_bytes,
        name="JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES",
    )
    if alert_webhook_max_body_bytes <= 0:
        raise RuntimeConfigError("JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES must be greater than 0")
    if alert_webhook_max_body_bytes > MAX_PRODUCTION_ALERT_WEBHOOK_BODY_BYTES:
        raise RuntimeConfigError(
            "JEDI_ALERT_WEBHOOK_MAX_BODY_BYTES must be at most "
            f"{MAX_PRODUCTION_ALERT_WEBHOOK_BODY_BYTES}"
        )
    if alert_webhook_url is not None:
        url_errors = validate_alert_webhook_url(
            alert_webhook_url,
            subject="JEDI_ALERT_WEBHOOK_URL",
        )
        if url_errors:
            raise RuntimeConfigError("; ".join(url_errors))
    return alert_webhook_url, alert_webhook_max_body_bytes


if __name__ == "__main__":
    raise SystemExit(main())
