"""Runtime facade.

Thin re-export layer preserving the public API of the former monolithic
``jedi_devproject.runtime`` module. Implementation now lives in:

- :mod:`jedi_devproject.runtime_config` -- settings model, env parsing, validation
- :mod:`jedi_devproject.runtime_store` -- operational store contract
- :mod:`jedi_devproject.runtime_auth` -- admin auth and rate-limit guards
- :mod:`jedi_devproject.runtime_redaction` -- secret redaction helpers
- :mod:`jedi_devproject.runtime_servicenow` -- ServiceNow client wiring and notifiers
- :mod:`jedi_devproject.admin_routes` -- FastAPI app factory and admin routes
- :mod:`jedi_devproject.runtime_fulfillment` -- worker-side fulfillment wiring
"""

from __future__ import annotations

from jedi_devproject.admin_routes import create_runtime_api
from jedi_devproject.runtime_config import (
    RuntimeConfigError,
    RuntimeSettings,
    load_runtime_settings,
    validate_runtime_settings,
)
from jedi_devproject.runtime_fulfillment import process_one_runtime_fulfillment
from jedi_devproject.runtime_servicenow import SplitServiceNowClient
from jedi_devproject.runtime_store import DEFAULT_STORE_FACTORY, RuntimeStore, StoreFactory

__all__ = [
    "DEFAULT_STORE_FACTORY",
    "RuntimeConfigError",
    "RuntimeSettings",
    "RuntimeStore",
    "SplitServiceNowClient",
    "StoreFactory",
    "create_runtime_api",
    "load_runtime_settings",
    "process_one_runtime_fulfillment",
    "validate_runtime_settings",
]
