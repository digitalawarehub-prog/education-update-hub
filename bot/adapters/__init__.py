"""
Education Update Hub
Adapters Package
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


__all__ = [
    "GenericAdapter",
    "IBPSAdapter",
    "PSCAdapter",
    "RailwayAdapter",
    "SSCAdapter",
    "UKAdapter",
    "UPSCAdapter",
    "ADAPTERS",
]
