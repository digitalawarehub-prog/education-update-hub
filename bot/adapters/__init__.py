"""Explicit production adapter registry."""
from .generic import GenericAdapter
from .ibps import IBPSAdapter
from .psc import PSCAdapter
from .railway import RailwayAdapter
from .ssc import SSCAdapter
from .uk import UKAdapter
from .upsc import UPSCAdapter
from .sbi import SBIAdapter

ADAPTERS = {
    "generic": GenericAdapter,
    "ibps": IBPSAdapter,
    "psc": PSCAdapter,
    "railway": RailwayAdapter,
    "ssc": SSCAdapter,
    "uk": UKAdapter,
    "upsc": UPSCAdapter,
    "sbi": SBIAdapter,
}


def get_adapter(source):
    name = str((source or {}).get("adapter", "generic")).strip().lower()
    if name not in ADAPTERS:
        raise ValueError(f"Unknown adapter '{name}'")
    return ADAPTERS[name]()

__all__ = ["get_adapter", "ADAPTERS"]
