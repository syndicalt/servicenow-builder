"""Facade for ServiceNow instance discovery.

Implementation lives in :mod:`jedi_devproject.discovery`; this module
re-exports the public API so existing imports keep working unchanged.
"""

from __future__ import annotations

from jedi_devproject.discovery.bundle import discover_servicenow_surface_context
from jedi_devproject.discovery.models import (
    EMPTY_REQUIRED_SURFACE_IS_SUFFICIENT,
    DiscoveredField,
    DiscoveredFormElement,
    DiscoveredFormSection,
    InstanceDiscoveryClient,
    InstanceDiscoveryContext,
    ServiceNowSurfaceContext,
    ServiceNowSurfaceContextBundle,
    ServiceNowSurfaceRecord,
    SurfaceName,
)
from jedi_devproject.discovery.schema_form import discover_dictionary_form_context

__all__ = [
    "EMPTY_REQUIRED_SURFACE_IS_SUFFICIENT",
    "DiscoveredField",
    "DiscoveredFormElement",
    "DiscoveredFormSection",
    "InstanceDiscoveryClient",
    "InstanceDiscoveryContext",
    "ServiceNowSurfaceContext",
    "ServiceNowSurfaceContextBundle",
    "ServiceNowSurfaceRecord",
    "SurfaceName",
    "discover_dictionary_form_context",
    "discover_servicenow_surface_context",
]
