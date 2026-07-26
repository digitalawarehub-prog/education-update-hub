from .generic import GenericAdapter
from .upsc import UPSCAdapter
from .ssc import SSCAdapter
from .ibps import IBPSAdapter
from .railway import RailwayAdapter
from .psc import PSCAdapter
from .uk import UKAdapter


ADAPTERS = {

    "generic": GenericAdapter(),

    "upsc": UPSCAdapter(),

    "ssc": SSCAdapter(),

    "ibps": IBPSAdapter(),

    "railway": RailwayAdapter(),

    "psc": PSCAdapter(),

    "uk": UKAdapter()

}
