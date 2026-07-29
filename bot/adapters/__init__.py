"""
=========================================================
Education Update Hub
Adapter Registry
=========================================================
"""

from .uk import UKAdapter
from .ssc import SSCAdapter
from .railway import RailwayAdapter
from .ibps import IBPSAdapter
from .upsc import UPSCAdapter
from .psc import PSCAdapter
from .generic import GenericAdapter


ADAPTERS = {

    "uk": UKAdapter,

    "ssc": SSCAdapter,

    "railway": RailwayAdapter,

    "ibps": IBPSAdapter,

    "upsc": UPSCAdapter,

    "psc": PSCAdapter,

    "generic": GenericAdapter

}


def get_adapter(source):

    adapter_name = str(

        source.get(
            "adapter",
            "generic"
        )

    ).lower()

    adapter = ADAPTERS.get(adapter_name)

    if adapter is None:

        adapter = GenericAdapter

    return adapter()
