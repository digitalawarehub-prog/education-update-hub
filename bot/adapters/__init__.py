"""
Education Update Hub - Production Adapter Registry

The scraper calls get_adapter(source) for every configured source.
The explicit adapter field in config.py prevents a source from silently
falling back to the generic scraper.
"""

from .generic import GenericAdapter
from .ibps import IBPSAdapter
from .psc import PSCAdapter
from .railway import RailwayAdapter
from .ssc import SSCAdapter
from .uk import UKAdapter
from .upsc import UPSCAdapter


ADAPTERS = {
    "generic": GenericAdapter,
    "ibps": IBPSAdapter,
    "psc": PSCAdapter,
    "railway": RailwayAdapter,
    "ssc": SSCAdapter,
    "uk": UKAdapter,
    "upsc": UPSCAdapter,
}


def get_adapter(source):
    """Return the adapter explicitly assigned to a source."""
    source = source or {}

    adapter_name = str(source.get("adapter", "generic")).strip().lower()
    adapter_class = ADAPTERS.get(adapter_name)

    if adapter_class is None:
        raise ValueError(
            f"Unknown adapter '{adapter_name}' for source '{source.get('name', 'Unknown')}'. "
            f"Available adapters: {', '.join(sorted(ADAPTERS))}"
        )

    return adapter_class()


__all__ = ["get_adapter", "ADAPTERS"]
