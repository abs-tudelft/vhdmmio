"""Submodule defining field behavior configuration structures."""

from .registry import behaviors

from .primitive import Primitive
from .constant import Constant, Config
from .status import Status, InternalStatus, Latching
from .control import Control, InternalControl
from .flag import Flag, VolatileFlag, InternalFlag, VolatileInternalFlag
from .request import Strobe, Request, MultiRequest
from .counter import Counter, VolatileCounter, InternalCounter, VolatileInternalCounter
from .stream import StreamToMMIO, MMIOToStream
from .axi import Axi
from .memory import Memory
from .interrupt import (
    Interrupt, InterruptFlag, VolatileInterruptFlag, InterruptPend,
    InterruptEnable, InterruptUnmask, InterruptStatus, InterruptRaw)
from .custom import Custom, CustomInterfaceConfig
