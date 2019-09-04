"""Submodule for parsed field behaviors."""

from .base import BusAccessNoOpMethod, BusAccessBehavior, BusBehavior, Behavior
from .primitive import PrimitiveBehavior
from .interrupt import InterruptBehavior
from .axi import AxiBehavior
from .custom import CustomBehavior
